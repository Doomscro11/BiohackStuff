# PatentPulse Seed Script - Development Only
# Populates sample patent data for dashboard testing
# Usage: ENV=dev python -m jobs.seed_patentpulse_dev

import os
import logging
import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Safety check
ENV = os.getenv("ENV", "production")
ALLOW_SEED = os.getenv("ALLOW_SEED", "false").lower() == "true"

if ENV == "production" and not ALLOW_SEED:
    logger.error("Seed script disabled in production without ALLOW_SEED=true")
    exit(1)

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'peptimancer_db')]

# Collections
patentpulse_items = db['patentpulse_items']

COUNTRIES = ["US", "EP", "WO", "JP", "CN"]
STATUSES = ["Expired", "Lapsed", "Expiring"]
ASSIGNEES = [
    "Novo Nordisk A/S", "Eli Lilly and Company", "Amgen Inc.", 
    "Genentech, Inc.", "Merck & Co.", "Pfizer Inc.", 
    "Sanofi SA", "Takeda Pharmaceutical", "AstraZeneca PLC",
    "Bayer AG", "Bristol-Myers Squibb", "F. Hoffmann-La Roche AG",
    "GlaxoSmithKline", "Johnson & Johnson", "Novartis AG"
]

KEYWORDS = [
    "peptide", "GLP-1", "agonist", "analog", "sequence",
    "formulation", "delivery", "conjugate", "synthesis",
    "therapeutic", "bioactive", "stability", "PEGylation",
    "lipidation", "half-life", "metabolic", "diabetes"
]

TITLES = [
    "Peptide therapeutic composition for diabetes treatment",
    "GLP-1 receptor agonist with extended half-life",
    "Novel peptide formulation for obesity management",
    "Lipidated peptide analog with improved stability",
    "PEGylated peptide therapeutic for metabolic disorders",
    "Peptide conjugate for enhanced bioavailability",
    "Modified GLP-1 analog with reduced immunogenicity",
    "Peptide drug delivery system using novel excipients",
    "Stable peptide formulation for subcutaneous administration",
    "Peptide therapeutic with improved pharmacokinetics"
]

NOTES = [
    "High commercial potential in obesity therapeutics market. Sequence modifications could bypass existing IP.",
    "Low synthesis complexity with modern solid-phase methods. Strong FTO position for immediate development.",
    "Novel delivery formulation approach. Patent expired, formulatio methods now standard in industry.",
    "Strong commercial interest in GLP-1 space. Synthesis route simplification possible with current technology.",
    "Expired patent with clear revival pathway. Market size $5B+ annually with growing demand.",
    "Low FTO risk, moderate synthesis complexity. Ideal candidate for generic development.",
    "Patent lapsed due to non-payment. Core innovation still valuable for metabolic disease treatment.",
    "Expiring within 18 months. Early development could position for immediate commercialization post-expiry.",
    "Strong sequence data available. Modern peptide synthesis makes this economically viable now.",
    "Novel conjugation strategy no longer protected. Compatible with current manufacturing capabilities."
]

async def seed_patents():
    """Seed 30-50 realistic patent items"""
    logger.info("Starting PatentPulse seed...")
    
    # Clear existing data (optional)
    logger.info("Clearing existing patent data...")
    await patentpulse_items.delete_many({})
    
    # Generate 30-50 patents
    num_patents = random.randint(30, 50)
    logger.info(f"Generating {num_patents} patent items...")
    
    for i in range(num_patents):
        # Generate unique patent ID
        patent_id = f"{random.choice(COUNTRIES)}{random.randint(5000000, 9999999)}"
        
        # Determine status and expiry date
        status_roll = random.random()
        if status_roll < 0.50:  # 50% Expired
            status = "Expired"
            days_ago = random.randint(30, 1095)  # 1 month to 3 years ago
            expiry_date = datetime.utcnow() - timedelta(days=days_ago)
        elif status_roll < 0.75:  # 25% Lapsed
            status = "Lapsed"
            days_ago = random.randint(180, 730)  # 6 months to 2 years ago
            expiry_date = datetime.utcnow() - timedelta(days=days_ago)
        else:  # 25% Expiring soon
            status = "Expiring"
            days_until = random.randint(30, 730)  # 1 month to 24 months
            expiry_date = datetime.utcnow() + timedelta(days=days_until)
        
        # Generate peptide sequence (70% have sequences)
        has_sequence = random.random() < 0.7
        sequence_data = None
        if has_sequence:
            amino_acids = "ACDEFGHIKLMNPQRSTVWY"
            seq_length = random.randint(18, 35)
            sequence_data = ''.join(random.choice(amino_acids) for _ in range(seq_length))
        
        # Generate realistic scores with some correlation
        # Higher commercial score → more willing to tolerate higher synthesis complexity
        commercial_base = random.uniform(0.35, 0.95)
        commercial_score = round(commercial_base, 3)
        
        # Synthesis score: lower is easier (inverse relationship with commercial sometimes)
        synthesis_score = round(random.uniform(0.15, 0.75), 3)
        
        # FTO risk: independent, but lower is better
        fto_risk = round(random.uniform(0.05, 0.55), 3)
        
        # Select random title and notes
        title = random.choice(TITLES)
        repurpose_notes = random.choice(NOTES)
        
        # Select 3-7 keywords
        patent_keywords = random.sample(KEYWORDS, k=random.randint(3, 7))
        
        # Create patent document
        patent_doc = {
            "title": title,
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
            "source": random.choice(["USPTO", "WIPO", "EPO", "Lens.org"])
        }
        
        await patentpulse_items.insert_one(patent_doc)
    
    total = await patentpulse_items.count_documents({})
    logger.info(f"Seed complete! Total patents: {total}")
    
    # Show breakdown by status
    for status_val in STATUSES:
        count = await patentpulse_items.count_documents({"status": status_val})
        logger.info(f"  - {status_val}: {count}")
    
    # Show top 5 opportunities
    pipeline = [
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
    
    top_opps = await patentpulse_items.aggregate(pipeline).to_list(5)
    
    logger.info("\nTop 5 Opportunities (by viability score):")
    for idx, opp in enumerate(top_opps, 1):
        viability = round(opp["viability_score"], 4)
        logger.info(f"  {idx}. {opp['patent_id']} - {viability} - {opp['assignee']}")

async def main():
    """Main entry point"""
    logger.info(f"Environment: {ENV}")
    logger.info(f"Allow seed: {ALLOW_SEED}")
    
    if ENV == "production":
        logger.warning("Running seed in PRODUCTION mode!")
        confirm = input("Type 'YES' to confirm: ")
        if confirm != "YES":
            logger.info("Aborted")
            return
    
    await seed_patents()
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
