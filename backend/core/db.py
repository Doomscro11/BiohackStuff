"""
Database connection management for MongoDB.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from functools import lru_cache


@lru_cache()
def get_db_client() -> AsyncIOMotorClient:
    """Get cached MongoDB client."""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    return AsyncIOMotorClient(mongo_url)


def get_database(db_name: str = None) -> AsyncIOMotorDatabase:
    """Get database instance."""
    if db_name is None:
        db_name = os.environ.get('DB_NAME', 'peptimancer_db')
    client = get_db_client()
    return client[db_name]
