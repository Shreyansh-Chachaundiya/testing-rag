"""
Helper module for processing failed transactions.

This file uses utils/logger.py from the main branch.
It demonstrates both CORRECT and INCORRECT usage of log_error():

- log_error() accepts exactly 4 params:
    error_message, error_type, transaction_id, extra

- One call below incorrectly passes exc_info=True, which is
  NOT a valid parameter for log_error(). The new pipeline should
  detect this as a TypeError by fetching the logger definition.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

from utils.logger import log_error, log_info, log_warning
from utils.database import get_user_by_id


class TransactionRecoveryError(Exception):
    pass


async def process_failed_transaction(
    transaction_id: str,
    failure_reason: str,
    user_id: str,
) -> Dict[str, Any]:
    """
    Handle a failed transaction by logging it and notifying the user.

    Contains both correct and incorrect calls to log_error.
    """
    recovery_id = f"recovery_{uuid4().hex[:8]}"

    # ── CORRECT USAGE: exactly 4 params ──
    log_error(
        error_message=f"Transaction {transaction_id} failed: {failure_reason}",
        error_type="TransactionFailure",
        transaction_id=transaction_id,
        extra={"user_id": user_id, "recovery_id": recovery_id},
    )

    user = await get_user_by_id(user_id)
    if not user:
        log_warning(
            message=f"User {user_id} not found during recovery",
            transaction_id=transaction_id,
        )

    log_info(
        message=f"Recovery initiated: {recovery_id}",
        transaction_id=transaction_id,
        extra={"original_failure": failure_reason},
    )

    return {
        "recovery_id": recovery_id,
        "transaction_id": transaction_id,
        "status": "recovery_initiated",
        "timestamp": datetime.utcnow().isoformat(),
    }


async def retry_failed_transactions(
    failed_transactions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Retry a batch of failed transactions.

    Contains an INCORRECT call to log_error with exc_info parameter
    that does not exist in the function signature.
    """
    results = {"retried": 0, "failed": 0, "errors": []}

    for txn in failed_transactions:
        txn_id = txn.get("transaction_id", "unknown")

        try:
            # Simulate retry logic
            await asyncio.sleep(0.05)

            if txn.get("retryable", True):
                results["retried"] += 1
                log_info(
                    message=f"Transaction {txn_id} retried successfully",
                    transaction_id=txn_id,
                )
            else:
                raise TransactionRecoveryError(
                    f"Transaction {txn_id} is not retryable"
                )

        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"transaction_id": txn_id, "error": str(e)})

            # ── INCORRECT USAGE: exc_info is NOT a valid parameter ──
            # log_error() signature: (error_message, error_type, transaction_id, extra)
            # Passing exc_info=True will cause a TypeError at runtime.
            log_error(
                error_message=f"Retry failed for {txn_id}: {str(e)}",
                error_type="RetryFailure",
                transaction_id=txn_id,
                extra={"attempt": txn.get("attempt", 1)},
                exc_info=True,  # BUG: This parameter does not exist
            )

    log_info(
        message=(
            f"Batch retry complete: {results['retried']} ok, "
            f"{results['failed']} failed"
        ),
        transaction_id="batch_retry",
    )
    return results
