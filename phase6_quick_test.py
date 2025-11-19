#!/usr/bin/env python3
"""
Phase VI Quick Backend Test - Focus on Critical Issues from Iteration 5
"""

import requests
import json
from datetime import datetime

BACKEND_URL = "https://peptimancer-share.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def test_critical_endpoints():
    """Test the critical endpoints that were failing in iteration 5"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "summary": {}
    }
    
    print("🧬 PEPTIMANCER PHASE VI - CRITICAL ENDPOINT VALIDATION")
    print("=" * 60)
    
    # Test 1: API Health
    print("\n1. Testing API Health...")
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
    
    # Test 2: Vault Ledger System (Critical Issue from Iteration 5)
    print("\n2. Testing Vault Ledger System (Critical from Iteration 5)...")
    try:
        response = requests.get(f"{API_BASE}/vault-ledger?limit=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            entries = data.get('ledger_entries', [])
            print(f"✅ Vault Ledger: FIXED ({len(entries)} entries, status: {data.get('registry_status')})")
            results["tests"]["vault_ledger"] = {"status": "PASS", "details": f"{len(entries)} entries"}
        else:
            print(f"❌ Vault Ledger: STILL FAILING (HTTP {response.status_code})")
            results["tests"]["vault_ledger"] = {"status": "FAIL", "error": f"HTTP {response.status_code}: {response.text[:200]}"}
    except Exception as e:
        print(f"❌ Vault Ledger: STILL FAILING ({str(e)})")
        results["tests"]["vault_ledger"] = {"status": "FAIL", "error": str(e)}
    
    # Test 3: Generation History (Critical Issue from Iteration 5)
    print("\n3. Testing Generation History (Critical from Iteration 5)...")
    try:
        response = requests.get(f"{API_BASE}/generation-history?limit=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            history = data.get('history', [])
            print(f"✅ Generation History: FIXED ({len(history)} entries, status: {data.get('status')})")
            results["tests"]["generation_history"] = {"status": "PASS", "details": f"{len(history)} entries"}
        else:
            print(f"❌ Generation History: STILL FAILING (HTTP {response.status_code})")
            results["tests"]["generation_history"] = {"status": "FAIL", "error": f"HTTP {response.status_code}: {response.text[:200]}"}
    except Exception as e:
        print(f"❌ Generation History: STILL FAILING ({str(e)})")
        results["tests"]["generation_history"] = {"status": "FAIL", "error": str(e)}
    
    # Test 4: Analogue Generation (Core Functionality)
    print("\n4. Testing Analogue Generation (Core Functionality)...")
    try:
        payload = {
            "base_molecule": "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR",
            "allowed_mods": "Substitution, D-isomers",
            "exclusions": "No modifications",
            "target_use": "Phase VI Test",
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
                results["tests"]["analogue_generation"] = {
                    "status": "PASS", 
                    "details": f"{len(analogues)} analogues",
                    "generation_id": data.get('request_id'),
                    "vault_ids": [a.get('vault_id') for a in analogues]
                }
            else:
                print(f"❌ Analogue Generation: PARTIAL (Expected 2, got {len(analogues)})")
                results["tests"]["analogue_generation"] = {"status": "PARTIAL", "error": f"Expected 2, got {len(analogues)}"}
        else:
            print(f"❌ Analogue Generation: FAILED (HTTP {response.status_code})")
            results["tests"]["analogue_generation"] = {"status": "FAIL", "error": f"HTTP {response.status_code}: {response.text[:200]}"}
    except Exception as e:
        print(f"❌ Analogue Generation: FAILED ({str(e)})")
        results["tests"]["analogue_generation"] = {"status": "FAIL", "error": str(e)}
    
    # Test 5: PDF Export (Was Fixed in Iteration 5)
    generation_id = results["tests"].get("analogue_generation", {}).get("generation_id")
    if generation_id:
        print("\n5. Testing PDF Export (Was Fixed in Iteration 5)...")
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
                    print(f"❌ PDF Export: BROKEN (Invalid PDF: {content_length} bytes)")
                    results["tests"]["pdf_export"] = {"status": "FAIL", "error": f"Invalid PDF: {content_length} bytes"}
            else:
                print(f"❌ PDF Export: BROKEN (HTTP {response.status_code})")
                results["tests"]["pdf_export"] = {"status": "FAIL", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ PDF Export: BROKEN ({str(e)})")
            results["tests"]["pdf_export"] = {"status": "FAIL", "error": str(e)}
    else:
        print("\n5. PDF Export: SKIPPED (No generation ID available)")
        results["tests"]["pdf_export"] = {"status": "SKIP", "error": "No generation ID"}
    
    # Test 6: CRO Integration (Was Working in Iteration 5)
    vault_ids = results["tests"].get("analogue_generation", {}).get("vault_ids", [])
    if vault_ids and vault_ids[0]:
        print("\n6. Testing CRO Integration (Was Working in Iteration 5)...")
        try:
            payload = {
                "vault_id": vault_ids[0],
                "partner_name": "Phase VI Test CRO",
                "quantity_mg": 100.0,
                "purity_requirement": 95.0,
                "timeline_days": 14,
                "contact_email": "test@phase6.com"
            }
            
            response = requests.post(f"{API_BASE}/request-synthesis", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                partner_ref = data.get('partner_response', {}).get('partner_reference', '')
                if partner_ref.startswith('SYN-'):
                    print(f"✅ CRO Integration: STILL WORKING (Ref: {partner_ref})")
                    results["tests"]["cro_integration"] = {"status": "PASS", "details": f"Ref: {partner_ref}"}
                else:
                    print(f"❌ CRO Integration: BROKEN (Invalid ref: {partner_ref})")
                    results["tests"]["cro_integration"] = {"status": "FAIL", "error": f"Invalid ref: {partner_ref}"}
            else:
                print(f"❌ CRO Integration: BROKEN (HTTP {response.status_code})")
                results["tests"]["cro_integration"] = {"status": "FAIL", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ CRO Integration: BROKEN ({str(e)})")
            results["tests"]["cro_integration"] = {"status": "FAIL", "error": str(e)}
    else:
        print("\n6. CRO Integration: SKIPPED (No vault ID available)")
        results["tests"]["cro_integration"] = {"status": "SKIP", "error": "No vault ID"}
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PHASE VI CRITICAL ENDPOINT SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for test in results["tests"].values() if test["status"] == "PASS")
    total = len([test for test in results["tests"].values() if test["status"] != "SKIP"])
    
    results["summary"] = {
        "tests_passed": passed,
        "tests_total": total,
        "success_rate": (passed / total * 100) if total > 0 else 0,
        "critical_issues_from_iteration_5": {
            "vault_ledger_fixed": results["tests"]["vault_ledger"]["status"] == "PASS",
            "generation_history_fixed": results["tests"]["generation_history"]["status"] == "PASS",
            "pdf_export_still_working": results["tests"]["pdf_export"]["status"] == "PASS"
        }
    }
    
    print(f"Tests Passed: {passed}/{total} ({results['summary']['success_rate']:.1f}%)")
    
    critical_fixed = sum(1 for fixed in results["summary"]["critical_issues_from_iteration_5"].values() if fixed)
    print(f"Critical Issues Fixed: {critical_fixed}/3")
    
    if critical_fixed == 3:
        print("🎉 ALL CRITICAL ISSUES FROM ITERATION 5 HAVE BEEN FIXED!")
    else:
        print("⚠️  Some critical issues from iteration 5 still remain")
    
    return results

if __name__ == "__main__":
    results = test_critical_endpoints()
    
    # Save results
    with open('/app/phase6_critical_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: /app/phase6_critical_test_results.json")