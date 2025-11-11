# PatentPulse Collector - Weekly Patent Mining Job
# Run via cron: 0 3 * * 0 python -m jobs.patentpulse_collector
# (Every Sunday at 3 AM)

import os
import logging
import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Feature flag check
if os.getenv("FEATURE_PATENTPULSE", "false").lower() != "true":
    logger.warning("PatentPulse feature not enabled, skipping collection")
    exit(0)

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'peptimancer_db')]

# Collections
patentpulse_items = db['patentpulse_items']

# Mock patent sources (in production, would integrate with USPTO, WIPO, Lens.org APIs)
PATENT_SOURCES = ["USPTO", "WIPO", "EPO", "Lens.org"]
COUNTRIES = ["US", "EP", "WO", "JP", "CN"]
STATUSES = ["Expired", "Lapsed", "Expiring"]
ASSIGNEES = [
    "Novo Nordisk", "Eli Lilly", "Amgen", "Genentech", 
    "Merck", "Pfizer", "Sanofi", "Takeda", "AstraZeneca",
    "Bayer", "Bristol-Myers Squibb", "Roche"
]

KEYWORDS = [
    "peptide", "GLP-1", "agonist", "analog", "sequence",
    "formulation", "delivery", "conjugate", "synthesis",
    "therapeutic", "bioactive", "stability"
]

async def collect_patents():
    """
    Collect and analyze patents from various sources
    In production, this would call real patent APIs
    For MVP, generates realistic mock data
    """
    logger.info("Starting PatentPulse collector...")
    
    collected_count = 0
    updated_count = 0
    
    # Simulate collecting 5-15 new patents per run
    num_patents = random.randint(5, 15)
    
    for i in range(num_patents):
        # Generate realistic patent data
        patent_id = f"{random.choice(COUNTRIES)}{random.randint(1000000, 9999999)}"
        
        # Check if patent already exists
        existing = await patentpulse_items.find_one({"patent_id": patent_id})
        
        if existing:
            # Update existing patent
            await patentpulse_items.update_one(
                {"patent_id": patent_id},
                {"$set": {"updated_at": datetime.utcnow()}}
            )
            updated_count += 1
            continue
        
        # Generate expiry date (some expired, some expiring soon)
        if random.random() < 0.6:  # 60% already expired
            days_ago = random.randint(1, 1095)  # Up to 3 years ago
            expiry_date = datetime.utcnow() - timedelta(days=days_ago)
            status = random.choice(["Expired", "Lapsed"])
        else:  # 40% expiring within 24 months
            days_until = random.randint(1, 730)  # Up to 24 months
            expiry_date = datetime.utcnow() + timedelta(days=days_until)
            status = "Expiring"
        
        # Generate peptide sequence (if applicable)
        has_sequence = random.random() < 0.7  # 70% have sequences
        sequence_data = None
        if has_sequence:
            # Mock peptide sequence (15-35 amino acids)
            amino_acids = "ACDEFGHIKLMNPQRSTVWY"
            seq_length = random.randint(15, 35)
            sequence_data = ''.join(random.choice(amino_acids) for _ in range(seq_length))
        
        # Generate scores
        commercial_score = round(random.uniform(0.3, 0.95), 3)
        synthesis_score = round(random.uniform(0.2, 0.8), 3)
        fto_risk = round(random.uniform(0.1, 0.6), 3)
        
        # Generate repurpose notes
        notes_templates = [
            "Potential for metabolic disease treatment repurposing",
            "Novel delivery formulation could reduce synthesis complexity",
            "Sequence modifications may improve half-life without IP conflicts",
            "Strong commercial potential in obesity therapeutics market",
            "Low FTO risk makes this attractive for immediate development",
            "Synthesis route simplification possible with modern methods"
        ]
        repurpose_notes = random.choice(notes_templates)
        
        # Select random keywords
        patent_keywords = random.sample(KEYWORDS, k=random.randint(3, 6))
        
        # Create patent document
        patent_doc = {
            "title": f"Peptide therapeutic composition for {random.choice(['diabetes', 'obesity', 'cancer', 'cardiovascular'])} treatment",
            "patent_id": patent_id,
            "assignee": random.choice(ASSIGNEES),
            "country": random.choice(COUNTRIES),
            "expiry_date": expiry_date,
            "status": status,
            "keywords": patent_keywords,
            "sequence_data": sequence_data,
            "commercial_score": commercial_score,
            "synthesis_score": synthesis_score,
            "fto_risk": fto_risk,
            "repurpose_notes": repurpose_notes,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "source": random.choice(PATENT_SOURCES)
        }
        
        # Insert patent
        await patentpulse_items.insert_one(patent_doc)
        collected_count += 1
        
        logger.info(f"Collected patent {i+1}/{num_patents}: {patent_id} ({status})")
    
    logger.info(f"Collection complete!")
    logger.info(f"  - New patents collected: {collected_count}")
    logger.info(f"  - Existing patents updated: {updated_count}")
    
    # Get top 5 opportunities for summary
    pipeline = [
        {"$match": {"status": {"$in": ["Expired", "Lapsed", "Expiring"]}}},
        {"$addFields": {
            "viability_score": {
                "$multiply": [
                    "$commercial_score",
                    {"$subtract": [1, "$synthesis_score"]},
                    {"$subtract": [1, "$fto_risk"]}
                ]
            }
        }},
        {"$sort": {"viability_score": -1}},
        {"$limit": 5}
    ]
    
    top_opportunities = await patentpulse_items.aggregate(pipeline).to_list(5)
    
    logger.info("\nTop 5 Opportunities:")
    for idx, opp in enumerate(top_opportunities, 1):
        viability = round(opp["viability_score"], 4)
        logger.info(f"  {idx}. {opp['patent_id']} - Viability: {viability} - {opp['assignee']}")
    
    return {
        "collected": collected_count,
        "updated": updated_count,
        "top_opportunities": top_opportunities
    }

async def main():
    """Main entry point"""
    logger.info("PatentPulse Collector v1.0")
    await collect_patents()
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
