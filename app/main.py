"""
Main application entry point for CenterFuze Organization Service
"""

import asyncio
import signal
import logging
from typing import Optional

import nats
from nats.errors import ConnectionClosedError, TimeoutError

from .config import get_settings
from .config.database import DatabaseManager
from .controllers import OrganizationController, HealthController
from .controllers.module_controller import ModuleController
from .services import OrganizationService, EventPublisher
from .services.module_service import ModuleService
from .utils.logging import setup_logging

logger = logging.getLogger(__name__)


class OrganizationServiceApp:
    """Main application class"""
    
    def __init__(self):
        self.settings = get_settings()
        self.nc: Optional[nats.Client] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.running = True
        self.tasks = []
        
        # Setup logging
        setup_logging(
            level=self.settings.log_level,
            service_name=self.settings.service_name
        )
        
    async def start(self):
        """Start the service"""
        logger.info(f"Starting {self.settings.service_name} v{self.settings.service_version}")
        
        try:
            # Connect to NATS
            await self._connect_nats()
            
            # Connect to MongoDB
            self._connect_database()
            
            # Initialize services
            event_publisher = EventPublisher(self.nc, self.settings.service_name)
            
            organization_service = OrganizationService(
                self.db_manager.get_database(),
                event_publisher
            )
            
            module_service = ModuleService(
                self.db_manager.get_database(),
                event_publisher
            )
            
            # Initialize controllers
            organization_controller = OrganizationController(organization_service)
            module_controller = ModuleController(module_service)
            health_controller = HealthController(self.db_manager, self.nc)
            
            # Register NATS handlers with proper topic names
            subscriptions = []
            
            # Organization topics
            subscriptions.extend(await self._register_organization_handlers(organization_controller))
            
            # Module topics
            subscriptions.extend(await self._register_module_handlers(module_controller))
            
            # Health topics
            subscriptions.extend(await health_controller.register_handlers(self.nc))
            
            logger.info(f"{self.settings.service_name} started successfully")
            logger.info(f"Subscribed to {len(subscriptions)} NATS topics")
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Service failed to start: {e}", exc_info=True)
            raise
        finally:
            await self.stop()
            
    async def _register_organization_handlers(self, controller: OrganizationController):
        """Register organization handlers with proper topic names"""
        nc = self.nc
        return [
            # Basic CRUD operations
            await nc.subscribe("organization.create", cb=controller.handle_create),
            await nc.subscribe("organization.get", cb=controller.handle_get),
            await nc.subscribe("organization.update", cb=controller.handle_update),
            await nc.subscribe("organization.delete", cb=controller.handle_delete),
            await nc.subscribe("organization.list", cb=controller.handle_list),
            await nc.subscribe("organization.search", cb=controller.handle_search),
            
            # Settings operations
            await nc.subscribe("organization.settings.get", cb=controller.handle_get_settings),
            await nc.subscribe("organization.settings.update", cb=controller.handle_update_settings),
            
            # Limits operations
            await nc.subscribe("organization.limits.get", cb=controller.handle_get_limits),
            await nc.subscribe("organization.limits.update", cb=controller.handle_update_limits)
        ]
    
    async def _register_module_handlers(self, controller: ModuleController):
        """Register module handlers"""
        nc = self.nc
        return [
            # Module management operations
            await nc.subscribe("module.get", cb=controller.handle_get_modules),
            await nc.subscribe("module.toggle", cb=controller.handle_toggle_module),
            await nc.subscribe("module.bulk_update", cb=controller.handle_bulk_update_modules),
            await nc.subscribe("module.status", cb=controller.handle_get_module_status),
            await nc.subscribe("module.available", cb=controller.handle_get_available_modules),
            await nc.subscribe("module.usage.stats", cb=controller.handle_module_usage_stats),
            
            # Listen for module events from admin service
            await nc.subscribe("centerfuze.admin.module.>", cb=controller.handle_module_event)
        ]
            
    async def stop(self):
        """Stop the service gracefully"""
        logger.info("Shutting down service...")
        self.running = False
        
        # Cancel background tasks
        for task in self.tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
                
        # Disconnect from NATS
        if self.nc and not self.nc.is_closed:
            await self.nc.close()
            logger.info("Disconnected from NATS")
            
        # Disconnect from MongoDB
        if self.db_manager:
            self.db_manager.disconnect()
            
        logger.info("Service stopped")
        
    async def _connect_nats(self):
        """Connect to NATS server"""
        logger.info(f"Attempting to connect to NATS servers: {self.settings.nats_servers}")
        
        connect_opts = {
            "name": self.settings.service_name,
            "reconnect_time_wait": 2,
            "max_reconnect_attempts": -1,
            "error_cb": self._nats_error_cb,
            "disconnected_cb": self._nats_disconnected_cb,
            "reconnected_cb": self._nats_reconnected_cb,
        }
        
        if self.settings.nats_user and self.settings.nats_password:
            connect_opts["user"] = self.settings.nats_user
            connect_opts["password"] = self.settings.nats_password
            logger.info(f"Connecting with user: {self.settings.nats_user}")
        else:
            logger.warning("No NATS credentials provided, attempting anonymous connection")
            
        # Pass servers as first argument, not in options
        self.nc = await nats.connect(
            servers=self.settings.nats_servers,
            **connect_opts
        )
        logger.info(f"Connected to NATS at {self.settings.nats_servers}")
        
    def _connect_database(self):
        """Connect to MongoDB"""
        self.db_manager = DatabaseManager(self.settings)
        self.db_manager.connect()
        
    async def _nats_error_cb(self, e):
        """NATS error callback"""
        logger.error(f"NATS error: {e}")
        
    async def _nats_disconnected_cb(self):
        """NATS disconnected callback"""
        logger.warning("Disconnected from NATS")
        
    async def _nats_reconnected_cb(self):
        """NATS reconnected callback"""
        logger.info("Reconnected to NATS")


def main():
    """Main entry point"""
    app = OrganizationServiceApp()
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        app.running = False
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the service
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Service crashed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()