"""
Response utilities for NATS message handling
"""

import json
import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class ResponseBuilder:
    """Helper for building consistent NATS responses"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success") -> bytes:
        """Build success response"""
        response = {
            "status": "success",
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        return ResponseBuilder._serialize(response)
    
    @staticmethod
    def error(message: str, error_code: str = "UNKNOWN_ERROR", details: Optional[Dict] = None) -> bytes:
        """Build error response"""
        response = {
            "status": "error",
            "message": message,
            "error_code": error_code,
            "timestamp": datetime.utcnow().isoformat()
        }
        if details:
            response["details"] = details
        return ResponseBuilder._serialize(response)
    
    @staticmethod
    def validation_error(errors: Dict[str, Any]) -> bytes:
        """Build validation error response"""
        return ResponseBuilder.error(
            message="Validation failed",
            error_code="VALIDATION_ERROR",
            details={"validation_errors": errors}
        )
    
    @staticmethod
    def not_found(resource_type: str, resource_id: str = None) -> bytes:
        """Build not found response"""
        message = f"{resource_type} not found"
        if resource_id:
            message += f" with ID: {resource_id}"
        return ResponseBuilder.error(
            message=message,
            error_code="NOT_FOUND"
        )
    
    @staticmethod
    def already_exists(resource_type: str, field: str = None, value: str = None) -> bytes:
        """Build already exists response"""
        message = f"{resource_type} already exists"
        if field and value:
            message += f" with {field}: {value}"
        return ResponseBuilder.error(
            message=message,
            error_code="ALREADY_EXISTS"
        )
    
    @staticmethod
    def _serialize(data: Dict[str, Any]) -> bytes:
        """Serialize response to JSON bytes"""
        try:
            return json.dumps(data, default=str).encode('utf-8')
        except Exception as e:
            logger.error(f"Failed to serialize response: {e}")
            # Fallback response
            fallback = {
                "status": "error",
                "message": "Internal server error - failed to serialize response",
                "error_code": "SERIALIZATION_ERROR",
                "timestamp": datetime.utcnow().isoformat()
            }
            return json.dumps(fallback).encode('utf-8')