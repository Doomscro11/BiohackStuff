#!/usr/bin/env python3
"""
Seed script to create mock reclaim pack exports for Partner Shares testing
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import uuid

# Load environment
load_dotenv(Path(__file__).parent.parent / '.env')

MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']


async def seed_mock_exports():
    """Create mock reclaim pack exports in the database"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🌱 Seeding mock export bundles...")
    
    # Clear existing exports first (optional - comment out if you want to keep existing data)
    # await db.reclaim_pack_exports.delete_many({})
    # print("   Cleared existing exports")
    
    # Mock Export 1: GLP-1 Patent Analysis
    export1 = {
        "export_id": str(uuid.uuid4()),
        "filename": "GLP1_Patent_Analysis.pdf",
        "format": "pdf",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "file_size_kb": 245,
        "item_count": 15,
        "filters": {
            "limit": 15,
            "country": "US",
            "status": None
        },
        "metadata": {
            "title": "GLP-1 Receptor Agonist Patents",
            "description": "Comprehensive analysis of expired and expiring GLP-1 related patents",
            "generated_by": "admin_seed_script",
            "tags": ["GLP-1", "diabetes", "patent_analysis"]
        },
        "file_path": "/tmp/mock_exports/GLP1_Patent_Analysis.pdf",  # Mock path
        "download_count": 0
    }
    
    # Mock Export 2: Peptide Synthesis Methods
    export2 = {
        "export_id": str(uuid.uuid4()),
        "filename": "Peptide_Synthesis_Methods.json",
        "format": "json",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "file_size_kb": 87,
        "item_count": 8,
        "filters": {
            "limit": 10,
            "country": "EP",
            "status": "Expired"
        },
        "metadata": {
            "title": "Peptide Synthesis Patent Portfolio",
            "description": "European patents on peptide synthesis methodologies - expired status",
            "generated_by": "admin_seed_script",
            "tags": ["synthesis", "methods", "peptide"]
        },
        "file_path": "/tmp/mock_exports/Peptide_Synthesis_Methods.json",  # Mock path
        "download_count": 0
    }
    
    # Mock Export 3: PK Enhancement Strategies
    export3 = {
        "export_id": str(uuid.uuid4()),
        "filename": "PK_Enhancement_Vault_Bundle.pdf",
        "format": "pdf",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "file_size_kb": 312,
        "item_count": 20,
        "filters": {
            "limit": 20,
            "country": None,
            "status": "ExpiringSoon"
        },
        "metadata": {
            "title": "Pharmacokinetic Enhancement Strategies",
            "description": "Patents on PK enhancement for therapeutic peptides - expiring soon",
            "generated_by": "admin_seed_script",
            "tags": ["pharmacokinetics", "half-life", "bioavailability"]
        },
        "file_path": "/tmp/mock_exports/PK_Enhancement_Vault_Bundle.pdf",  # Mock path
        "download_count": 0
    }
    
    # Mock Export 4: Lipidation Patents
    export4 = {
        "export_id": str(uuid.uuid4()),
        "filename": "Lipidation_Patent_Landscape.json",
        "format": "json",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "file_size_kb": 156,
        "item_count": 12,
        "filters": {
            "limit": 12,
            "country": "US",
            "status": "Lapsed"
        },
        "metadata": {
            "title": "Lipidation Technology Patents",
            "description": "US patent landscape for peptide lipidation technologies - lapsed",
            "generated_by": "admin_seed_script",
            "tags": ["lipidation", "conjugation", "modification"]
        },
        "file_path": "/tmp/mock_exports/Lipidation_Patent_Landscape.json",  # Mock path
        "download_count": 0
    }
    
    # Insert all mock exports
    exports = [export1, export2, export3, export4]
    
    result = await db.reclaim_pack_exports.insert_many(exports)
    
    print(f"✅ Successfully seeded {len(result.inserted_ids)} mock export bundles:")
    for exp in exports:
        print(f"   - {exp['filename']} ({exp['format'].upper()}, {exp['item_count']} items)")
    
    print("\n📋 Mock exports are now available at:")
    print("   GET /api/patentpulse/reclaim/exports")
    print("   These can be used in Partner Shares dropdown!")
    
    client.close()
    return exports


async def verify_exports():
    """Verify the seeded exports"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    count = await db.reclaim_pack_exports.count_documents({})
    print(f"\n🔍 Total exports in database: {count}")
    
    if count > 0:
        print("\n📦 Export files:")
        async for export in db.reclaim_pack_exports.find().sort("generated_at", -1):
            print(f"   • {export['filename']} - {export['item_count']} items ({export.get('file_size_kb', 0)} KB)")
    
    client.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🌱 Mock Export Bundles Seeder")
    print("=" * 60)
    
    asyncio.run(seed_mock_exports())
    asyncio.run(verify_exports())
    
    print("\n✅ Seeding complete!")
    print("=" * 60)
