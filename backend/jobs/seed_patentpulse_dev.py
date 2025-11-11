# PatentPulse Seed Script - Development Only (ENHANCED)
# Populates realistic expired peptide & biotech patents for testing
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

# Synthetic company names for realistic seeding
ASSIGNEES = [
    "BioNova Labs",
    "Genex Therapeutics",
    "NeoPeptidics Inc.",
    "Synaptica Biotech",
    "Dermacore Research",
    "PeptaTech Industries",
    "VitalBio Corporation",
    "ChromaPeptide Systems",
    "NutraGen Sciences",
    "BioSequence Innovations"
]

COUNTRIES = ["US", "CA", "JP", "EP", "WO"]

# Keyword pool for realistic patent classification
KEYWORDS_POOL = [
    "peptide", "analog", "agonist", "formulation", "delivery",
    "GLP-1", "HGH", "antimicrobial", "cosmetic", "bioactive",
    "nutraceutical", "therapeutic", "stability", "carrier",
    "nanoparticle", "transdermal", "oral", "topical"
]

# Amino acids for sequence generation
AMINO_ACIDS = {
    "Ala": "A", "Arg": "R", "Asn": "N", "Asp": "D", "Cys": "C",
    "Gln": "Q", "Glu": "E", "Gly": "G", "His": "H", "Ile": "I",
    "Leu": "L", "Lys": "K", "Met": "M", "Phe": "F", "Pro": "P",
    "Ser": "S", "Thr": "T", "Trp": "W", "Tyr": "Y", "Val": "V"
}

# Realistic patent titles with variations
TITLE_TEMPLATES = [
    "Stabilized {target} Peptide Analogue for {application}",
    "{modification} Peptide Derivative of {base} for {application}",
    "{delivery} Delivery Carrier Peptide for {target}",
    "Peptide-Based {formulation} for {application}",
    "{feature} Peptide Composition for {therapeutic_area}",
    "Novel {target} Receptor Agonist with {benefit}",
    "Peptide-Coated {carrier} for {delivery} Delivery",
    "{modification} Peptide Sequence with Enhanced {property}"
]

TARGET_OPTIONS = ["GLP-1", "Growth Hormone", "Insulin", "Ghrelin", "Oxytocin"]
APPLICATION_OPTIONS = [
    "Metabolic Regulation", "Skin Care Applications", "Weight Management",
    "Wound Healing", "Anti-Aging Therapy", "Muscle Recovery"
]
MODIFICATION_OPTIONS = ["Antimicrobial", "Lipidated", "PEGylated", "Cyclized", "D-Amino"]
DELIVERY_OPTIONS = ["Oral", "Transdermal", "Nasal", "Subcutaneous"]
FORMULATION_OPTIONS = ["Chelation Complex", "Emulsion System", "Hydrogel Matrix"]
CARRIER_OPTIONS = ["Nanoparticles", "Liposomes", "Micelles"]
BENEFIT_OPTIONS = ["Extended Half-Life", "Improved Stability", "Enhanced Bioavailability"]
PROPERTY_OPTIONS = ["Solubility", "Permeability", "Protease Resistance"]
THERAPEUTIC_OPTIONS = ["Diabetes Management", "Cardiovascular Health", "Oncology Support"]

# Repurpose notes templates
REPURPOSE_NOTES = [
    "Potential for nutraceutical {application} products.",
    "Candidate for topical {condition} and {condition} formulations.",
    "Useful as oral carrier for short peptides in functional foods.",
    "Repurpose for {application} supplement absorption boosters.",
    "Potential new carrier for peptide-based {application} serums.",
    "Strong commercial interest in {market} market with low entry barriers.",
    "Modern synthesis methods reduce complexity, making commercialization viable.",
    "Clear pathway for generic development post-expiry with minimal FTO risk.",
    "Sequence modifications could bypass existing IP for novel {application}.",
    "Expired formulation patents allow immediate development for {market} products."
]

def generate_sequence(length):
    """Generate realistic amino acid sequence in 3-letter format"""
    aa_list = list(AMINO_ACIDS.keys())
    sequence = '-'.join(random.sample(aa_list * 3, k=length))
    return sequence

def generate_title():
    """Generate realistic patent title"""
    template = random.choice(TITLE_TEMPLATES)
    return template.format(
        target=random.choice(TARGET_OPTIONS),
        application=random.choice(APPLICATION_OPTIONS),
        modification=random.choice(MODIFICATION_OPTIONS),
        base=random.choice(["LL-37", "Insulin", "GLP-1", "Ghrelin", "HGH"]),
        delivery=random.choice(DELIVERY_OPTIONS),
        formulation=random.choice(FORMULATION_OPTIONS),
        carrier=random.choice(CARRIER_OPTIONS),
        benefit=random.choice(BENEFIT_OPTIONS),
        property=random.choice(PROPERTY_OPTIONS),
        therapeutic_area=random.choice(THERAPEUTIC_OPTIONS),
        feature=random.choice(["Novel", "Enhanced", "Optimized", "Modified"])
    )

def generate_repurpose_note():
    """Generate repurpose notes"""
    template = random.choice(REPURPOSE_NOTES)
    return template.format(
        application=random.choice(["weight-management", "skin-repair", "mineral absorption", "anti-aging"]),
        condition=random.choice(["acne", "wound-healing", "wrinkle reduction", "scar treatment"]),
        market=random.choice(["cosmetics", "nutraceuticals", "therapeutics", "functional foods"])
    )

