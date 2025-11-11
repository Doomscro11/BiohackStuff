#!/usr/bin/env python3
"""
Create MongoDB indexes for Peptimancer
Phase VII - Admin Enhancements
"""
import os
import sys
from pathlib import Path
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# Connect to MongoDB
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'peptimancer_db')

client = MongoClient(mongo_url)
db = client[db_name]

print(f"Creating indexes for database: {db_name}")

# Users collection indexes
print("Creating users indexes...")
try:
    # Unique index on email
    db.users.create_index("email", unique=True, name="email_unique_idx")
    print("  ✓ email (unique)")
    
    # Index on lastLogin for sorting/filtering
    db.users.create_index("lastLogin", name="lastLogin_idx")
    print("  ✓ lastLogin")
    
    # Index on tier for filtering
    db.users.create_index("tier", name="tier_idx")
    print("  ✓ tier")
    
    # Index on role for RBAC queries
    db.users.create_index("role", name="role_idx")
    print("  ✓ role")
    
except Exception as e:
    print(f"  ✗ Error creating users indexes: {str(e)}")

# Credits ledger collection indexes
print("\nCreating credits_ledger indexes...")
try:
    # Compound index on userId and timestamp for efficient queries
    db.credits_ledger.create_index(
        [("userId", ASCENDING), ("timestamp", DESCENDING)],
        name="userId_timestamp_idx"
    )
    print("  ✓ userId + timestamp (compound)")
    
    # Index on timestamp for cleanup queries
    db.credits_ledger.create_index("timestamp", name="timestamp_idx")
    print("  ✓ timestamp")
    
except Exception as e:
    print(f"  ✗ Error creating credits_ledger indexes: {str(e)}")

# Vault ledger indexes (already exists but ensure)
print("\nCreating vault_ledger indexes...")
try:
    db.vault_ledger.create_index("vault_id", unique=True, name="vault_id_unique_idx")
    print("  ✓ vault_id (unique)")
    
    db.vault_ledger.create_index("request_id", name="request_id_idx")
    print("  ✓ request_id")
    
    db.vault_ledger.create_index("created_at", name="created_at_idx")
    print("  ✓ created_at")
    
except Exception as e:
    print(f"  ✗ Error creating vault_ledger indexes: {str(e)}")

# Synthesis requests indexes
print("\nCreating synthesis_requests indexes...")
try:
    db.synthesis_requests.create_index("status", name="status_idx")
    print("  ✓ status")
    
    db.synthesis_requests.create_index("vault_id", name="vault_id_idx")
    print("  ✓ vault_id")
    
    db.synthesis_requests.create_index("created_at", name="created_at_idx")
    print("  ✓ created_at")
    
except Exception as e:
    print(f"  ✗ Error creating synthesis_requests indexes: {str(e)}")

# Magic codes indexes (for auth) with TTL
print("\nCreating _magic_codes indexes...")
try:
    db._magic_codes.create_index("email", name="email_idx")
    print("  ✓ email")
    
    # TTL index for automatic expiration
    db._magic_codes.create_index("expires", name="expires_ttl_idx", expireAfterSeconds=0)
    print("  ✓ expires (TTL)")
    
except Exception as e:
    print(f"  ✗ Error creating _magic_codes indexes: {str(e)}")

# Login attempts indexes (for rate limiting)
print("\nCreating _login_attempts indexes...")
try:
    db._login_attempts.create_index("email", name="email_idx")
    print("  ✓ email")
    
    db._login_attempts.create_index("timestamp", name="timestamp_idx")
    print("  ✓ timestamp")
    
except Exception as e:
    print(f"  ✗ Error creating _login_attempts indexes: {str(e)}")

# Phase 7.1: Errors collection indexes
print("\nCreating errors indexes...")
try:
    db.errors.create_index("ts", name="timestamp_idx")
    print("  ✓ ts (timestamp)")
    
    db.errors.create_index("kind", name="kind_idx")
    print("  ✓ kind")
    
except Exception as e:
    print(f"  ✗ Error creating errors indexes: {str(e)}")

# Phase VIII: Billing collection indexes
print("\nCreating billing indexes...")
try:
    db.plans.create_index("code", unique=True, name="code_unique_idx")
    print("  ✓ plans.code (unique)")
    
    db.subscriptions.create_index("userId", unique=True, name="userId_unique_idx")
    print("  ✓ subscriptions.userId (unique)")
    
    db.subscriptions.create_index("renewsAt", name="renewsAt_idx")
    print("  ✓ subscriptions.renewsAt")
    
except Exception as e:
    print(f"  ✗ Error creating billing indexes: {str(e)}")

# Phase IXa: Analytics collection indexes
print("\nCreating analytics indexes...")
try:
    # Generation logs indexes
    db.generation_logs.create_index("ts", name="timestamp_idx")
    print("  ✓ generation_logs.ts")
    
    db.generation_logs.create_index(
        [("status", ASCENDING), ("ts", DESCENDING)],
        name="status_timestamp_idx"
    )
    print("  ✓ generation_logs.status + ts (compound)")
    
    db.generation_logs.create_index(
        [("userTier", ASCENDING), ("ts", DESCENDING)],
        name="userTier_timestamp_idx"
    )
    print("  ✓ generation_logs.userTier + ts (compound)")
    
    # Analytics snapshots index
    db.analytics_snapshots.create_index(
        [("snapshot_date", DESCENDING)],
        name="snapshot_date_desc_idx"
    )
    print("  ✓ analytics_snapshots.snapshot_date (descending)")
    
