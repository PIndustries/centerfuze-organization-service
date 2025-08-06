"""
Organization data models
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum


class OrganizationStatus(str, Enum):
    """Organization status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive" 
    SUSPENDED = "suspended"
    PENDING = "pending"


class BillingCycle(str, Enum):
    """Billing cycle enumeration"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class Organization(BaseModel):
    """Organization model"""
    id: Optional[str] = Field(None, alias="_id")
    org_id: str = Field(..., description="Unique organization identifier")
    name: str = Field(..., description="Organization name (slug/identifier)")
    display_name: str = Field(..., description="Display name for organization")
    description: Optional[str] = Field(None, description="Organization description")
    status: OrganizationStatus = Field(OrganizationStatus.ACTIVE, description="Organization status")
    owner_id: str = Field(..., description="ID of the organization owner")
    parent_org_id: Optional[str] = Field(None, description="Parent organization ID for sub-orgs")
    
    # Contact Information
    email: Optional[str] = Field(None, description="Primary contact email")
    phone: Optional[str] = Field(None, description="Primary contact phone")
    website: Optional[str] = Field(None, description="Organization website")
    
    # Address Information
    address: Optional[Dict[str, str]] = Field(None, description="Organization address")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Organization tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('name')
    def validate_name(cls, v):
        """Validate organization name format"""
        if not v.replace('-', '').replace('_', '').replace('.', '').isalnum():
            raise ValueError('Organization name must contain only alphanumeric characters, hyphens, underscores, and dots')
        return v.lower()


class OrganizationSettings(BaseModel):
    """Organization settings model"""
    id: Optional[str] = Field(None, alias="_id")
    org_id: str = Field(..., description="Organization ID this settings belong to")
    
    # Billing Settings
    billing_email: Optional[str] = Field(None, description="Billing contact email")
    billing_cycle: BillingCycle = Field(BillingCycle.MONTHLY, description="Billing cycle")
    payment_method_id: Optional[str] = Field(None, description="Default payment method ID")
    tax_id: Optional[str] = Field(None, description="Tax identification number")
    
    # Notification Settings
    notifications: Dict[str, bool] = Field(
        default_factory=lambda: {
            "billing_alerts": True,
            "usage_alerts": True,
            "security_alerts": True,
            "system_updates": True
        },
        description="Notification preferences"
    )
    
    # Feature Flags
    features: Dict[str, bool] = Field(
        default_factory=lambda: {
            "api_access": True,
            "advanced_analytics": False,
            "custom_integrations": False,
            "priority_support": False
        },
        description="Feature flags"
    )
    
    # Security Settings
    security: Dict[str, Any] = Field(
        default_factory=lambda: {
            "require_2fa": False,
            "session_timeout": 3600,
            "allowed_domains": [],
            "ip_whitelist": []
        },
        description="Security settings"
    )
    
    # UI/UX Preferences
    preferences: Dict[str, Any] = Field(
        default_factory=lambda: {
            "theme": "light",
            "timezone": "UTC",
            "date_format": "YYYY-MM-DD",
            "language": "en"
        },
        description="UI/UX preferences"
    )
    
    # Integration Settings
    integrations: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Third-party integration settings"
    )
    
    # Custom Settings
    custom_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom organization-specific settings"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OrganizationLimits(BaseModel):
    """Organization limits model"""
    id: Optional[str] = Field(None, alias="_id")
    org_id: str = Field(..., description="Organization ID these limits belong to")
    
    # User Limits
    max_users: int = Field(100, description="Maximum number of users")
    max_admin_users: int = Field(10, description="Maximum number of admin users")
    
    # Storage Limits (in bytes)
    max_storage_bytes: int = Field(10 * 1024 * 1024 * 1024, description="Maximum storage in bytes (10GB default)")
    
    # API Limits
    api_calls_per_hour: int = Field(1000, description="API calls per hour limit")
    api_calls_per_day: int = Field(10000, description="API calls per day limit")
    
    # Resource Limits
    max_projects: int = Field(50, description="Maximum number of projects")
    max_integrations: int = Field(10, description="Maximum number of integrations")
    max_webhooks: int = Field(20, description="Maximum number of webhooks")
    
    # Feature Limits
    max_custom_fields: int = Field(100, description="Maximum custom fields")
    max_workflows: int = Field(25, description="Maximum workflows")
    max_reports: int = Field(50, description="Maximum saved reports")
    
    # Bandwidth Limits (in bytes)
    monthly_bandwidth_bytes: int = Field(100 * 1024 * 1024 * 1024, description="Monthly bandwidth limit in bytes (100GB default)")
    
    # File Upload Limits (in bytes)
    max_file_size_bytes: int = Field(100 * 1024 * 1024, description="Maximum file size in bytes (100MB default)")
    
    # Time-based Limits
    data_retention_days: int = Field(365, description="Data retention period in days")
    backup_retention_days: int = Field(90, description="Backup retention period in days")
    
    # Custom Limits
    custom_limits: Dict[str, int] = Field(
        default_factory=dict,
        description="Custom organization-specific limits"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Request Models

class CreateOrganizationRequest(BaseModel):
    """Request model for creating organization"""
    name: str = Field(..., min_length=2, max_length=100, description="Organization name (slug)")
    display_name: str = Field(..., min_length=2, max_length=200, description="Display name")
    description: Optional[str] = Field(None, max_length=1000, description="Organization description")
    owner_id: str = Field(..., description="ID of the organization owner")
    parent_org_id: Optional[str] = Field(None, description="Parent organization ID")
    
    # Contact Information
    email: Optional[str] = Field(None, description="Primary contact email")
    phone: Optional[str] = Field(None, description="Primary contact phone")
    website: Optional[str] = Field(None, description="Organization website")
    
    # Address Information
    address: Optional[Dict[str, str]] = Field(None, description="Organization address")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Organization tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate organization name format"""
        if not v.replace('-', '').replace('_', '').replace('.', '').isalnum():
            raise ValueError('Organization name must contain only alphanumeric characters, hyphens, underscores, and dots')
        return v.lower()


