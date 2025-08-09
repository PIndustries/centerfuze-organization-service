#!/usr/bin/env python
"""
Test Organization Service Module Integration
Tests the module management functionality in the organization service
"""

import asyncio
import json
import logging
import os
from datetime import datetime
import nats
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_org_service_modules():
    """Test organization service module integration"""
    
    # NATS connection parameters
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    nats_user = os.getenv("NATS_USER")
    nats_password = os.getenv("NATS_PASSWORD")
    
    # Connect to NATS
    logger.info(f"Connecting to NATS at {nats_url}")
    
    connect_opts = {
        "servers": [nats_url],
        "name": "org-service-module-test",
    }
    
    if nats_user and nats_password:
        connect_opts["user"] = nats_user
        connect_opts["password"] = nats_password
    
    nc = await nats.connect(**connect_opts)
    logger.info("Connected to NATS successfully")
    
    # Test organization ID
    test_org_id = "org_05dbfa9ff64348d8"
    
    # Test 1: Get modules for organization
    logger.info("\n=== Test 1: Get modules for organization ===")
    
    request_data = {
        "org_id": test_org_id
    }
    
    try:
        response = await nc.request(
            "module.get",
            json.dumps(request_data).encode(),
            timeout=5.0
        )
        result = json.loads(response.data.decode())
        logger.info(f"Get modules response: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            logger.info(f"Organization: {result['data']['organization']['name']}")
            logger.info(f"Available modules: {len(result['data']['modules'])}")
            logger.info(f"Enabled modules: {result['data']['enabled_modules']}")
    except asyncio.TimeoutError:
        logger.error("Request timed out")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    await asyncio.sleep(1)
    
    # Test 2: Toggle a module
    logger.info("\n=== Test 2: Toggle module ===")
    
    toggle_data = {
        "org_id": test_org_id,
        "module_key": "reports",
        "enabled": True,
        "updated_by": "test_script"
    }
    
    try:
        response = await nc.request(
            "module.toggle",
            json.dumps(toggle_data).encode(),
            timeout=5.0
        )
        result = json.loads(response.data.decode())
        logger.info(f"Toggle module response: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            logger.info(f"Module {result['data']['module_key']} {result['data']['action']} successfully")
    except asyncio.TimeoutError:
        logger.error("Request timed out")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    await asyncio.sleep(1)
    
    # Test 3: Bulk update modules
    logger.info("\n=== Test 3: Bulk update modules ===")
    
    bulk_data = {
        "org_id": test_org_id,
        "enabled_modules": [
            "dashboard", "clients", "invoices", "reports", 
            "subscriptions", "payment_methods", "fuze_ai"
        ],
        "updated_by": "test_script"
    }
    
    try:
        response = await nc.request(
            "module.bulk_update",
            json.dumps(bulk_data).encode(),
            timeout=5.0
        )
        result = json.loads(response.data.decode())
        logger.info(f"Bulk update response: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            logger.info(f"Modules added: {result['data']['modules_added']}")
            logger.info(f"Modules removed: {result['data']['modules_removed']}")
    except asyncio.TimeoutError:
        logger.error("Request timed out")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    await asyncio.sleep(1)
    
    # Test 4: Get module status
    logger.info("\n=== Test 4: Get module status ===")
    
    status_data = {
        "org_id": test_org_id
    }
    
    try:
        response = await nc.request(
            "module.status",
            json.dumps(status_data).encode(),
            timeout=5.0
        )
        result = json.loads(response.data.decode())
        logger.info(f"Module status response: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            usage = result['data'].get('usage_summary', {})
            logger.info(f"Usage summary: {usage}")
    except asyncio.TimeoutError:
        logger.error("Request timed out")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    await asyncio.sleep(1)
    
    # Test 5: Get available modules
    logger.info("\n=== Test 5: Get available modules ===")
    
    try:
        response = await nc.request(
            "module.available",
            json.dumps({}).encode(),
            timeout=5.0
        )
        result = json.loads(response.data.decode())
        logger.info(f"Available modules response: {json.dumps(result, indent=2)}")
        
        if result.get("success"):
            modules = result['data']['modules']
            logger.info(f"Total available modules: {len(modules)}")
            for module in modules[:3]:  # Show first 3
                logger.info(f"  - {module['key']}: {module['name']}")
    except asyncio.TimeoutError:
        logger.error("Request timed out")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    await asyncio.sleep(1)
    
    # Test 6: Get module usage statistics
    logger.info("\n=== Test 6: Get module usage statistics ===")
    
    usage_data = {
        "org_id": test_org_id,
        "module_key": "invoices"
    }
    
    try:
        response = await nc.request(
            "module.usage.stats",
            json.dumps(usage_data).encode(),
            timeout=5.0
        )
        result = json.loads(response.data.decode())
        logger.info(f"Module usage response: {json.dumps(result, indent=2)}")
    except asyncio.TimeoutError:
        logger.error("Request timed out")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    await asyncio.sleep(1)
    
    # Test 7: Listen for module events
    logger.info("\n=== Test 7: Setting up event listener ===")
    
    events_received = []
    
    async def event_handler(msg):
        subject = msg.subject
        data = json.loads(msg.data.decode())
        logger.info(f"Received event on {subject}")
        logger.info(f"Event data: {json.dumps(data, indent=2)}")
        events_received.append((subject, data))
    
    # Subscribe to organization module events
    sub = await nc.subscribe("centerfuze.organization.module.>", cb=event_handler)
    logger.info("Subscribed to centerfuze.organization.module.* events")
    
    # Trigger an event by toggling a module
    logger.info("\n=== Triggering module event ===")
    
    toggle_data = {
        "org_id": test_org_id,
        "module_key": "billing_admin",
        "enabled": False,
        "updated_by": "test_script"
    }
    
    try:
        response = await nc.request(
            "module.toggle",
            json.dumps(toggle_data).encode(),
            timeout=5.0
        )
        result = json.loads(response.data.decode())
        logger.info(f"Toggle triggered: {result.get('success')}")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    # Wait for events
    await asyncio.sleep(2)
    
    logger.info(f"\nTotal events received: {len(events_received)}")
    for subject, data in events_received:
        logger.info(f"  - {subject}: org={data.get('org_id')}, module={data.get('module_key')}")
    
    # Clean up
    await sub.unsubscribe()
    await nc.close()
    logger.info("\n=== Test completed, connection closed ===")


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_org_service_modules())