except Exception as e:
    print(f"  ✗ Error creating analytics indexes: {str(e)}")

# Phase IXb: PatentPulse collection indexes
print("\nCreating PatentPulse indexes...")
try:
    db.patentpulse_items.create_index("patent_id", unique=True, name="patent_id_unique_idx")
    print("  ✓ patentpulse_items.patent_id (unique)")
    
    db.patentpulse_items.create_index("status", name="status_idx")
    print("  ✓ patentpulse_items.status")
    
    db.patentpulse_items.create_index("expiry_date", name="expiry_date_idx")
    print("  ✓ patentpulse_items.expiry_date")
    
    db.patentpulse_items.create_index(
        [("commercial_score", DESCENDING)],
        name="commercial_score_desc_idx"
    )
    print("  ✓ patentpulse_items.commercial_score (descending)")
    
    db.patentpulse_items.create_index("country", name="country_idx")
    print("  ✓ patentpulse_items.country")
    
    db.patentpulse_items.create_index("assignee", name="assignee_idx")
    print("  ✓ patentpulse_items.assignee")
    
    # Phase IXc: Additional indexes for collector
    db.patentpulse_items.create_index("last_seen_at", name="last_seen_at_idx")
    print("  ✓ patentpulse_items.last_seen_at")
    
    db.patentpulse_items.create_index("source_hash", name="source_hash_idx")
    print("  ✓ patentpulse_items.source_hash")
    
    # Phase IXd: Market signals indexes
    db.patentpulse_items.create_index("market_last_refreshed_at", name="market_last_refreshed_at_idx")
    print("  ✓ patentpulse_items.market_last_refreshed_at")
    
    db.patentpulse_items.create_index(
        [("commercial_score_adj", DESCENDING)],
        name="commercial_score_adj_desc_idx"
    )
    print("  ✓ patentpulse_items.commercial_score_adj (descending)")
    
except Exception as e:
    print(f"  ✗ Error creating PatentPulse indexes: {str(e)}")

# Phase IXc: Collector metadata indexes
print("\nCreating PatentPulse Runs indexes...")
try:
    db.patentpulse_runs.create_index("run_id", unique=True, name="run_id_unique_idx")
    print("  ✓ patentpulse_runs.run_id (unique)")
    
    db.patentpulse_runs.create_index(
        [("started_at", DESCENDING)],
        name="started_at_desc_idx"
    )
    print("  ✓ patentpulse_runs.started_at (descending)")
    
    db.patentpulse_runs.create_index("status", name="status_idx")
    print("  ✓ patentpulse_runs.status")
    
except Exception as e:
    print(f"  ✗ Error creating PatentPulse Runs indexes: {str(e)}")

# Phase IXc: DLQ indexes
print("\nCreating PatentPulse DLQ indexes...")
try:
    db.patentpulse_dlq.create_index("source", name="source_idx")
    print("  ✓ patentpulse_dlq.source")
    
    db.patentpulse_dlq.create_index("retries", name="retries_idx")
    print("  ✓ patentpulse_dlq.retries")
    
    db.patentpulse_dlq.create_index(
        [("last_failed_at", DESCENDING)],
        name="last_failed_at_desc_idx"
    )
    print("  ✓ patentpulse_dlq.last_failed_at (descending)")
    
except Exception as e:
    print(f"  ✗ Error creating PatentPulse DLQ indexes: {str(e)}")

# Phase IXd: Signals indexes with TTL
print("\nCreating PatentPulse Signals indexes...")
try:
    db.patentpulse_signals.create_index("patent_id", name="patent_id_idx")
    print("  ✓ patentpulse_signals.patent_id")
    
    db.patentpulse_signals.create_index("keyword_key", name="keyword_key_idx")
    print("  ✓ patentpulse_signals.keyword_key")
    
    # TTL index for 24h cache expiry
    db.patentpulse_signals.create_index("ttl_expires_at", name="ttl_expires_at_ttl_idx", expireAfterSeconds=0)
    print("  ✓ patentpulse_signals.ttl_expires_at (TTL)")
    
except Exception as e:
    print(f"  ✗ Error creating PatentPulse Signals indexes: {str(e)}")

print("\n✅ Index creation complete!")

# Show all indexes
print("\n📊 Current indexes:")
for collection_name in ['users', 'credits_ledger', 'vault_ledger', 'synthesis_requests', '_magic_codes', '_login_attempts']:
    if collection_name in db.list_collection_names():
        indexes = list(db[collection_name].list_indexes())
        print(f"\n{collection_name}:")
        for idx in indexes:
            print(f"  - {idx['name']}: {idx['key']}")

client.close()
