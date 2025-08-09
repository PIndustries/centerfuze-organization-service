"""
Module Controller for Organization Service
Handles module management operations for organizations
"""

import json
import logging
from typing import Dict, Any
from datetime import datetime

from ..services import ModuleService

logger = logging.getLogger(__name__)


class ModuleController:
    """Controller for module management operations"""
    
    def __init__(self, module_service: ModuleService):
        self.module_service = module_service
        
    async def handle_get_modules(self, msg):
        """Handle get modules request"""
        try:
            data = json.loads(msg.data.decode())
            org_id = data.get("org_id")
            
            logger.info(f"Getting modules for organization: {org_id}")
            
            result = await self.module_service.get_modules(org_id)
            
            response = {
                "success": True,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Error getting modules: {e}")
            response = {
                "success": False,
                "error": {
                    "code": "GET_MODULES_ERROR",
                    "message": str(e)
                }
            }
            
        await msg.respond(json.dumps(response).encode())
        
    async def handle_toggle_module(self, msg):
        """Handle module toggle request"""
        try:
            data = json.loads(msg.data.decode())
            org_id = data.get("org_id")
            module_key = data.get("module_key")
            enabled = data.get("enabled")
            updated_by = data.get("updated_by", "system")
            
            logger.info(f"Toggling module {module_key} to {enabled} for org {org_id}")
            
            result = await self.module_service.toggle_module(
                org_id, module_key, enabled, updated_by
            )
            
            response = {
                "success": True,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Error toggling module: {e}")
            response = {
                "success": False,
                "error": {
                    "code": "TOGGLE_MODULE_ERROR",
                    "message": str(e)
                }
            }
            
        await msg.respond(json.dumps(response).encode())
        
    async def handle_bulk_update_modules(self, msg):
        """Handle bulk module update request"""
        try:
            data = json.loads(msg.data.decode())
            org_id = data.get("org_id")
            enabled_modules = data.get("enabled_modules", [])
            updated_by = data.get("updated_by", "system")
            
            logger.info(f"Bulk updating modules for org {org_id}")
            
            result = await self.module_service.bulk_update_modules(
                org_id, enabled_modules, updated_by
            )
            
            response = {
                "success": True,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Error bulk updating modules: {e}")
            response = {
                "success": False,
                "error": {
                    "code": "BULK_UPDATE_ERROR",
                    "message": str(e)
                }
            }
            
        await msg.respond(json.dumps(response).encode())
        
    async def handle_get_module_status(self, msg):
        """Handle module status request"""
        try:
            data = json.loads(msg.data.decode())
            org_id = data.get("org_id")
            
            logger.info(f"Getting module status for org {org_id}")
            
            result = await self.module_service.get_module_status(org_id)
            
            response = {
                "success": True,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Error getting module status: {e}")
            response = {
                "success": False,
                "error": {
                    "code": "STATUS_ERROR",
                    "message": str(e)
                }
            }
            
        await msg.respond(json.dumps(response).encode())
        
    async def handle_get_available_modules(self, msg):
        """Handle get available modules request"""
        try:
            logger.info("Getting available modules")
            
            result = await self.module_service.get_available_modules()
            
            response = {
                "success": True,
                "data": {
                    "modules": result
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting available modules: {e}")
            response = {
                "success": False,
                "error": {
                    "code": "AVAILABLE_MODULES_ERROR",
                    "message": str(e)
                }
            }
            
        await msg.respond(json.dumps(response).encode())
        
    async def handle_module_usage_stats(self, msg):
        """Handle module usage statistics request"""
        try:
            data = json.loads(msg.data.decode())
            org_id = data.get("org_id")
            module_key = data.get("module_key")
            
            logger.info(f"Getting usage stats for module {module_key} in org {org_id}")
            
            result = await self.module_service.get_module_usage(org_id, module_key)
            
            response = {
                "success": True,
                "data": {
                    "usage": result
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting module usage: {e}")
            response = {
                "success": False,
                "error": {
                    "code": "USAGE_STATS_ERROR",
                    "message": str(e)
                }
            }
            
        await msg.respond(json.dumps(response).encode())
        
    async def handle_module_event(self, msg):
        """Handle incoming module events from admin service"""
        try:
            subject = msg.subject
            data = json.loads(msg.data.decode())
            
            logger.info(f"Received module event on {subject}: {data}")
            
            # Process different types of module events
            if "enabled" in subject or "disabled" in subject:
                await self._process_module_toggle_event(data)
            elif "bulk_update" in subject:
                await self._process_bulk_update_event(data)
            elif "sync_request" in subject:
                await self._process_sync_request(data)
                
        except Exception as e:
            logger.error(f"Error handling module event: {e}")
            
    async def _process_module_toggle_event(self, data: Dict[str, Any]):
        """Process module toggle event"""
        org_id = data.get("org_id")
        module_key = data.get("module_key")
        enabled = data.get("enabled")
        
        logger.info(f"Processing module toggle: {module_key} -> {enabled} for org {org_id}")
        
        # Update local cache or trigger related operations
        await self.module_service.sync_module_state(org_id, module_key, enabled)
        
    async def _process_bulk_update_event(self, data: Dict[str, Any]):
        """Process bulk module update event"""
        org_id = data.get("org_id")
        enabled_modules = data.get("enabled_modules", [])
        
        logger.info(f"Processing bulk module update for org {org_id}")
        
        # Sync all module states
        await self.module_service.sync_all_modules(org_id, enabled_modules)
        
    async def _process_sync_request(self, data: Dict[str, Any]):
        """Process module sync request"""
        org_id = data.get("org_id")
        
        logger.info(f"Processing module sync request for org {org_id}")
        
        # Trigger full sync with admin service
        await self.module_service.full_sync(org_id)