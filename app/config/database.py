"""
Database configuration and management
"""

import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages MongoDB connections"""
    
    def __init__(self, settings):
        self.settings = settings
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        
    def connect(self) -> None:
        """Connect to MongoDB"""
        try:
            logger.info(f"Connecting to MongoDB at {self.settings.mongo_url}")
            
            self.client = MongoClient(
                self.settings.mongo_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database
            self.database = self.client[self.settings.mongo_db_name]
            
            # Create indexes
            self._create_indexes()
            
            logger.info(f"Connected to MongoDB database: {self.settings.mongo_db_name}")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise
            
    def disconnect(self) -> None:
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
            
    def get_database(self) -> Database:
        """Get the database instance"""
        if not self.database:
            raise RuntimeError("Database not connected")
        return self.database
        
    def health_check(self) -> bool:
        """Check if database is healthy"""
        try:
            if self.client:
                self.client.admin.command('ping')
                return True
        except:
            pass
        return False
        
    def _create_indexes(self):
        """Create database indexes"""
        try:
            # Organizations indexes
            self.database.organizations.create_index("org_id", unique=True)
            self.database.organizations.create_index("name")
            self.database.organizations.create_index("display_name")
            self.database.organizations.create_index("status")
            self.database.organizations.create_index("created_at")
            self.database.organizations.create_index("owner_id")
            
            # Organization settings indexes
            self.database.organization_settings.create_index("org_id", unique=True)
            
            # Organization limits indexes
            self.database.organization_limits.create_index("org_id", unique=True)
            
            # Audit log indexes
            self.database.audit_logs.create_index("timestamp")
            self.database.audit_logs.create_index("org_id")
            self.database.audit_logs.create_index("action")
            self.database.audit_logs.create_index([("timestamp", -1)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            # Don't fail startup if indexes can't be created