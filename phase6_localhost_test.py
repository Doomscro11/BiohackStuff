#!/usr/bin/env python3
"""
Phase VI Backend Test - Using Localhost to Test Core Functionality
"""

import requests
import json
from datetime import datetime

# Use localhost for testing
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

def test_backend_localhost():
    """Test backend using localhost to bypass external connectivity issues"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "summary": {}
    }
    
    print("🧬 PEPTIMANCER PHASE VI - LOCALHOST BACKEND VALIDATION")
    print("=" * 60)
    
    # Test 1: API Health
    print("\n1. Testing API Health (localhost)...")
    try:
        response = requests.get(f"{API_BASE}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Health: OK (Version: {data.get('version')})")
            results["tests"]["api_health"] = {"status": "PASS", "details": f"Version {data.get('version')}"}
        else:
            print(f"❌ API Health: FAILED (HTTP {response.status_code})")
            results["tests"]["api_health"] = {"status": "FAIL", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        print(f"❌ API Health: FAILED ({str(e)})")
        results["tests"]["api_health"] = {"status": "FAIL", "error": str(e)}
    
    # Test 2: Sequence Validation
    print("\n2. Testing Sequence Validation...")
    try:
        response = requests.get(f"{API_BASE}/validate-sequence/HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('is_valid'):
                print(f"✅ Sequence Validation: OK (Valid sequence detected)")
                results["tests"]["sequence_validation"] = {"status": "PASS", "details": "Valid sequence"}
            else:
                print(f"❌ Sequence Validation: FAILED (Valid sequence not recognized)")
                results["tests"]["sequence_validation"] = {"status": "FAIL", "error": "Valid sequence not recognized"}
        else:
            print(f"❌ Sequence Validation: FAILED (HTTP {response.status_code})")
            results["tests"]["sequence_validation"] = {"status": "FAIL", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        print(f"❌ Sequence Validation: FAILED ({str(e)})")
        results["tests"]["sequence_validation"] = {"status": "FAIL", "error": str(e)}
    
    # Test 3: Vault Ledger System (Critical Issue from Iteration 5)
    print("\n3. Testing Vault Ledger System (Critical from Iteration 5)...")
    try:
        response = requests.get(f"{API_BASE}/vault-ledger?limit=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            entries = data.get('ledger_entries', [])
            print(f"✅ Vault Ledger: FIXED ({len(entries)} entries, status: {data.get('registry_status')})")
            results["tests"]["vault_ledger"] = {"status": "PASS", "details": f"{len(entries)} entries"}
        else:
            print(f"❌ Vault Ledger: STILL FAILING (HTTP {response.status_code})")
            print(f"   Response: {response.text[:300]}")
            results["tests"]["vault_ledger"] = {"status": "FAIL", "error": f"HTTP {response.status_code}: {response.text[:200]}"}
    except Exception as e:
        print(f"❌ Vault Ledger: STILL FAILING ({str(e)})")
        results["tests"]["vault_ledger"] = {"status": "FAIL", "error": str(e)}
    
    # Test 4: Generation History (Critical Issue from Iteration 5)
    print("\n4. Testing Generation History (Critical from Iteration 5)...")
    try:
        response = requests.get(f"{API_BASE}/generation-history?limit=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            history = data.get('history', [])
            print(f"✅ Generation History: FIXED ({len(history)} entries, status: {data.get('status')})")
            results["tests"]["generation_history"] = {"status": "PASS", "details": f"{len(history)} entries"}
        else:
            print(f"❌ Generation History: STILL FAILING (HTTP {response.status_code})")
            print(f"   Response: {response.text[:300]}")
            results["tests"]["generation_history"] = {"status": "FAIL", "error": f"HTTP {response.status_code}: {response.text[:200]}"}
    except Exception as e:
        print(f"❌ Generation History: STILL FAILING ({str(e)})")
        results["tests"]["generation_history"] = {"status": "FAIL", "error": str(e)}
    
    # Test 5: Analogue Generation (Core Functionality)
    print("\n5. Testing Analogue Generation (Core Functionality)...")
    try:
        payload = {
            "base_molecule": "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR",
            "allowed_mods": "Substitution, D-isomers",
            "exclusions": "No modifications",
            "target_use": "Phase VI Localhost Test",
            "num_analogues": 2,
            "include_cost": True
        }
        
        print("   Generating analogues (may take 10-15 seconds)...")
        response = requests.post(f"{API_BASE}/generate-analogues", json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            analogues = data.get('analogues', [])
            if len(analogues) == 2:
                print(f"✅ Analogue Generation: OK ({len(analogues)} analogues generated)")
                # Check enterprise fields
                first_analogue = analogues[0]
                enterprise_fields = ['vault_id', 'patent_similarity_risk', 'novelty_score', 'binding_affinity']
                missing_fields = [field for field in enterprise_fields if not first_analogue.get(field)]
                
                if not missing_fields:
                    print(f"   ✅ Enterprise fields present: {enterprise_fields}")
                    results["tests"]["analogue_generation"] = {
                        "status": "PASS", 
                        "details": f"{len(analogues)} analogues with enterprise fields",
                        "generation_id": data.get('request_id'),
                        "vault_ids": [a.get('vault_id') for a in analogues]
                    }
                else:
                    print(f"   ⚠️  Missing enterprise fields: {missing_fields}")
                    results["tests"]["analogue_generation"] = {
                        "status": "PARTIAL", 
                        "details": f"{len(analogues)} analogues, missing fields: {missing_fields}",
                        "generation_id": data.get('request_id'),
                        "vault_ids": [a.get('vault_id') for a in analogues]
                    }
            else:
                print(f"❌ Analogue Generation: PARTIAL (Expected 2, got {len(analogues)})")
                results["tests"]["analogue_generation"] = {"status": "PARTIAL", "error": f"Expected 2, got {len(analogues)}"}
        else:
            print(f"❌ Analogue Generation: FAILED (HTTP {response.status_code})")
            print(f"   Response: {response.text[:300]}")
            results["tests"]["analogue_generation"] = {"status": "FAIL", "error": f"HTTP {response.status_code}: {response.text[:200]}"}
    except Exception as e:
        print(f"❌ Analogue Generation: FAILED ({str(e)})")
        results["tests"]["analogue_generation"] = {"status": "FAIL", "error": str(e)}
    
    # Test 6: PDF Export (Was Fixed in Iteration 5)
    generation_id = results["tests"].get("analogue_generation", {}).get("generation_id")
    if generation_id:
        print("\n6. Testing PDF Export (Was Fixed in Iteration 5)...")
        try:
            payload = {
                "generation_id": generation_id,
                "format": "pdf",
                "include_cost": True,
                "watermark": True
            }
            
            response = requests.post(f"{API_BASE}/export-report", json=payload, timeout=15)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                if 'pdf' in content_type.lower() and content_length > 1000:
                    print(f"✅ PDF Export: STILL WORKING ({content_length} bytes)")
                    results["tests"]["pdf_export"] = {"status": "PASS", "details": f"{content_length} bytes PDF"}
                else:
                    print(f"❌ PDF Export: BROKEN (Invalid PDF: {content_length} bytes, type: {content_type})")
                    results["tests"]["pdf_export"] = {"status": "FAIL", "error": f"Invalid PDF: {content_length} bytes"}
            else:
                print(f"❌ PDF Export: BROKEN (HTTP {response.status_code})")
                print(f"   Response: {response.text[:300]}")
                results["tests"]["pdf_export"] = {"status": "FAIL", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ PDF Export: BROKEN ({str(e)})")
            results["tests"]["pdf_export"] = {"status": "FAIL", "error": str(e)}
    else:
        print("\n6. PDF Export: SKIPPED (No generation ID available)")
        results["tests"]["pdf_export"] = {"status": "SKIP", "error": "No generation ID"}
    
    # Test 7: Token Management
    print("\n7. Testing Token Management...")
    try:
        response = requests.post(f"{API_BASE}/vault-tokens/create?user_id=phase6_test&tier=enterprise&credits=1000", timeout=10)
        if response.status_code == 200:
            data = response.json()
            token_id = data.get('token_id')
            if token_id:
                print(f"✅ Token Management: OK (Token: {token_id})")
                results["tests"]["token_management"] = {"status": "PASS", "details": f"Token: {token_id}"}
            else:
                print(f"❌ Token Management: FAILED (No token ID returned)")
                results["tests"]["token_management"] = {"status": "FAIL", "error": "No token ID"}
        else:
            print(f"❌ Token Management: FAILED (HTTP {response.status_code})")
            results["tests"]["token_management"] = {"status": "FAIL", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        print(f"❌ Token Management: FAILED ({str(e)})")
        results["tests"]["token_management"] = {"status": "FAIL", "error": str(e)}
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PHASE VI LOCALHOST BACKEND SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for test in results["tests"].values() if test["status"] == "PASS")
    partial = sum(1 for test in results["tests"].values() if test["status"] == "PARTIAL")
    total = len([test for test in results["tests"].values() if test["status"] != "SKIP"])
    
    results["summary"] = {
        "tests_passed": passed,
        "tests_partial": partial,
        "tests_total": total,
        "success_rate": (passed / total * 100) if total > 0 else 0,
        "critical_issues_from_iteration_5": {
            "vault_ledger_fixed": results["tests"]["vault_ledger"]["status"] == "PASS",
            "generation_history_fixed": results["tests"]["generation_history"]["status"] == "PASS",
            "pdf_export_still_working": results["tests"]["pdf_export"]["status"] == "PASS"
        }
    }
    
    print(f"Tests Passed: {passed}/{total} ({results['summary']['success_rate']:.1f}%)")
    print(f"Tests Partial: {partial}/{total}")
    
    critical_fixed = sum(1 for fixed in results["summary"]["critical_issues_from_iteration_5"].values() if fixed)
    print(f"Critical Issues Fixed: {critical_fixed}/3")
    
    if critical_fixed == 3:
        print("🎉 ALL CRITICAL ISSUES FROM ITERATION 5 HAVE BEEN FIXED!")
    elif critical_fixed >= 2:
        print("✅ Most critical issues from iteration 5 have been fixed")
    else:
        print("⚠️  Critical issues from iteration 5 still remain")
    
    return results

if __name__ == "__main__":
    results = test_backend_localhost()
    
    # Save results
    with open('/app/phase6_localhost_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: /app/phase6_localhost_test_results.json")