async def seed_patents():
    """Seed 20-30 realistic patent items"""
    logger.info("Starting PatentPulse Enhanced Seeding...")
    
    # Clear existing data
    logger.info("Clearing existing patent data...")
    await patentpulse_items.delete_many({})
    
    # Generate 20-30 patents
    num_patents = random.randint(20, 30)
    logger.info(f"Generating {num_patents} realistic patent items...")
    
    inserted_records = []
    
    for i in range(num_patents):
        # Generate unique patent ID
        country = random.choice(COUNTRIES)
        patent_id = f"{country}{random.randint(5000000, 9999999)}"
        
        # All patents are expired (2022-01-01 to 2024-12-31)
        start_date = datetime(2022, 1, 1)
        end_date = datetime(2024, 12, 31)
        days_diff = (end_date - start_date).days
        expiry_date = start_date + timedelta(days=random.randint(0, days_diff))
        
        # Generate peptide sequence (8-25 amino acids in 3-letter format)
        seq_length = random.randint(8, 25)
        sequence_data = generate_sequence(seq_length)
        
        # Generate realistic scores
        commercial_score = round(random.uniform(0.4, 0.9), 2)
        synthesis_score = round(random.uniform(0.2, 0.8), 2)
        fto_risk = round(random.uniform(0.1, 0.6), 2)
        
        # Generate title and notes
        title = generate_title()
        repurpose_notes = generate_repurpose_note()
        
        # Select 3-5 keywords
        patent_keywords = random.sample(KEYWORDS_POOL, k=random.randint(3, 5))
        
        # Create patent document
        patent_doc = {
            "title": title,
            "patent_id": patent_id,
            "assignee": random.choice(ASSIGNEES),
            "country": country,
            "expiry_date": expiry_date,
            "status": "Expired",
            "keywords": patent_keywords,
            "sequence_data": sequence_data,
            "commercial_score": commercial_score,
            "synthesis_score": synthesis_score,
            "fto_risk": fto_risk,
            "repurpose_notes": repurpose_notes,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "source": random.choice(["USPTO", "CIPO", "JPO", "EPO", "WIPO"])
        }
        
        await patentpulse_items.insert_one(patent_doc)
        
        # Store first 3 for preview
        if i < 3:
            preview_doc = patent_doc.copy()
            preview_doc["expiry_date"] = preview_doc["expiry_date"].isoformat()
            preview_doc["created_at"] = preview_doc["created_at"].isoformat()
            preview_doc["updated_at"] = preview_doc["updated_at"].isoformat()
            preview_doc.pop("_id", None)
            inserted_records.append(preview_doc)
    
    total = await patentpulse_items.count_documents({})
    logger.info(f"✅ Seed complete! Total patents: {total}")
    
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
    
    logger.info("\n" + "="*60)
    logger.info("PATENTPULSE DEV SEEDING COMPLETE")
    logger.info("="*60)
    logger.info(f"\n📊 Records Inserted: {total}")
    logger.info(f"📅 Date Range: 2022-01-01 to 2024-12-31")
    logger.info(f"🏢 Assignees: {len(ASSIGNEES)} synthetic companies")
    logger.info(f"🌍 Countries: {', '.join(COUNTRIES)}")
    
    logger.info("\n🏆 Top 5 Opportunities (by viability score):")
    for idx, opp in enumerate(top_opps, 1):
        viability = round(opp["viability_score"], 4)
        logger.info(f"  {idx}. {opp['patent_id']} ({opp['country']}) - {viability} - {opp['assignee']}")
        logger.info(f"     Commercial: {opp['commercial_score']} | Synthesis: {opp['synthesis_score']} | FTO Risk: {opp['fto_risk']}")
    
    logger.info("\n📝 Example Record Summary:")
    if inserted_records:
        example = inserted_records[0]
        logger.info(f"  Title: {example['title']}")
        logger.info(f"  Patent ID: {example['patent_id']}")
        logger.info(f"  Assignee: {example['assignee']}")
        logger.info(f"  Sequence: {example['sequence_data'][:50]}...")
        logger.info(f"  Commercial Score: {example['commercial_score']}")
        logger.info(f"  Notes: {example['repurpose_notes']}")
    
    logger.info("\n📋 JSON Preview (3 sample entries):")
    import json
    logger.info(json.dumps(inserted_records[:3], indent=2))
    
    logger.info("\n" + "="*60)
    logger.info("✅ VERIFICATION:")
    logger.info(f"   - patentpulse_items collection: {total} entries")
    logger.info("   - /api/patentpulse/items: Ready to test")
    logger.info("   - /admin/patentpulse: Dashboard ready")
    logger.info("="*60)

async def main():
    """Main entry point"""
    logger.info(f"Environment: {ENV}")
    logger.info(f"Allow seed: {ALLOW_SEED or 'N/A (dev mode)'}")
    
    if ENV == "production":
        logger.warning("⚠️  Running seed in PRODUCTION mode!")
        confirm = input("Type 'YES' to confirm: ")
        if confirm != "YES":
            logger.info("Aborted")
            return
    
    await seed_patents()
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
