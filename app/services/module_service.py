"""
Module Service for Organization Service
Business logic for module management
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pymongo.database import Database

from .event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class ModuleService:
    """Service for module management operations"""
    
    # Default available modules
    AVAILABLE_MODULES = [
        {'key': 'dashboard', 'name': 'Dashboard', 'icon': 'fa-tachometer-alt'},
        {'key': 'select_organization', 'name': 'Select Organization', 'icon': 'fa-building'},
        {'key': 'clients', 'name': 'Clients', 'icon': 'fa-users'},
        {'key': 'discounts', 'name': 'Discounts', 'icon': 'fa-tags'},
        {'key': 'invoices', 'name': 'Invoices', 'icon': 'fa-file-invoice-dollar'},
        {'key': 'items', 'name': 'Items', 'icon': 'fa-box'},
        {'key': 'locations', 'name': 'Locations', 'icon': 'fa-map-marker-alt'},
        {'key': 'payment_methods', 'name': 'Payment Methods', 'icon': 'fa-credit-card'},
        {'key': 'providers', 'name': 'Providers', 'icon': 'fa-user-md'},
        {'key': 'sales_reps', 'name': 'Sales Reps', 'icon': 'fa-user-tie'},
        {'key': 'subscriptions', 'name': 'Subscriptions', 'icon': 'fa-sync-alt'},
        {'key': 'support_requests', 'name': 'Support Requests', 'icon': 'fa-headset'},
        {'key': 'reports', 'name': 'Reports', 'icon': 'fa-chart-bar'},
        {'key': 'credit_grants', 'name': 'Credit Grants', 'icon': 'fa-coins'},
        {'key': 'fuze_ai', 'name': 'Fuze AI Assistant', 'icon': 'fa-robot'},
        {'key': 'billing_admin', 'name': 'Billing & Payments Admin', 'icon': 'fa-cash-register'}
    ]
    
    def __init__(self, db: Database, event_publisher: EventPublisher):
        self.db = db
        self.event_publisher = event_publisher
        self.module_permissions_collection = db['module_permissions']
        self.module_usage_collection = db['module_usage']
        
    async def get_modules(self, org_id: str) -> Dict[str, Any]:
        """Get modules for an organization"""
        try:
            # Get module permissions
            permissions = self.module_permissions_collection.find_one({"org_id": org_id})
            
            if permissions:
                enabled_modules = permissions.get('enabled_modules', [])
            else:
                # Default: enable all modules for new organizations
                enabled_modules = [module['key'] for module in self.AVAILABLE_MODULES]
                # Save the default
                self.module_permissions_collection.insert_one({
                    "org_id": org_id,
                    "enabled_modules": enabled_modules,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                
            # Get organization info
            org = self.db['organizations'].find_one({"_id": org_id})
            
            return {
                "organization": {
                    "org_id": org_id,
                    "name": org.get('name', org_id) if org else org_id
                },
                "modules": self.AVAILABLE_MODULES,
                "enabled_modules": enabled_modules
            }
            
        except Exception as e:
            logger.error(f"Error getting modules for org {org_id}: {e}")
            raise
            
    async def toggle_module(self, org_id: str, module_key: str, enabled: bool, updated_by: str) -> Dict[str, Any]:
        """Toggle a module on/off for an organization"""
        try:
            # Validate module key
            if not any(module['key'] == module_key for module in self.AVAILABLE_MODULES):
                raise ValueError(f"Invalid module key: {module_key}")
                
            # Get current permissions
            permissions = self.module_permissions_collection.find_one({"org_id": org_id})
            
            if permissions:
                enabled_modules = permissions.get('enabled_modules', [])
            else:
                enabled_modules = [module['key'] for module in self.AVAILABLE_MODULES]
                
            # Update the list
            if enabled and module_key not in enabled_modules:
                enabled_modules.append(module_key)
            elif not enabled and module_key in enabled_modules:
                enabled_modules.remove(module_key)
                
            # Save to database
            self.module_permissions_collection.update_one(
                {"org_id": org_id},
                {
                    "$set": {
                        "org_id": org_id,
                        "enabled_modules": enabled_modules,
                        "updated_at": datetime.utcnow(),
                        "updated_by": updated_by
                    }
                },
                upsert=True
            )
            
            # Publish event
            action = "enabled" if enabled else "disabled"
            await self.event_publisher.publish(
                f"centerfuze.organization.module.{action}",
                {
                    "org_id": org_id,
                    "module_key": module_key,
                    "enabled": enabled,
                    "updated_by": updated_by,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Track usage
            await self._track_module_action(org_id, module_key, action, updated_by)
            
            return {
                "module_key": module_key,
                "enabled": enabled,
                "action": action
            }
            
        except Exception as e:
            logger.error(f"Error toggling module {module_key} for org {org_id}: {e}")
            raise
            
    async def bulk_update_modules(self, org_id: str, enabled_modules: List[str], updated_by: str) -> Dict[str, Any]:
        """Bulk update modules for an organization"""
        try:
            # Validate module keys
            valid_keys = [module['key'] for module in self.AVAILABLE_MODULES]
            enabled_modules = [key for key in enabled_modules if key in valid_keys]
            
            # Get previous state
            prev_doc = self.module_permissions_collection.find_one({"org_id": org_id})
            prev_modules = prev_doc.get('enabled_modules', []) if prev_doc else []
            
            # Save to database
            self.module_permissions_collection.update_one(
                {"org_id": org_id},
                {
                    "$set": {
                        "org_id": org_id,
                        "enabled_modules": enabled_modules,
                        "updated_at": datetime.utcnow(),
                        "updated_by": updated_by
                    }
                },
                upsert=True
            )
            
            # Calculate changes
            modules_added = [m for m in enabled_modules if m not in prev_modules]
            modules_removed = [m for m in prev_modules if m not in enabled_modules]
            
            # Publish event
            await self.event_publisher.publish(
                "centerfuze.organization.module.bulk_update",
                {
                    "org_id": org_id,
                    "enabled_modules": enabled_modules,
                    "previous_modules": prev_modules,
                    "modules_added": modules_added,
                    "modules_removed": modules_removed,
                    "updated_by": updated_by,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "enabled_modules": enabled_modules,
                "modules_added": modules_added,
                "modules_removed": modules_removed
            }
            
        except Exception as e:
            logger.error(f"Error bulk updating modules for org {org_id}: {e}")
            raise
            
    async def get_module_status(self, org_id: str) -> Dict[str, Any]:
        """Get current module status for an organization"""
        try:
            modules_data = await self.get_modules(org_id)
            
            # Add usage statistics
            usage_stats = await self._get_usage_summary(org_id)
            
            return {
                **modules_data,
                "usage_summary": usage_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting module status for org {org_id}: {e}")
            raise
            
    async def get_available_modules(self) -> List[Dict[str, Any]]:
        """Get all available modules"""
        return self.AVAILABLE_MODULES
        
    async def get_module_usage(self, org_id: str, module_key: Optional[str] = None) -> Dict[str, Any]:
        """Get module usage statistics"""
        try:
            query = {"org_id": org_id}
            if module_key:
                query["module_key"] = module_key
                
            # Aggregate usage data
            pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": "$module_key",
                        "total_actions": {"$sum": 1},
                        "last_used": {"$max": "$timestamp"},
                        "unique_users": {"$addToSet": "$user"}
                    }
                }
            ]
            
            usage_data = list(self.module_usage_collection.aggregate(pipeline))
            
            result = {}
            for item in usage_data:
                module_key = item["_id"]
                result[module_key] = {
                    "total_actions": item["total_actions"],
                    "last_used": item["last_used"].isoformat() if item["last_used"] else None,
                    "unique_users_count": len(item["unique_users"])
                }
                
            return result
            
        except Exception as e:
            logger.error(f"Error getting module usage: {e}")
            raise
            
    async def sync_module_state(self, org_id: str, module_key: str, enabled: bool):
        """Sync module state from external event"""
        try:
            logger.info(f"Syncing module state: {module_key} -> {enabled} for org {org_id}")
            
            # Update local cache/database if needed
            # This is called when receiving events from admin service
            
            # Could trigger additional operations based on module state change
            if not enabled:
                # Module disabled - could clean up resources
                await self._cleanup_module_resources(org_id, module_key)
            else:
                # Module enabled - could initialize resources
                await self._initialize_module_resources(org_id, module_key)
                
        except Exception as e:
            logger.error(f"Error syncing module state: {e}")
            
    async def sync_all_modules(self, org_id: str, enabled_modules: List[str]):
        """Sync all module states from external event"""
        try:
            logger.info(f"Syncing all modules for org {org_id}")
            
            # Get current state
            permissions = self.module_permissions_collection.find_one({"org_id": org_id})
            current_modules = permissions.get('enabled_modules', []) if permissions else []
            
            # Determine changes
            modules_to_enable = [m for m in enabled_modules if m not in current_modules]
            modules_to_disable = [m for m in current_modules if m not in enabled_modules]
            
            # Process changes
            for module_key in modules_to_disable:
                await self._cleanup_module_resources(org_id, module_key)
                
            for module_key in modules_to_enable:
                await self._initialize_module_resources(org_id, module_key)
                
        except Exception as e:
            logger.error(f"Error syncing all modules: {e}")
            
    async def full_sync(self, org_id: str):
        """Perform full module sync with admin service"""
        try:
            logger.info(f"Performing full module sync for org {org_id}")
            
            # Get current state
            modules_data = await self.get_modules(org_id)
            
            # Publish sync response event
            await self.event_publisher.publish(
                "centerfuze.organization.module.sync_response",
                {
                    "org_id": org_id,
                    "modules": modules_data["modules"],
                    "enabled_modules": modules_data["enabled_modules"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error performing full sync: {e}")
            
    async def _track_module_action(self, org_id: str, module_key: str, action: str, user: str):
        """Track module action for usage statistics"""
        try:
            self.module_usage_collection.insert_one({
                "org_id": org_id,
                "module_key": module_key,
                "action": action,
                "user": user,
                "timestamp": datetime.utcnow()
            })
        except Exception as e:
            logger.error(f"Error tracking module action: {e}")
            
    async def _get_usage_summary(self, org_id: str) -> Dict[str, Any]:
        """Get usage summary for all modules"""
        try:
            # Get last 30 days of usage
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            pipeline = [
                {
                    "$match": {
                        "org_id": org_id,
                        "timestamp": {"$gte": cutoff_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_actions": {"$sum": 1},
                        "unique_modules": {"$addToSet": "$module_key"},
                        "unique_users": {"$addToSet": "$user"}
                    }
                }
            ]
            
            result = list(self.module_usage_collection.aggregate(pipeline))
            
            if result:
                summary = result[0]
                return {
                    "total_actions_30d": summary["total_actions"],
                    "active_modules_count": len(summary["unique_modules"]),
                    "active_users_count": len(summary["unique_users"])
                }
            else:
                return {
                    "total_actions_30d": 0,
                    "active_modules_count": 0,
                    "active_users_count": 0
                }
                
        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")
            return {}
            
    async def _cleanup_module_resources(self, org_id: str, module_key: str):
        """Clean up resources when module is disabled"""
        logger.info(f"Cleaning up resources for module {module_key} in org {org_id}")
        # Implementation specific to each module
        pass
        
    async def _initialize_module_resources(self, org_id: str, module_key: str):
        """Initialize resources when module is enabled"""
        logger.info(f"Initializing resources for module {module_key} in org {org_id}")
        # Implementation specific to each module
        pass