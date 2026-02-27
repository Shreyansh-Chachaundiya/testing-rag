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

    recovery_id = f"recovery_{uuid4().hex[:8]}"

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
            log_error(
                error_message=f"Retry failed for {txn_id}: {str(e)}",
                error_type="RetryFailure",
                transaction_id=txn_id,
                extra={"attempt": txn.get("attempt", 1)},
                exc_info=True,              )

    log_info(
        message=(
            f"Batch retry complete: {results['retried']} ok, "
            f"{results['failed']} failed"
        ),
        transaction_id="batch_retry",
    )
    return results
