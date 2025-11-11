#!/usr/bin/env python3
"""
PatentPulse Post-Deploy Verifier
Validates canary stability & SLO compliance before promotion

Usage:
    python jobs/post_deploy_verifier.py
    
Environment Variables:
    API_BASE_URL - Base URL for API endpoints
    MONGO_URI - MongoDB connection string
    DB_NAME - Database name (default: peptimancer_db)
    EXPECT_MIN_ITEMS - Minimum expected patents (default: 27)
    FEATURE_FLAG_NAME - Feature flag to check (default: FEATURE_PATENTPULSE)
    FEATURE_FLAG_EXPECTED - Expected flag value (default: true)
    P95_MAX_MS - Max p95 latency in ms (default: 900)
    ERROR_RATE_MAX - Max error rate (default: 0.02)
"""

import os
import sys
import json
import time
import statistics
from datetime import datetime
from typing import Dict, List, Tuple
import requests
from pymongo import MongoClient

# Configuration from environment
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8001')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'peptimancer_db')
EXPECT_MIN_ITEMS = int(os.getenv('EXPECT_MIN_ITEMS', '27'))
FEATURE_FLAG_NAME = os.getenv('FEATURE_FLAG_NAME', 'FEATURE_PATENTPULSE')
FEATURE_FLAG_EXPECTED = os.getenv('FEATURE_FLAG_EXPECTED', 'true')
P95_MAX_MS = int(os.getenv('P95_MAX_MS', '900'))
ERROR_RATE_MAX = float(os.getenv('ERROR_RATE_MAX', '0.02'))

# Test results storage
results = {
    "timestamp": datetime.utcnow().isoformat(),
    "checks": {},
    "metrics": {},
    "pass": True,
    "failures": []
}