class UpdateOrganizationRequest(BaseModel):
    """Request model for updating organization"""
    org_id: str = Field(..., description="Organization ID to update")
    display_name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[OrganizationStatus] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ListOrganizationsRequest(BaseModel):
    """Request model for listing organizations"""
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")
    status: Optional[OrganizationStatus] = Field(None, description="Filter by status")
    owner_id: Optional[str] = Field(None, description="Filter by owner ID")
    parent_org_id: Optional[str] = Field(None, description="Filter by parent organization")
    search: Optional[str] = Field(None, description="Search in name and display_name")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    sort_by: str = Field("created_at", pattern="^(created_at|updated_at|name|display_name)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


class UpdateOrganizationSettingsRequest(BaseModel):
    """Request model for updating organization settings"""
    org_id: str = Field(..., description="Organization ID")
    billing_email: Optional[str] = None
    billing_cycle: Optional[BillingCycle] = None
    payment_method_id: Optional[str] = None
    tax_id: Optional[str] = None
    notifications: Optional[Dict[str, bool]] = None
    features: Optional[Dict[str, bool]] = None
    security: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    integrations: Optional[Dict[str, Dict[str, Any]]] = None
    custom_settings: Optional[Dict[str, Any]] = None


class UpdateOrganizationLimitsRequest(BaseModel):
    """Request model for updating organization limits"""
    org_id: str = Field(..., description="Organization ID")
    max_users: Optional[int] = Field(None, ge=1)
    max_admin_users: Optional[int] = Field(None, ge=1)
    max_storage_bytes: Optional[int] = Field(None, ge=0)
    api_calls_per_hour: Optional[int] = Field(None, ge=0)
    api_calls_per_day: Optional[int] = Field(None, ge=0)
    max_projects: Optional[int] = Field(None, ge=0)
    max_integrations: Optional[int] = Field(None, ge=0)
    max_webhooks: Optional[int] = Field(None, ge=0)
    max_custom_fields: Optional[int] = Field(None, ge=0)
    max_workflows: Optional[int] = Field(None, ge=0)
    max_reports: Optional[int] = Field(None, ge=0)
    monthly_bandwidth_bytes: Optional[int] = Field(None, ge=0)
    max_file_size_bytes: Optional[int] = Field(None, ge=0)
    data_retention_days: Optional[int] = Field(None, ge=1)
    backup_retention_days: Optional[int] = Field(None, ge=1)
    custom_limits: Optional[Dict[str, int]] = None


class GetOrganizationRequest(BaseModel):
    """Request model for getting organization"""
    org_id: str = Field(..., description="Organization ID to retrieve")


class DeleteOrganizationRequest(BaseModel):
    """Request model for deleting organization"""
    org_id: str = Field(..., description="Organization ID to delete")


class GetOrganizationSettingsRequest(BaseModel):
    """Request model for getting organization settings"""
    org_id: str = Field(..., description="Organization ID")


class GetOrganizationLimitsRequest(BaseModel):
    """Request model for getting organization limits"""
    org_id: str = Field(..., description="Organization ID")