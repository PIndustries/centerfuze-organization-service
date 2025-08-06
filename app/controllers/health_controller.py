"""
Health check controller
"""

import json
import logging
from typing import List
from nats.aio.msg import Msg
from nats.aio.client import Client as NATS

from ..config.database import DatabaseManager
from ..utils.response import ResponseBuilder

logger = logging.getLogger(__name__)


class HealthController:
    """Handles health check requests"""
    
    def __init__(self, db_manager: DatabaseManager, nats_client: NATS):
        self.db_manager = db_manager
        self.nats_client = nats_client
        
    async def register_handlers(self, nc: NATS) -> List:
        """Register NATS handlers"""
        return [
            await nc.subscribe("organization.health", cb=self.handle_health)
        ]
        
    async def handle_health(self, msg: Msg):
        """Handle health check request"""
        try:
            # Check database connection
            db_healthy = self.db_manager.health_check()
            
            # Check NATS connection
            nats_healthy = not self.nats_client.is_closed
            
            # Overall health status
            healthy = db_healthy and nats_healthy
            
            response_data = {
                "service": "centerfuze-organization-service",
                "status": "healthy" if healthy else "unhealthy",
                "components": {
                    "database": "healthy" if db_healthy else "unhealthy",
                    "nats": "healthy" if nats_healthy else "unhealthy"
                }
            }
            
            if healthy:
                response = ResponseBuilder.success(response_data, "Service is healthy")
            else:
                response = ResponseBuilder.error(
                    "Service is unhealthy",
                    "HEALTH_CHECK_FAILED",
                    response_data
                )
                
            await msg.respond(response)
            
        except Exception as e:
            logger.error(f"Error in health check: {e}", exc_info=True)
            response = ResponseBuilder.error(
                f"Health check failed: {str(e)}",
                "HEALTH_CHECK_ERROR"
            )
            await msg.respond(response)