"""
Profile service — persistence layer for user profile operations.

Handles writing profile changes (address, phone, deactivation)
back to the data store. Called by the Profile API layer.
"""

from typing import Dict, Any, Optional
from utils.database import get_user_by_id
from utils.logger import log_info, log_error


class ProfileServiceError(Exception):
    pass


class ProfileService:
    """Handles persistence for user profile changes."""

    async def persist_address(
        self,
        user_id: str,
        address: Dict[str, str],
    ) -> bool:
        """Write the updated address to the database."""
        if not user_id:
            raise ProfileServiceError("user_id is required for address update")

        if not isinstance(address, dict):
            raise ProfileServiceError("address must be a dict")

        # In production: await db.users.update_one(
        #     {"id": user_id}, {"$set": {"address": address}}
        # )
        log_info(
            message=f"Address persisted for user {user_id}",
            transaction_id=f"persist-addr-{user_id[:8]}",
        )
        return True

    async def persist_phone(
        self,
        user_id: str,
        phone: str,
    ) -> bool:
        """Write the updated phone number to the database."""
        if not user_id:
            raise ProfileServiceError("user_id is required for phone update")

        if not phone or not isinstance(phone, str):
            raise ProfileServiceError("phone must be a non-empty string")

        # In production: await db.users.update_one(
        #     {"id": user_id}, {"$set": {"phone": phone}}
        # )
        log_info(
            message=f"Phone persisted for user {user_id}",
            transaction_id=f"persist-phone-{user_id[:8]}",
        )
        return True

    async def persist_deactivation(self, user_id: str) -> bool:
        """Mark the user account as inactive in the database."""
        if not user_id:
            raise ProfileServiceError("user_id is required for deactivation")

        # In production: await db.users.update_one(
        #     {"id": user_id}, {"$set": {"is_active": False}}
        # )
        log_info(
            message=f"Account deactivation persisted for user {user_id}",
            transaction_id=f"persist-deact-{user_id[:8]}",
        )
        return True

    async def get_profile_summary(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Return a lightweight profile summary for display purposes."""
        user_data = await get_user_by_id(user_id)
        if not user_data:
            return None

        return {
            "user_id": user_id,
            "name": user_data.get("name"),
            "email": user_data.get("email"),
            "has_address": bool(user_data.get("address")),
            "has_phone": bool(user_data.get("phone")),
            "is_active": user_data.get("is_active", True),
        }
