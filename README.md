# CenterFuze Organization Service

A microservice for managing organizations, their settings, and limits in the CenterFuze platform. This service provides comprehensive organization lifecycle management with support for hierarchical organizations, granular settings control, and flexible resource limits.

## Features

- **Organization Management**: Complete CRUD operations for organizations
- **Hierarchical Organizations**: Support for parent-child organization relationships
- **Settings Management**: Comprehensive organization settings including billing, security, notifications, and preferences
- **Limits Management**: Flexible resource limits and quotas per organization
- **NATS Integration**: Event-driven architecture with NATS messaging
- **MongoDB Storage**: Scalable document storage with proper indexing
- **Health Monitoring**: Built-in health checks and monitoring endpoints

## Architecture

The service follows a clean architecture pattern:

```
app/
├── config/          # Configuration and database management
├── models/          # Pydantic data models
├── services/        # Business logic layer
├── controllers/     # NATS message handlers
└── utils/           # Utility functions
```

## Data Models

### Organization
Core organization entity with:
- Basic information (name, display_name, description)
- Contact details (email, phone, website, address)
- Status management (active, inactive, suspended, pending)
- Hierarchical support (parent_org_id)
- Metadata and tags

### OrganizationSettings
Comprehensive settings management:
- **Billing**: email, cycle, payment methods, tax information
- **Notifications**: alerts and system updates preferences
- **Features**: feature flags and access controls
- **Security**: 2FA requirements, session timeouts, IP restrictions
- **Preferences**: UI/UX settings, timezone, language
- **Integrations**: third-party service configurations

### OrganizationLimits
Resource limits and quotas:
- **Users**: max users and admin users
- **Storage**: storage quotas in bytes
- **API**: rate limits per hour/day
- **Resources**: projects, integrations, webhooks
- **Features**: custom fields, workflows, reports
- **Bandwidth**: monthly bandwidth limits
- **Files**: maximum file sizes
- **Retention**: data and backup retention periods

## NATS Topics

The service subscribes to the following NATS topics:

### Organization Operations
- `organization.create` - Create new organization
- `organization.get` - Get organization by ID
- `organization.update` - Update organization
- `organization.delete` - Delete organization
- `organization.list` - List organizations with pagination/filtering
- `organization.search` - Search organizations

### Settings Operations
- `organization.settings.get` - Get organization settings
- `organization.settings.update` - Update organization settings

### Limits Operations
- `organization.limits.get` - Get organization limits
- `organization.limits.update` - Update organization limits

### Health Check
- `organization.health` - Service health check

## Events Published

The service publishes the following events:

- `centerfuze.organization.created` - When organization is created
- `centerfuze.organization.updated` - When organization is updated
- `centerfuze.organization.deleted` - When organization is deleted
- `centerfuze.organization.settings.updated` - When settings are updated
- `centerfuze.organization.limits.updated` - When limits are updated

## Configuration

The service uses environment variables for configuration:

### Required
- `MONGO_URL` - MongoDB connection string
- `NATS_URL` - NATS server URL

### Optional
- `MONGO_DB_NAME` - Database name (default: centerfuze)
- `NATS_USER` - NATS username for authentication
- `NATS_PASSWORD` - NATS password for authentication
- `REDIS_URL` - Redis URL for caching (default: redis://localhost:6379/0)
- `SECRET_KEY` - Secret key for JWT and other security features
- `LOG_LEVEL` - Logging level (default: INFO)

## Installation

### Using Docker

```bash
# Build the image
docker build -t centerfuze-organization-service .

# Run with environment variables
docker run -e MONGO_URL=mongodb://localhost:27017 \
           -e NATS_URL=nats://localhost:4222 \
           centerfuze-organization-service
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MONGO_URL=mongodb://localhost:27017
export NATS_URL=nats://localhost:4222

# Run the service
python main.py
```

## Usage Examples

### Create Organization

```python
import nats
import json

nc = await nats.connect("nats://localhost:4222")

request = {
    "name": "acme-corp",
    "display_name": "ACME Corporation",
    "description": "A sample organization",
    "owner_id": "user_12345",
    "email": "contact@acme.com"
}

response = await nc.request(
    "organization.create", 
    json.dumps(request).encode(),
    timeout=10
)

result = json.loads(response.data.decode())
print(f"Created organization: {result['data']['org_id']}")
```

### Get Organization

```python
request = {"org_id": "org_abc12345"}

response = await nc.request(
    "organization.get", 
    json.dumps(request).encode(),
    timeout=10
)

result = json.loads(response.data.decode())
organization = result['data']
```

### Update Settings

```python
request = {
    "org_id": "org_abc12345",
    "billing_cycle": "annual",
    "features": {
        "api_access": True,
        "advanced_analytics": True
    },
    "notifications": {
        "billing_alerts": True,
        "usage_alerts": False
    }
}

response = await nc.request(
    "organization.settings.update", 
    json.dumps(request).encode(),
    timeout=10
)
```

### Update Limits

```python
request = {
    "org_id": "org_abc12345",
    "max_users": 500,
    "max_storage_bytes": 50 * 1024 * 1024 * 1024,  # 50GB
    "api_calls_per_day": 50000
}

response = await nc.request(
    "organization.limits.update", 
    json.dumps(request).encode(),
    timeout=10
)
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install -r test_requirements.txt

# Run tests
python -m pytest tests/
```

### Database Indexes

The service automatically creates the following MongoDB indexes:

**Organizations Collection:**
- `org_id` (unique)
- `name`
- `display_name`
- `status`
- `created_at`
- `owner_id`

**Organization Settings Collection:**
- `org_id` (unique)

**Organization Limits Collection:**
- `org_id` (unique)

### Adding New Features

1. Update models in `app/models/organization.py`
2. Add business logic in `app/services/organization_service.py`
3. Add request handlers in `app/controllers/organization_controller.py`
4. Register new NATS topics in `app/main.py`
5. Update documentation

## API Response Format

All responses follow a consistent format:

### Success Response
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {...}
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z",
  "details": {...}
}
```

### Pagination Response
```json
{
  "status": "success",
  "message": "Retrieved 20 organizations",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "organizations": [...],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_count": 100,
      "limit": 20,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

## Monitoring and Health

The service provides health check endpoints that monitor:

- Database connectivity
- NATS connectivity
- Overall service status

Health check via NATS:
```python
response = await nc.request("organization.health", b"", timeout=5)
health_status = json.loads(response.data.decode())
```

## Security Considerations

- All organization names are automatically converted to lowercase
- Input validation using Pydantic models
- SQL injection prevention through MongoDB's document model
- Proper error handling without exposing internal details
- JWT secret key configuration for secure operations

## Deployment

### Docker Compose

```yaml
version: '3.8'
services:
  organization-service:
    build: .
    environment:
      - MONGO_URL=mongodb://mongo:27017
      - NATS_URL=nats://nats:4222
      - LOG_LEVEL=INFO
    depends_on:
      - mongo
      - nats
```

### Kubernetes

The service is designed to be stateless and can be deployed in Kubernetes with appropriate ConfigMaps and Secrets for configuration.

## Contributing

1. Follow the existing code structure and patterns
2. Add appropriate tests for new features
3. Update documentation
4. Follow Python PEP 8 style guidelines
5. Use type hints throughout the codebase

## License

Part of the CenterFuze platform - proprietary software.