# Analytics Seed Script - Development Only
# Populates sample data for chart testing
# Usage: python -m app.jobs.seed_analytics_dev

import os
import logging
import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
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
generation_logs = db['generation_logs']
credits_ledger = db['credits_ledger']
analytics_snapshots = db['analytics_snapshots']

MOD_GROUPS = [
    "protease_resistance",
    "exopeptidase_protection",
    "affinity_tuning",
    "pk_extension",
    "conformational_stability"
]

async def seed_analytics():
    """
    Seed 14 days of realistic sample data
    """
    logger.info("Starting analytics seed...")
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Clear existing test data (optional - comment out to preserve)
    logger.info("Clearing existing analytics data...")
    await generation_logs.delete_many({})
    await analytics_snapshots.delete_many({})
    
    total_gen_logs = 0
    total_ledger = 0
    total_snapshots = 0
    
    for d in range(14):
        day = today - timedelta(days=(13 - d))
        logger.info(f"Seeding day {d + 1}/14: {day.date()}")
        
        # Generation logs for this day (6-14 requests)
        num_requests = random.randint(6, 14)
        day_analogues = 0
        
        for _ in range(num_requests):
            # Random mod mix
            mods_mix = {
                group: random.randint(0, 1)
                for group in MOD_GROUPS
            }
            
            # Status (92% success rate)
            status = "success" if random.random() > 0.08 else "error"
            error_kind = None
            if status == "error":
                error_kind = random.choice(["402_out_of_credits", "400_conflict"])
            
            num_analogues = random.choice([1, 2, 3])
            if status == "success":
                day_analogues += num_analogues
            
            # Insert generation log
            await generation_logs.insert_one({
                "ts": day + timedelta(minutes=random.randint(0, 60 * 23)),
                "userTier": random.choice(["basic", "pro", "pro", "enterprise"]),  # weighted
                "numAnalogues": num_analogues,
                "seqLen": random.randint(25, 40),
                "mods": mods_mix,
                "exclusionsCount": random.randint(0, 3),
                "status": status,
                "errorKind": error_kind,
                "latencyMs": random.randint(600, 2600)
            })
            total_gen_logs += 1
        
        # Credits ledger entries
        # Random purchases (70% chance of purchase)
        purchased = 0
        if random.random() > 0.3:
            purchased = random.choice([100, 200, 500])
            await credits_ledger.insert_one({
                "userId": str(ObjectId()),
                "delta": purchased,
                "reason": "Credit purchase",
                "balanceAfter": purchased,
                "timestamp": day + timedelta(hours=random.randint(1, 10)),
                "meta": {}
            })
            total_ledger += 1
        
        # Consumption based on day's analogues
        consumed = day_analogues  # 1 credit per analogue
        if consumed > 0:
            await credits_ledger.insert_one({
                "userId": str(ObjectId()),
                "delta": -consumed,
                "reason": f"Analogue generation x{consumed}",
                "balanceAfter": max(0, purchased - consumed),
                "timestamp": day + timedelta(hours=random.randint(12, 22)),
                "meta": {}
            })
            total_ledger += 1
        
        # Create snapshot for this day
        # Calculate cumulative mod mix for the day
        mod_mix_for_day = {
            group: sum([
                random.randint(5, 25)
                for _ in range(random.randint(1, 3))
            ])
            for group in MOD_GROUPS
        }
        
        await analytics_snapshots.insert_one({
            "snapshot_date": day,
            "users_total": 50 + d,
            "users_active_24h": random.randint(5, 18),
            "analogues_24h": day_analogues,
            "analogues_7d": random.randint(400, 600),
            "analogues_total": 1000 + (d * 80),
            "credits_purchased_24h": purchased,
            "credits_consumed_24h": consumed,
            "net_flow_24h": purchased - consumed,
            "mod_group_mix_24h": mod_mix_for_day,
            "errors_24h": random.randint(0, 5),
            "latency_p95_ms": random.choice([None, 1800, 2100, 2400]),
            "created_at": day
        })
        total_snapshots += 1
    
    logger.info(f"Seed complete!")
    logger.info(f"  - Generation logs: {total_gen_logs}")
    logger.info(f"  - Ledger entries: {total_ledger}")
    logger.info(f"  - Snapshots: {total_snapshots}")
    logger.info(f"Charts should now render with 14 days of data")

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
    
    await seed_analytics()
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
