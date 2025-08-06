"""
Organization service for managing organizations, settings, and limits
"""

import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError
from pymongo import ASCENDING, DESCENDING

from ..models.organization import (
    Organization, OrganizationSettings, OrganizationLimits,
    CreateOrganizationRequest, UpdateOrganizationRequest, ListOrganizationsRequest,
    UpdateOrganizationSettingsRequest, UpdateOrganizationLimitsRequest,
    OrganizationStatus
)
from .event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class OrganizationService:
    """Service for managing organizations and their settings/limits"""
    
    def __init__(self, database: Database, event_publisher: EventPublisher):
        self.db = database
        self.event_publisher = event_publisher
        self.orgs_collection = database.organizations
        self.settings_collection = database.organization_settings
        self.limits_collection = database.organization_limits
        
    async def create_organization(self, request: CreateOrganizationRequest) -> Organization:
        """Create a new organization"""
        try:
            # Generate unique org_id
            org_id = f"org_{uuid.uuid4().hex[:8]}"
            
            # Check if name already exists
            existing = self.orgs_collection.find_one({"name": request.name})
            if existing:
                raise ValueError(f"Organization with name '{request.name}' already exists")
                
            # Create organization document
            now = datetime.utcnow()
            org_doc = {
                "org_id": org_id,
                "name": request.name,
                "display_name": request.display_name,
                "description": request.description,
                "status": OrganizationStatus.ACTIVE.value,
                "owner_id": request.owner_id,
                "parent_org_id": request.parent_org_id,
                "email": request.email,
                "phone": request.phone,
                "website": request.website,
                "address": request.address,
                "tags": request.tags,
                "metadata": request.metadata,
                "created_at": now,
                "updated_at": now
            }
            
            # Insert organization
            result = self.orgs_collection.insert_one(org_doc)
            org_doc["_id"] = str(result.inserted_id)
            
            # Create default settings
            await self._create_default_settings(org_id)
            
            # Create default limits
            await self._create_default_limits(org_id)
            
            # Create organization object
            organization = Organization(**org_doc)
            
            # Publish event
            await self.event_publisher.publish(
                "organization.created",
                {
                    "org_id": org_id,
                    "name": request.name,
                    "display_name": request.display_name,
                    "owner_id": request.owner_id
                }
            )
            
            logger.info(f"Created organization: {org_id}")
            return organization
            
        except DuplicateKeyError as e:
            logger.error(f"Duplicate organization name: {request.name}")
            raise ValueError(f"Organization with name '{request.name}' already exists")
        except Exception as e:
            logger.error(f"Error creating organization: {e}", exc_info=True)
            raise
            
    async def get_organization(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID"""
        try:
            org_doc = self.orgs_collection.find_one({"org_id": org_id})
            if not org_doc:
                return None
                
            org_doc["_id"] = str(org_doc["_id"])
            return Organization(**org_doc)
            
        except Exception as e:
            logger.error(f"Error getting organization {org_id}: {e}", exc_info=True)
            raise
            
    async def update_organization(self, request: UpdateOrganizationRequest) -> Optional[Organization]:
        """Update an organization"""
        try:
            # Build update document
            update_doc = {"updated_at": datetime.utcnow()}
            
            if request.display_name is not None:
                update_doc["display_name"] = request.display_name
            if request.description is not None:
                update_doc["description"] = request.description
            if request.status is not None:
                update_doc["status"] = request.status.value
            if request.email is not None:
                update_doc["email"] = request.email
            if request.phone is not None:
                update_doc["phone"] = request.phone
            if request.website is not None:
                update_doc["website"] = request.website
            if request.address is not None:
                update_doc["address"] = request.address
            if request.tags is not None:
                update_doc["tags"] = request.tags
            if request.metadata is not None:
                update_doc["metadata"] = request.metadata
                
            # Update organization
            result = self.orgs_collection.update_one(
                {"org_id": request.org_id},
                {"$set": update_doc}
            )
            
            if result.matched_count == 0:
                return None
                
            # Get updated organization
            updated_org = await self.get_organization(request.org_id)
            
            # Publish event
            await self.event_publisher.publish(
                "organization.updated",
                {
                    "org_id": request.org_id,
                    "updated_fields": list(update_doc.keys())
                }
            )
            
            logger.info(f"Updated organization: {request.org_id}")
            return updated_org
            
        except Exception as e:
            logger.error(f"Error updating organization {request.org_id}: {e}", exc_info=True)
            raise
            
    async def delete_organization(self, org_id: str) -> bool:
        """Delete an organization and its related data"""
        try:
            # Check if organization exists
            org = await self.get_organization(org_id)
            if not org:
                return False
                
            # Delete organization
            self.orgs_collection.delete_one({"org_id": org_id})
            
            # Delete settings
            self.settings_collection.delete_one({"org_id": org_id})
            
            # Delete limits
            self.limits_collection.delete_one({"org_id": org_id})
            
            # Publish event
            await self.event_publisher.publish(
                "organization.deleted",
                {
                    "org_id": org_id,
                    "name": org.name
                }
            )
            
            logger.info(f"Deleted organization: {org_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting organization {org_id}: {e}", exc_info=True)
            raise
            
    async def list_organizations(self, request: ListOrganizationsRequest) -> Tuple[List[Organization], int]:
        """List organizations with pagination and filtering"""
        try:
            # Build query
            query = {}
            
            if request.status:
                query["status"] = request.status.value
            if request.owner_id:
                query["owner_id"] = request.owner_id
            if request.parent_org_id:
                query["parent_org_id"] = request.parent_org_id
            if request.tags:
                query["tags"] = {"$in": request.tags}
            if request.search:
                query["$or"] = [
                    {"name": {"$regex": request.search, "$options": "i"}},
                    {"display_name": {"$regex": request.search, "$options": "i"}}
                ]
                
            # Build sort
            sort_order = ASCENDING if request.sort_order == "asc" else DESCENDING
            sort_spec = [(request.sort_by, sort_order)]
            
            # Get total count
            total_count = self.orgs_collection.count_documents(query)
            
            # Get organizations
            skip = (request.page - 1) * request.limit
            cursor = self.orgs_collection.find(query).sort(sort_spec).skip(skip).limit(request.limit)
            
            organizations = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                organizations.append(Organization(**doc))
                
            return organizations, total_count
            
        except Exception as e:
            logger.error(f"Error listing organizations: {e}", exc_info=True)
            raise
            
    async def search_organizations(self, search_term: str, limit: int = 20) -> List[Organization]:
        """Search organizations by name or display name"""
        try:
            query = {
                "$or": [
                    {"name": {"$regex": search_term, "$options": "i"}},
                    {"display_name": {"$regex": search_term, "$options": "i"}}
                ]
            }
            
            cursor = self.orgs_collection.find(query).limit(limit)
            organizations = []
            
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                organizations.append(Organization(**doc))
                
            return organizations
            
        except Exception as e:
            logger.error(f"Error searching organizations: {e}", exc_info=True)
            raise
            
    # Settings Management
    
    async def get_organization_settings(self, org_id: str) -> Optional[OrganizationSettings]:
        """Get organization settings"""
        try:
            settings_doc = self.settings_collection.find_one({"org_id": org_id})
            if not settings_doc:
                # Create default settings if they don't exist
                return await self._create_default_settings(org_id)
                
            settings_doc["_id"] = str(settings_doc["_id"])
            return OrganizationSettings(**settings_doc)
            
        except Exception as e:
            logger.error(f"Error getting organization settings {org_id}: {e}", exc_info=True)
            raise
            
    async def update_organization_settings(self, request: UpdateOrganizationSettingsRequest) -> Optional[OrganizationSettings]:
        """Update organization settings"""
        try:
            # Build update document
            update_doc = {"updated_at": datetime.utcnow()}
            
            if request.billing_email is not None:
                update_doc["billing_email"] = request.billing_email
            if request.billing_cycle is not None:
                update_doc["billing_cycle"] = request.billing_cycle.value
            if request.payment_method_id is not None:
                update_doc["payment_method_id"] = request.payment_method_id
            if request.tax_id is not None:
                update_doc["tax_id"] = request.tax_id
            if request.notifications is not None:
                update_doc["notifications"] = request.notifications
            if request.features is not None:
                update_doc["features"] = request.features
            if request.security is not None:
                update_doc["security"] = request.security
            if request.preferences is not None:
                update_doc["preferences"] = request.preferences
            if request.integrations is not None:
                update_doc["integrations"] = request.integrations
            if request.custom_settings is not None:
                update_doc["custom_settings"] = request.custom_settings
                
            # Update settings
            result = self.settings_collection.update_one(
                {"org_id": request.org_id},
                {"$set": update_doc},
                upsert=True
            )
            
            # Get updated settings
            updated_settings = await self.get_organization_settings(request.org_id)
            
            # Publish event
            await self.event_publisher.publish(
                "organization.settings.updated",
                {
                    "org_id": request.org_id,
                    "updated_fields": list(update_doc.keys())
                }
            )
            
            logger.info(f"Updated organization settings: {request.org_id}")
            return updated_settings
            
        except Exception as e:
            logger.error(f"Error updating organization settings {request.org_id}: {e}", exc_info=True)
            raise
            
    # Limits Management
    
    async def get_organization_limits(self, org_id: str) -> Optional[OrganizationLimits]:
        """Get organization limits"""
        try:
            limits_doc = self.limits_collection.find_one({"org_id": org_id})
            if not limits_doc:
                # Create default limits if they don't exist
                return await self._create_default_limits(org_id)
                
            limits_doc["_id"] = str(limits_doc["_id"])
            return OrganizationLimits(**limits_doc)
            
        except Exception as e:
            logger.error(f"Error getting organization limits {org_id}: {e}", exc_info=True)
            raise
            
    async def update_organization_limits(self, request: UpdateOrganizationLimitsRequest) -> Optional[OrganizationLimits]:
        """Update organization limits"""
        try:
            # Build update document
            update_doc = {"updated_at": datetime.utcnow()}
            
            if request.max_users is not None:
                update_doc["max_users"] = request.max_users
            if request.max_admin_users is not None:
                update_doc["max_admin_users"] = request.max_admin_users
            if request.max_storage_bytes is not None:
                update_doc["max_storage_bytes"] = request.max_storage_bytes
            if request.api_calls_per_hour is not None:
                update_doc["api_calls_per_hour"] = request.api_calls_per_hour
            if request.api_calls_per_day is not None:
                update_doc["api_calls_per_day"] = request.api_calls_per_day
            if request.max_projects is not None:
                update_doc["max_projects"] = request.max_projects
            if request.max_integrations is not None:
                update_doc["max_integrations"] = request.max_integrations
            if request.max_webhooks is not None:
                update_doc["max_webhooks"] = request.max_webhooks
            if request.max_custom_fields is not None:
                update_doc["max_custom_fields"] = request.max_custom_fields
            if request.max_workflows is not None:
                update_doc["max_workflows"] = request.max_workflows
            if request.max_reports is not None:
                update_doc["max_reports"] = request.max_reports
            if request.monthly_bandwidth_bytes is not None:
                update_doc["monthly_bandwidth_bytes"] = request.monthly_bandwidth_bytes
            if request.max_file_size_bytes is not None:
                update_doc["max_file_size_bytes"] = request.max_file_size_bytes
            if request.data_retention_days is not None:
                update_doc["data_retention_days"] = request.data_retention_days
            if request.backup_retention_days is not None:
                update_doc["backup_retention_days"] = request.backup_retention_days
            if request.custom_limits is not None:
                update_doc["custom_limits"] = request.custom_limits
                
            # Update limits
            result = self.limits_collection.update_one(
                {"org_id": request.org_id},
                {"$set": update_doc},
                upsert=True
            )
            
            # Get updated limits
            updated_limits = await self.get_organization_limits(request.org_id)
            
            # Publish event
            await self.event_publisher.publish(
                "organization.limits.updated",
                {
                    "org_id": request.org_id,
                    "updated_fields": list(update_doc.keys())
                }
            )
            
            logger.info(f"Updated organization limits: {request.org_id}")
            return updated_limits
            
        except Exception as e:
            logger.error(f"Error updating organization limits {request.org_id}: {e}", exc_info=True)
            raise
            
    # Helper Methods
    
    async def _create_default_settings(self, org_id: str) -> OrganizationSettings:
        """Create default settings for an organization"""
        try:
            now = datetime.utcnow()
            settings_doc = {
                "org_id": org_id,
                "billing_email": None,
                "billing_cycle": "monthly",
                "payment_method_id": None,
                "tax_id": None,
                "notifications": {
                    "billing_alerts": True,
                    "usage_alerts": True,
                    "security_alerts": True,
                    "system_updates": True
                },
                "features": {
                    "api_access": True,
                    "advanced_analytics": False,
                    "custom_integrations": False,
                    "priority_support": False
                },
                "security": {
                    "require_2fa": False,
                    "session_timeout": 3600,
                    "allowed_domains": [],
                    "ip_whitelist": []
                },
                "preferences": {
                    "theme": "light",
                    "timezone": "UTC",
                    "date_format": "YYYY-MM-DD",
                    "language": "en"
                },
                "integrations": {},
                "custom_settings": {},
                "created_at": now,
                "updated_at": now
            }
            
            result = self.settings_collection.insert_one(settings_doc)
            settings_doc["_id"] = str(result.inserted_id)
            
            return OrganizationSettings(**settings_doc)
            
        except Exception as e:
            logger.error(f"Error creating default settings for {org_id}: {e}", exc_info=True)
            raise
            
    async def _create_default_limits(self, org_id: str) -> OrganizationLimits:
        """Create default limits for an organization"""
        try:
            now = datetime.utcnow()
            limits_doc = {
                "org_id": org_id,
                "max_users": 100,
                "max_admin_users": 10,
                "max_storage_bytes": 10 * 1024 * 1024 * 1024,  # 10GB
                "api_calls_per_hour": 1000,
                "api_calls_per_day": 10000,
                "max_projects": 50,
                "max_integrations": 10,
                "max_webhooks": 20,
                "max_custom_fields": 100,
                "max_workflows": 25,
                "max_reports": 50,
                "monthly_bandwidth_bytes": 100 * 1024 * 1024 * 1024,  # 100GB
                "max_file_size_bytes": 100 * 1024 * 1024,  # 100MB
                "data_retention_days": 365,
                "backup_retention_days": 90,
                "custom_limits": {},
                "created_at": now,
                "updated_at": now
            }
            
            result = self.limits_collection.insert_one(limits_doc)
            limits_doc["_id"] = str(result.inserted_id)
            
            return OrganizationLimits(**limits_doc)
            
        except Exception as e:
            logger.error(f"Error creating default limits for {org_id}: {e}", exc_info=True)
            raise