def log_check(name: str, passed: bool, details: str = ""):
    """Log a check result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if details:
        print(f"    {details}")
    
    results["checks"][name] = {
        "passed": passed,
        "details": details
    }
    
    if not passed:
        results["pass"] = False
        results["failures"].append(name)

def measure_latency(url: str, samples: int = 20) -> Tuple[float, float, float]:
    """Measure avg, p95, and max latency over N samples"""
    latencies = []
    errors = 0
    
    for _ in range(samples):
        start = time.time()
        try:
            response = requests.get(url, timeout=5)
            elapsed_ms = (time.time() - start) * 1000
            latencies.append(elapsed_ms)
            if response.status_code >= 500:
                errors += 1
        except Exception as e:
            errors += 1
            latencies.append(5000)  # Timeout or error
    
    if not latencies:
        return 0, 0, 0
    
    avg = statistics.mean(latencies)
    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
    max_latency = max(latencies)
    error_rate = errors / samples
    
    return avg, p95, max_latency, error_rate

def check_http_endpoints():
    """Check 1: HTTP smoke tests on PatentPulse endpoints"""
    print("\n🔍 Check 1: HTTP Endpoint Smoke Tests")
    
    endpoints = [
        "/health",
        "/api/patentpulse/items",
        "/api/patentpulse/stats",
        "/api/patentpulse/top-opportunities"
    ]
    
    all_passed = True
    
    for endpoint in endpoints:
        url = f"{API_BASE_URL}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            passed = response.status_code in [200, 401, 403]  # 401/403 acceptable for protected endpoints
            log_check(
                f"Endpoint {endpoint}",
                passed,
                f"Status: {response.status_code}"
            )
            if not passed:
                all_passed = False
        except Exception as e:
            log_check(f"Endpoint {endpoint}", False, f"Error: {str(e)}")
            all_passed = False
    
    return all_passed

def check_json_shape():
    """Check 2: Validate JSON shape and key presence"""
    print("\n🔍 Check 2: JSON Response Shape Validation")
    
    # Test /stats endpoint
    try:
        url = f"{API_BASE_URL}/api/patentpulse/stats"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            required_keys = ["total", "by_status", "top_assignees", "avg_commercial_score"]
            missing_keys = [k for k in required_keys if k not in data]
            
            passed = len(missing_keys) == 0
            log_check(
                "Stats JSON shape",
                passed,
                f"Missing keys: {missing_keys}" if missing_keys else "All required keys present"
            )
        else:
            log_check("Stats JSON shape", False, f"Non-200 status: {response.status_code}")
    except Exception as e:
        log_check("Stats JSON shape", False, f"Error: {str(e)}")

def check_latency():
    """Check 3: Compute latency (avg, p95) from 20 samples"""
    print("\n🔍 Check 3: Latency Performance Measurement")
    
    url = f"{API_BASE_URL}/api/patentpulse/items?limit=10"
    
    print(f"   Measuring latency over 20 samples...")
    avg, p95, max_lat, error_rate = measure_latency(url, samples=20)
    
    results["metrics"]["latency_avg_ms"] = round(avg, 2)
    results["metrics"]["latency_p95_ms"] = round(p95, 2)
    results["metrics"]["latency_max_ms"] = round(max_lat, 2)
    results["metrics"]["error_rate"] = round(error_rate, 4)
    
    # Check SLOs
    p95_passed = p95 <= P95_MAX_MS
    error_rate_passed = error_rate <= ERROR_RATE_MAX
    
    log_check(
        "Latency p95 SLO",
        p95_passed,
        f"p95: {p95:.2f}ms (max: {P95_MAX_MS}ms)"
    )
    
    log_check(
        "Error Rate SLO",
        error_rate_passed,
        f"Error rate: {error_rate:.2%} (max: {ERROR_RATE_MAX:.2%})"
    )
    
    return p95_passed and error_rate_passed

def check_feature_flag():
    """Check 4: Verify FEATURE_PATENTPULSE==true"""
    print("\n🔍 Check 4: Feature Flag Verification")
    
    flag_value = os.getenv(FEATURE_FLAG_NAME, "false")
    passed = flag_value.lower() == FEATURE_FLAG_EXPECTED.lower()
    
    log_check(
        "Feature flag status",
        passed,
        f"{FEATURE_FLAG_NAME}={flag_value} (expected: {FEATURE_FLAG_EXPECTED})"
    )
    
    return passed

def check_mongo():
    """Check 5: Mongo checks: count≥27, indexes exist"""
    print("\n🔍 Check 5: MongoDB Data & Index Validation")
    
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db['patentpulse_items']
        
        # Count documents
        count = collection.count_documents({})
        count_passed = count >= EXPECT_MIN_ITEMS
        
        log_check(
            "Patent count",
            count_passed,
            f"Found: {count} (minimum: {EXPECT_MIN_ITEMS})"
        )
        
        # Check indexes
        indexes = list(collection.list_indexes())
        index_names = [idx['name'] for idx in indexes]
        
        required_indexes = ['patent_id_unique_idx', 'status_idx', 'commercial_score_desc_idx']
        missing_indexes = [idx for idx in required_indexes if idx not in index_names]
        
        indexes_passed = len(missing_indexes) == 0
        
        log_check(
            "Required indexes",
            indexes_passed,
            f"Missing: {missing_indexes}" if missing_indexes else "All indexes present"
        )
        
        client.close()
        return count_passed and indexes_passed
        
    except Exception as e:
        log_check("MongoDB connection", False, f"Error: {str(e)}")
        return False

def check_data_quality():
    """Check 7: Data-Quality Guardrails"""
    print("\n🔍 Check 7: Data Quality Guardrails")
    
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db['patentpulse_items']
        
        # Required fields check
        required_fields = ['title', 'status', 'commercial_score', 'expiry_date']
        
        # Sample 10 random documents
        samples = list(collection.aggregate([{"$sample": {"size": 10}}]))
        
        field_violations = 0
        score_violations = 0
        date_violations = 0
        
        for doc in samples:
            # Check required fields
            missing = [f for f in required_fields if f not in doc]
            if missing:
                field_violations += 1
            
            # Check commercial_score range
            if 'commercial_score' in doc:
                score = doc['commercial_score']
                if not (0 <= score <= 1):
                    score_violations += 1
            
            # Check expiry_date < now
            if 'expiry_date' in doc:
                expiry = doc['expiry_date']
                if isinstance(expiry, datetime) and expiry > datetime.utcnow():
                    date_violations += 1
        
        all_passed = field_violations == 0 and score_violations == 0 and date_violations == 0
        
        log_check(
            "Required fields",
            field_violations == 0,
            f"Violations: {field_violations}/10 samples"
        )
        
        log_check(
            "Commercial score range",
            score_violations == 0,
            f"Out of range: {score_violations}/10 samples"
        )
        
        log_check(
            "Expiry dates",
            date_violations == 0,
            f"Future dates: {date_violations}/10 samples"
        )
        
        client.close()
        return all_passed
        
    except Exception as e:
        log_check("Data quality check", False, f"Error: {str(e)}")
        return False

def check_idempotency():
    """Check 8: Idempotency Check"""
    print("\n🔍 Check 8: Idempotency & Duplicate Prevention")
    
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db['patentpulse_items']
        
        # Check for duplicate patent_ids
        pipeline = [
            {"$group": {"_id": "$patent_id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}}
        ]
        
        duplicates = list(collection.aggregate(pipeline))
        duplicate_count = len(duplicates)
        
        passed = duplicate_count == 0
        
        log_check(
            "Duplicate prevention",
            passed,
            f"Duplicates found: {duplicate_count}"
        )
        
        client.close()
        return passed
        
    except Exception as e:
        log_check("Idempotency check", False, f"Error: {str(e)}")
        return False

def print_summary():
    """Print final summary"""
    print("\n" + "="*60)
    print("POST-DEPLOY VERIFICATION SUMMARY")
    print("="*60)
    
    # Overall status
    if results["pass"]:
        print("✅ OVERALL STATUS: PASS")
        print("\n🎉 Canary is healthy and ready for promotion!")
    else:
        print("❌ OVERALL STATUS: FAIL")
        print(f"\n⚠️  Failed checks: {', '.join(results['failures'])}")
        print("\n🚨 ROLLBACK RECOMMENDED")
    
    # Metrics
    print("\n📊 SLO Metrics:")
    print(f"   - Latency (avg): {results['metrics'].get('latency_avg_ms', 0):.2f}ms")
    print(f"   - Latency (p95): {results['metrics'].get('latency_p95_ms', 0):.2f}ms (SLO: ≤{P95_MAX_MS}ms)")
    print(f"   - Error rate: {results['metrics'].get('error_rate', 0):.2%} (SLO: ≤{ERROR_RATE_MAX:.2%})")
    
    # Summary table
    print("\n📋 Check Summary:")
    for check_name, check_data in results["checks"].items():
        status = "✅" if check_data["passed"] else "❌"
        print(f"   {status} {check_name}")
    
    print("\n" + "="*60)
    
    # JSON output
    print("\n📄 JSON Result:")
    print(json.dumps(results, indent=2))

def main():
    """Main verification flow"""
    print("🚀 PatentPulse Post-Deploy Verifier")
    print(f"   Target: {API_BASE_URL}")
    print(f"   Database: {DB_NAME}")
    print(f"   Timestamp: {results['timestamp']}")
    
    # Run all checks
    check_http_endpoints()
    check_json_shape()
    check_latency()
    check_feature_flag()
    check_mongo()
    check_data_quality()
    check_idempotency()
    
    # Print summary
    print_summary()
    
    # Exit with appropriate code
    exit_code = 0 if results["pass"] else 1
    
    if exit_code == 0:
        print("\n✅ Verification PASSED - Safe to promote canary")
    else:
        print("\n❌ Verification FAILED - Rollback recommended")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
