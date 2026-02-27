

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4

from utils.database import get_user_by_id
from utils.logger import log_info, log_error

from services.export_service import (
    ExportServiceX,
    ExportFormat,
    export_to_csv,
    export_to_json,
)


class OrderExportError(Exception):
    pass


async def export_user_orders(
    user_id: str,
    format: str = "csv",
    date_range: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Export a user's order history via the external ExportServiceX.

    Args:
        user_id: User whose orders to export
        format: Export format (csv, json)
        date_range: Optional date filter

    Returns:
        Dict with export_id, file_url, record_count
    """
    transaction_id = f"export_{uuid4().hex[:8]}"

    try:
        log_info(
            message=f"Starting order export for user {user_id}",
            transaction_id=transaction_id,
        )

        user = await get_user_by_id(user_id)
        if not user:
            raise OrderExportError(f"User not found: {user_id}")

        exporter = ExportServiceX(
            api_key="export-key-123",
            region="us-east-1",
        )

        if format == "csv":
            result = await export_to_csv(
                exporter=exporter,
                user_id=user_id,
                date_range=date_range,
            )
        elif format == "json":
            result = await export_to_json(
                exporter=exporter,
                user_id=user_id,
                date_range=date_range,
            )
        else:
            raise OrderExportError(f"Unsupported export format: {format}")

        log_info(
            message=f"Export completed: {result.get('record_count', 0)} records",
            transaction_id=transaction_id,
            extra={"format": format, "user_id": user_id},
        )

        return {
            "export_id": transaction_id,
            "file_url": result.get("file_url"),
            "record_count": result.get("record_count", 0),
            "format": format,
            "created_at": datetime.utcnow().isoformat(),
        }

    except OrderExportError:
        raise
    except Exception as e:
        log_error(
            error_message=f"Export failed: {str(e)}",
            error_type="OrderExportError",
            transaction_id=transaction_id,
        )
        raise OrderExportError(f"Export failed: {str(e)}")
