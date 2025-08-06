"""
Event publishing service for NATS
"""

import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime
from nats.aio.client import Client as NATS

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publishes events to NATS"""
    
    def __init__(self, nc: NATS, service_name: str):
        self.nc = nc
        self.service_name = service_name
        
    async def publish(self, event_type: str, data: Dict[str, Any], metadata: Optional[Dict] = None):
        """Publish an event to NATS"""
        try:
            # Build event payload
            event = {
                "event_type": event_type,
                "service": self.service_name,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            if metadata:
                event["metadata"] = metadata
                
            # Serialize to JSON
            payload = json.dumps(event).encode()
            
            # Publish to NATS
            await self.nc.publish(f"centerfuze.{event_type}", payload)
            
            logger.debug(f"Published event: {event_type}")
            
        except Exception as e:
            logger.error(f"Error publishing event {event_type}: {e}", exc_info=True)
            # Don't raise - event publishing should not break the main flow