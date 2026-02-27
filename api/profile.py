"""
Profile API — manages user account and shipping address.

Handles profile retrieval and address updates for authenticated users.
Address changes are written back to the data store via ProfileService.
"""

from datetime import datetime
from typing import Dict, Any
from uuid import uuid4

from services.profile_service import ProfileService, ProfileServiceError
from models.user import User, UserRole
from utils.database import get_user_by_id
from utils.logger import log_info, log_error


class ProfileUpdateError(Exception):
    pass


async def get_profile(user_id: str) -> Dict[str, Any]:
    """Return the current profile data for a user."""
    txn_id = f"PROF-GET-{uuid4().hex[:8]}"

    user_data = await get_user_by_id(user_id)
    if not user_data:
        raise ProfileUpdateError(f"User not found: {user_id}")

    log_info(
        message=f"Profile fetched for user {user_id}",
        transaction_id=txn_id,
    )

    return {
        "user_id": user_id,
        "name": user_data.get("name"),
        "email": user_data.get("email"),
        "role": user_data.get("role"),
        "phone": user_data.get("phone"),
        "address": user_data.get("address"),
    }


async def update_shipping_address(
    user_id: str,
    address_data: Dict[str, str],
) -> Dict[str, Any]:
    """
    Update the saved shipping address for a user account.

    Reconstructs the User domain object from persisted data,
    applies the new address, then delegates persistence to ProfileService.
    """
    txn_id = f"PROF-ADDR-{uuid4().hex[:8]}"

    try:
        user_data = await get_user_by_id(user_id)
        if not user_data:
            raise ProfileUpdateError(f"User not found: {user_id}")

        user = User(
            name=user_data["name"],
            email=user_data["email"],
            age=user_data["age"],
            role=UserRole(user_data.get("role", "customer")),
            id=user_data.get("id"),
        )

        user.update_address(address_data)

        service = ProfileService()
        await service.persist_address(user_id, user.address)

        log_info(
            message=f"Shipping address updated for user {user_id}",
            transaction_id=txn_id,
            extra={"user_id": user_id},
        )

        return {
            "status": "updated",
            "user_id": user_id,
            "address": user.address,
            "updated_at": datetime.utcnow().isoformat(),
        }

    except (ValueError, ProfileServiceError) as e:
        log_error(
            error_message=f"Address update failed for {user_id}: {str(e)}",
            error_type=type(e).__name__,
            transaction_id=txn_id,
        )
        raise ProfileUpdateError(str(e))


async def update_phone_number(
    user_id: str,
    phone: str,
) -> Dict[str, Any]:
    """Update the contact phone number for a user account."""
    txn_id = f"PROF-PHONE-{uuid4().hex[:8]}"

    user_data = await get_user_by_id(user_id)
    if not user_data:
        raise ProfileUpdateError(f"User not found: {user_id}")

    service = ProfileService()
    await service.persist_phone(user_id, phone)

    log_info(
        message=f"Phone updated for user {user_id}",
        transaction_id=txn_id,
    )

    return {
        "status": "updated",
        "user_id": user_id,
        "phone": phone,
        "updated_at": datetime.utcnow().isoformat(),
    }


async def deactivate_account(
    user_id: str,
    requesting_admin_id: str,
) -> Dict[str, Any]:
    """Deactivate a user account. Admin-only operation."""
    txn_id = f"PROF-DEACT-{uuid4().hex[:8]}"

    user_data = await get_user_by_id(user_id)
    if not user_data:
        raise ProfileUpdateError(f"User not found: {user_id}")

    admin_data = await get_user_by_id(requesting_admin_id)
    if not admin_data or admin_data.get("role") != "admin":
        raise ProfileUpdateError("Only admins can deactivate accounts")

    user = User(
        name=user_data["name"],
        email=user_data["email"],
        age=user_data["age"],
        role=UserRole(user_data.get("role", "customer")),
        id=user_data.get("id"),
    )

    user.deactivate()

    service = ProfileService()
    await service.persist_deactivation(user_id)

    log_info(
        message=f"Account deactivated: {user_id} by admin {requesting_admin_id}",
        transaction_id=txn_id,
        extra={"admin_id": requesting_admin_id},
    )

    return {
        "status": "deactivated",
        "user_id": user_id,
        "deactivated_at": datetime.utcnow().isoformat(),
    }
