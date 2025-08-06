"""
Organization controller for handling NATS requests
"""

import json
import logging
from typing import Dict, Any
from nats.aio.msg import Msg
from pydantic import ValidationError

from ..models.organization import (
    CreateOrganizationRequest,
    UpdateOrganizationRequest,
    ListOrganizationsRequest,
    UpdateOrganizationSettingsRequest,
    UpdateOrganizationLimitsRequest,
    GetOrganizationRequest,
    DeleteOrganizationRequest,
    GetOrganizationSettingsRequest,
    GetOrganizationLimitsRequest
)
from ..services.organization_service import OrganizationService
from ..utils.response import ResponseBuilder

logger = logging.getLogger(__name__)


class OrganizationController:
    """Handles organization-related NATS requests"""
    
    def __init__(self, organization_service: OrganizationService):
        self.organization_service = organization_service
        
    async def handle_create(self, msg: Msg):
        """Handle organization creation"""
        try:
            # Parse request
            data = json.loads(msg.data.decode())
            request = CreateOrganizationRequest(**data)
            
            # Create organization
            organization = await self.organization_service.create_organization(request)
            
            # Return response
            response = ResponseBuilder.success(
                organization.dict(),
                f"Organization '{organization.name}' created successfully"
            )
            await msg.respond(response)
            
        except ValidationError as e:
            logger.warning(f"Validation error in create_organization: {e}")
            response = ResponseBuilder.validation_error(e.errors())
            await msg.respond(response)
            
        except ValueError as e:
            logger.warning(f"Value error in create_organization: {e}")
            response = ResponseBuilder.error(str(e), "INVALID_REQUEST")
            await msg.respond(response)
            
        except Exception as e:
            logger.error(f"Error creating organization: {e}", exc_info=True)
            response = ResponseBuilder.error(
                "Failed to create organization",
                "CREATE_ORGANIZATION_ERROR"
            )
            await msg.respond(response)
            
    async def handle_get(self, msg: Msg):
        """Handle get organization request"""
        try:
            # Parse request
            data = json.loads(msg.data.decode())
            request = GetOrganizationRequest(**data)
            
            # Get organization
            organization = await self.organization_service.get_organization(request.org_id)
            
            if not organization:
                response = ResponseBuilder.not_found("Organization", request.org_id)
            else:
                response = ResponseBuilder.success(
                    organization.dict(),
                    "Organization retrieved successfully"
                )
                
            await msg.respond(response)
            
        except ValidationError as e:
            logger.warning(f"Validation error in get_organization: {e}")
            response = ResponseBuilder.validation_error(e.errors())
            await msg.respond(response)
            
        except Exception as e:
            logger.error(f"Error getting organization: {e}", exc_info=True)
            response = ResponseBuilder.error(
                "Failed to get organization",
                "GET_ORGANIZATION_ERROR"
            )
            await msg.respond(response)
            
    async def handle_update(self, msg: Msg):
        """Handle organization update"""
        try:
            # Parse request
            data = json.loads(msg.data.decode())
            request = UpdateOrganizationRequest(**data)
            
            # Update organization
            organization = await self.organization_service.update_organization(request)
            
            if not organization:
                response = ResponseBuilder.not_found("Organization", request.org_id)
            else:
                response = ResponseBuilder.success(
                    organization.dict(),
                    "Organization updated successfully"
                )
                
            await msg.respond(response)
            
        except ValidationError as e:
            logger.warning(f"Validation error in update_organization: {e}")
            response = ResponseBuilder.validation_error(e.errors())
            await msg.respond(response)
            
        except Exception as e:
            logger.error(f"Error updating organization: {e}", exc_info=True)
            response = ResponseBuilder.error(
                "Failed to update organization",
                "UPDATE_ORGANIZATION_ERROR"
            )
            await msg.respond(response)
            
    async def handle_delete(self, msg: Msg):
        """Handle organization deletion"""
        try:
            # Parse request
            data = json.loads(msg.data.decode())
            request = DeleteOrganizationRequest(**data)
            
            # Delete organization
            success = await self.organization_service.delete_organization(request.org_id)
            
            if not success:
                response = ResponseBuilder.not_found("Organization", request.org_id)
            else:
                response = ResponseBuilder.success(
                    {"org_id": request.org_id},
                    "Organization deleted successfully"
                )
                
            await msg.respond(response)
            
        except ValidationError as e:
            logger.warning(f"Validation error in delete_organization: {e}")
            response = ResponseBuilder.validation_error(e.errors())
            await msg.respond(response)
            
        except Exception as e:
            logger.error(f"Error deleting organization: {e}", exc_info=True)
            response = ResponseBuilder.error(
                "Failed to delete organization",
                "DELETE_ORGANIZATION_ERROR"
            )
            await msg.respond(response)
            
    async def handle_list(self, msg: Msg):
        """Handle list organizations request"""
        try:
            # Parse request
            data = json.loads(msg.data.decode())
            request = ListOrganizationsRequest(**data)
            
            # List organizations
            organizations, total_count = await self.organization_service.list_organizations(request)
            
            # Calculate pagination info
            total_pages = (total_count + request.limit - 1) // request.limit
            
            response_data = {
                "organizations": [org.dict() for org in organizations],
                "pagination": {
                    "current_page": request.page,
                    "total_pages": total_pages,
                    "total_count": total_count,
                    "limit": request.limit,
                    "has_next": request.page < total_pages,
                    "has_prev": request.page > 1
                }
            }
            
            response = ResponseBuilder.success(
                response_data,
                f"Retrieved {len(organizations)} organizations"
            )
            await msg.respond(response)
            
        except ValidationError as e:
            logger.warning(f"Validation error in list_organizations: {e}")
            response = ResponseBuilder.validation_error(e.errors())
            await msg.respond(response)
            
        except Exception as e:
            logger.error(f"Error listing organizations: {e}", exc_info=True)
            response = ResponseBuilder.error(
                "Failed to list organizations",
                "LIST_ORGANIZATIONS_ERROR"
            )
            await msg.respond(response)
            
    async def handle_search(self, msg: Msg):
        """Handle search organizations request"""
        try:
            # Parse request
            data = json.loads(msg.data.decode())
            search_term = data.get("search_term", "")
            limit = data.get("limit", 20)
            
            # Search organizations
            organizations = await self.organization_service.search_organizations(search_term, limit)
            
            response = ResponseBuilder.success(
                {"organizations": [org.dict() for org in organizations]},
                f"Found {len(organizations)} organizations"
            )
            await msg.respond(response)
            
        except Exception as e:
            logger.error(f"Error searching organizations: {e}", exc_info=True)
            response = ResponseBuilder.error(
                "Failed to search organizations",
                "SEARCH_ORGANIZATIONS_ERROR"
            )
            await msg.respond(response)
            
    # Settings handlers
    
    async def handle_get_settings(self, msg: Msg):
        """Handle get organization settings"""
        try:
            # Parse request
            data = json.loads(msg.data.decode())
            request = GetOrganizationSettingsRequest(**data)
            
            # Get settings
            settings = await self.organization_service.get_organization_settings(request.org_id)
            
            if not settings:
                response = ResponseBuilder.not_found("Organization settings", request.org_id)
            else:
                response = ResponseBuilder.success(
                    settings.dict(),
                    "Organization settings retrieved successfully"
                )
                
            await msg.respond(response)
            
        except ValidationError as e:
            logger.warning(f"Validation error in get_settings: {e}")
            response = ResponseBuilder.validation_error(e.errors())
            await msg.respond(response)
            
        except Exception as e:
            logger.error(f"Error getting organization settings: {e}", exc_info=True)
            response = ResponseBuilder.error(
                "Failed to get organization settings",
                "GET_SETTINGS_ERROR"
            )
            await msg.respond(response)
            
    async def handle_update_settings(self, msg: Msg):
        """Handle update organization settings"""
        try:
            # Parse request
            data = json.loads(msg.data.decode())
            request = UpdateOrganizationSettingsRequest(**data)
            
            # Update settings
            settings = await self.organization_service.update_organization_settings(request)
            
            if not settings:
                response = ResponseBuilder.not_found("Organization", request.org_id)
            else:
                response = ResponseBuilder.success(
                    settings.dict(),
                    "Organization settings updated successfully"
                )
                
            await msg.respond(response)
            
        except ValidationError as e:
            logger.warning(f"Validation error in update_settings: {e}")
            response = ResponseBuilder.validation_error(e.errors())
            await msg.respond(response)
            
        except Exception as e:
            logger.error(f"Error updating organization settings: {e}", exc_info=True)
            response = ResponseBuilder.error(
                "Failed to update organization settings",
                "UPDATE_SETTINGS_ERROR"
            )
            await msg.respond(response)
            
    # Limits handlers
    
    async def handle_get_limits(self, msg: Msg):
        """Handle get organization limits"""
        try:
            # Parse request
            data = json.loads(msg.data.decode())
            request = GetOrganizationLimitsRequest(**data)
            
            # Get limits
            limits = await self.organization_service.get_organization_limits(request.org_id)
            
            if not limits:
                response = ResponseBuilder.not_found("Organization limits", request.org_id)
            else:
                response = ResponseBuilder.success(
                    limits.dict(),
                    "Organization limits retrieved successfully"
                )
                
            await msg.respond(response)
            
        except ValidationError as e:
            logger.warning(f"Validation error in get_limits: {e}")
            response = ResponseBuilder.validation_error(e.errors())
            await msg.respond(response)
            
        except Exception as e:
            logger.error(f"Error getting organization limits: {e}", exc_info=True)
            response = ResponseBuilder.error(
                "Failed to get organization limits",
                "GET_LIMITS_ERROR"
            )
            await msg.respond(response)
            
    async def handle_update_limits(self, msg: Msg):
        """Handle update organization limits"""
        try:
            # Parse request
            data = json.loads(msg.data.decode())
            request = UpdateOrganizationLimitsRequest(**data)
            
            # Update limits
            limits = await self.organization_service.update_organization_limits(request)
            
            if not limits:
                response = ResponseBuilder.not_found("Organization", request.org_id)
            else:
                response = ResponseBuilder.success(
                    limits.dict(),
                    "Organization limits updated successfully"
                )
                
            await msg.respond(response)
            
        except ValidationError as e:
            logger.warning(f"Validation error in update_limits: {e}")
            response = ResponseBuilder.validation_error(e.errors())
            await msg.respond(response)
            
        except Exception as e:
            logger.error(f"Error updating organization limits: {e}", exc_info=True)
            response = ResponseBuilder.error(
                "Failed to update organization limits",
                "UPDATE_LIMITS_ERROR"
            )
            await msg.respond(response)