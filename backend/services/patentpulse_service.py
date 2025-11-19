"""
PatentPulse Service
Handles patent data queries and operations
"""

import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'peptimancer_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]


async def get_patent_items(
    status: Optional[str] = None,
    country: Optional[str] = None,
    limit: int = 100,
    skip: int = 0
) -> List[Dict[str, Any]]:
    """
    Get patent items with optional filters
    """
    query = {}
    
    if status:
        query['status'] = status
    
    if country:
        query['country'] = country
    
    cursor = db.patentpulse_items.find(query, {'_id': 0}).skip(skip).limit(limit).sort('priority_date', -1)
    items = await cursor.to_list(length=limit)
    
    logger.info(f"Retrieved {len(items)} patent items")
    
    return items


async def get_patent_by_id(patent_id: str) -> Optional[Dict[str, Any]]:
    """Get patent by ID"""
    patent = await db.patentpulse_items.find_one({'patent_id': patent_id}, {'_id': 0})
    return patent


async def get_patent_stats() -> Dict[str, Any]:
    """
    Get patent statistics
    
    Returns:
        Dict with total, by_status, by_country counts
    """
    pipeline = [
        {
            '$facet': {
                'total': [{'$count': 'count'}],
                'by_status': [
                    {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
                ],
                'by_country': [
                    {'$group': {'_id': '$country', 'count': {'$sum': 1}}},
                    {'$sort': {'count': -1}},
                    {'$limit': 10}
                ]
            }
        }
    ]
    
    result = await db.patentpulse_items.aggregate(pipeline).to_list(length=1)
    
    if not result:
        return {
            'total': 0,
            'by_status': {},
            'by_country': {}
        }
    
    data = result[0]
    
    total = data['total'][0]['count'] if data['total'] else 0
    
    by_status = {item['_id']: item['count'] for item in data['by_status']}
    by_country = {item['_id']: item['count'] for item in data['by_country']}
    
    return {
        'total': total,
        'by_status': by_status,
        'by_country': by_country
    }


async def get_top_opportunities(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get top patent opportunities sorted by viability score
    """
    cursor = db.patentpulse_items.find(
        {'viability_score': {'$exists': True}},
        {'_id': 0}
    ).sort('viability_score', -1).limit(limit)
    
    opportunities = await cursor.to_list(length=limit)
    
    logger.info(f"Retrieved {len(opportunities)} top opportunities")
    
    return opportunities


async def update_patent_status(patent_id: str, status: str) -> bool:
    """
    Update patent status
    
    Returns:
        True if updated, False if not found
    """
    result = await db.patentpulse_items.update_one(
        {'patent_id': patent_id},
        {
            '$set': {
                'status': status,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.modified_count > 0:
        logger.info(f"Updated patent {patent_id} status to {status}")
        return True
    
    return False


async def search_patents(
    query_text: str,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Search patents by text
    
    Note: Requires text index on title and abstract fields
    """
    cursor = db.patentpulse_items.find(
        {'$text': {'$search': query_text}},
        {'_id': 0, 'score': {'$meta': 'textScore'}}
    ).sort([('score', {'$meta': 'textScore'})]).limit(limit)
    
    results = await cursor.to_list(length=limit)
    
    logger.info(f"Found {len(results)} patents matching '{query_text}'")
    
    return results
