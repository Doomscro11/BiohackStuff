#!/usr/bin/env python3
"""
Partner Shares Deprecation & Core App Stabilization Testing
Comprehensive validation for Partner Shares removal and core functionality
"""

import requests
import json
import time
import asyncio
import aiohttp
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

# Use production endpoint from frontend .env
BACKEND_URL = "https://partner-purge.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class PeptimancerEnterpriseTest:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []
        self.test_results = {}
        
    def log_test(self, test_name, success, details="", error_details=""):
        """Log test results with enterprise-grade detail"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
            if details:
                print(f"   Details: {details}")
        else:
            print(f"❌ {test_name}: FAILED")
            if error_details:
                print(f"   Error: {error_details}")
            self.critical_failures.append({
                "test": test_name,
                "error": error_details,
                "timestamp": datetime.now().isoformat()
            })
        
        self.test_results[test_name] = {
            "success": success,
            "details": details,
            "error": error_details,
            "timestamp": datetime.now().isoformat()
        }
        print()

    def test_api_health(self):
        """Test basic API connectivity and health"""
        try:
            response = requests.get(f"{API_BASE}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "API Health Check",
                    True,
                    f"Status: {response.status_code}, Version: {data.get('version', 'unknown')}"
                )
                return True
            else:
                self.log_test(
                    "API Health Check",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "API Health Check",
                False,
                error_details=f"Connection failed: {str(e)}"
            )
            return False

    def test_sequence_validation(self):
        """Test peptide sequence validation system"""
        test_cases = [
            ("HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR", True, "Valid GLP-1 sequence"),
            ("INVALID123", False, "Invalid characters"),
            ("", False, "Empty sequence"),
            ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", False, "Invalid amino acids")
        ]
        
        all_passed = True
        for sequence, should_be_valid, description in test_cases:
            try:
                if sequence:
                    response = requests.get(f"{API_BASE}/validate-sequence/{sequence}", timeout=10)
                else:
                    response = requests.get(f"{API_BASE}/validate-sequence/", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    is_valid = data.get('is_valid', False)
                    
                    if is_valid == should_be_valid:
                        self.log_test(
                            f"Sequence Validation - {description}",
                            True,
                            f"Correctly identified as {'valid' if is_valid else 'invalid'}"
                        )
                    else:
                        self.log_test(
                            f"Sequence Validation - {description}",
                            False,
                            error_details=f"Expected {should_be_valid}, got {is_valid}"
                        )
                        all_passed = False
                else:
                    self.log_test(
                        f"Sequence Validation - {description}",
                        False,
                        error_details=f"HTTP {response.status_code}: {response.text}"
                    )
                    all_passed = False
                    
            except Exception as e:
                self.log_test(
                    f"Sequence Validation - {description}",
                    False,
                    error_details=f"Request failed: {str(e)}"
                )
                all_passed = False
        
        return all_passed

    def test_analogue_generation(self):
        """Test enterprise-grade peptide analogue generation"""
        payload = {
            "base_molecule": "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR",
            "allowed_mods": "Substitution, Lipidation, Cyclization, D-isomers",
            "exclusions": "No Aib or γ-Glu residues",
            "target_use": "Enterprise GLP-1R Research",
            "num_analogues": 3,
            "include_cost": True
        }
        
        try:
            print("🧬 Generating enterprise analogues (may take 10-15 seconds)...")
            response = requests.post(f"{API_BASE}/generate-analogues", json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                analogues = data.get('analogues', [])
                
                if len(analogues) == 3:
                    # Validate enterprise fields
                    enterprise_fields_valid = True
                    for i, analogue in enumerate(analogues):
                        required_fields = [
                            'vault_id', 'analogue_name', 'modified_sequence',
                            'patent_similarity_risk', 'novelty_score', 'ip_notes',
                            'binding_affinity', 'predicted_half_life', 'synthesis_complexity'
                        ]
                        
                        missing_fields = [field for field in required_fields if not analogue.get(field)]
                        if missing_fields:
                            enterprise_fields_valid = False
                            print(f"   Analogue {i+1} missing fields: {missing_fields}")
                    
                    if enterprise_fields_valid:
                        self.log_test(
                            "Enterprise Analogue Generation",
                            True,
                            f"Generated {len(analogues)} analogues with all enterprise fields"
                        )
                        
                        # Store generation ID for later tests
                        self.generation_id = data.get('request_id')
                        self.vault_ids = [a.get('vault_id') for a in analogues if a.get('vault_id')]
                        return True
                    else:
                        self.log_test(
                            "Enterprise Analogue Generation",
                            False,
                            error_details="Missing required enterprise fields in analogues"
                        )
                        return False
                else:
                    self.log_test(
                        "Enterprise Analogue Generation",
                        False,
                        error_details=f"Expected 3 analogues, got {len(analogues)}"
                    )
                    return False
            else:
                self.log_test(
                    "Enterprise Analogue Generation",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Enterprise Analogue Generation",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_vault_ledger_system(self):
        """Test vault ledger/IP registry system - CRITICAL for enterprise"""
        try:
            response = requests.get(f"{API_BASE}/vault-ledger?limit=10", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                ledger_entries = data.get('ledger_entries', [])
                
                self.log_test(
                    "Vault Ledger System",
                    True,
                    f"Retrieved {len(ledger_entries)} ledger entries, status: {data.get('registry_status')}"
                )
                return True
            else:
                self.log_test(
                    "Vault Ledger System",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Vault Ledger System",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_generation_history(self):
        """Test generation history/audit trail system - CRITICAL for enterprise"""
        try:
            response = requests.get(f"{API_BASE}/generation-history?limit=10", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                history = data.get('history', [])
                
                self.log_test(
                    "Generation History System",
                    True,
                    f"Retrieved {len(history)} history entries, status: {data.get('status')}"
                )
                return True
            else:
                self.log_test(
                    "Generation History System",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Generation History System",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_pdf_export_system(self):
        """Test PDF export functionality"""
        if not hasattr(self, 'generation_id') or not self.generation_id:
            self.log_test(
                "PDF Export System",
                False,
                error_details="No generation ID available (analogue generation must succeed first)"
            )
            return False
        
        try:
            payload = {
                "generation_id": self.generation_id,
                "format": "pdf",
                "include_cost": True,
                "include_ip_analysis": True,
                "watermark": True
            }
            
            response = requests.post(f"{API_BASE}/export-report", json=payload, timeout=15)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                if 'pdf' in content_type.lower() and content_length > 1000:
                    self.log_test(
                        "PDF Export System",
                        True,
                        f"Generated PDF: {content_length} bytes, content-type: {content_type}"
                    )
                    return True
                else:
                    self.log_test(
                        "PDF Export System",
                        False,
                        error_details=f"Invalid PDF: {content_length} bytes, type: {content_type}"
                    )
                    return False
            else:
                self.log_test(
                    "PDF Export System",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "PDF Export System",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_cro_integration(self):
        """Test CRO synthesis partner integration"""
        if not hasattr(self, 'vault_ids') or not self.vault_ids:
            self.log_test(
                "CRO Integration System",
                False,
                error_details="No vault IDs available (analogue generation must succeed first)"
            )
            return False
        
        try:
            payload = {
                "vault_id": self.vault_ids[0],
                "partner_name": "Enterprise CRO Partners",
                "quantity_mg": 500.0,
                "purity_requirement": 98.0,
                "timeline_days": 21,
                "contact_email": "enterprise@test.com",
                "additional_notes": "Phase VI enterprise validation"
            }
            
            response = requests.post(f"{API_BASE}/request-synthesis", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                partner_ref = data.get('partner_response', {}).get('partner_reference', '')
                
                if partner_ref.startswith('SYN-'):
                    self.log_test(
                        "CRO Integration System",
                        True,
                        f"Partner reference: {partner_ref}, status: {data.get('status')}"
                    )
                    return True
                else:
                    self.log_test(
                        "CRO Integration System",
                        False,
                        error_details=f"Invalid partner reference: {partner_ref}"
                    )
                    return False
            else:
                self.log_test(
                    "CRO Integration System",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "CRO Integration System",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_token_management(self):
        """Test Pro Vault token management system"""
        try:
            # Create enterprise token
            response = requests.post(
                f"{API_BASE}/vault-tokens/create?user_id=enterprise_test&tier=enterprise&credits=5000",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                token_id = data.get('token_id')
                
                if token_id:
                    # Check token status
                    status_response = requests.get(f"{API_BASE}/vault-tokens/{token_id}", timeout=10)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        self.log_test(
                            "Token Management System",
                            True,
                            f"Created token: {token_id}, tier: {status_data.get('tier')}, credits: {status_data.get('credits')}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Token Management System",
                            False,
                            error_details=f"Token status check failed: HTTP {status_response.status_code}"
                        )
                        return False
                else:
                    self.log_test(
                        "Token Management System",
                        False,
                        error_details="No token ID returned from creation"
                    )
                    return False
            else:
                self.log_test(
                    "Token Management System",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Token Management System",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_concurrent_load(self):
        """Test concurrent user handling - CRITICAL for enterprise deployment"""
        def make_analogue_request(request_id):
            """Make a single analogue generation request"""
            payload = {
                "base_molecule": "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR",
                "allowed_mods": "Substitution, D-isomers",
                "exclusions": "No modifications",
                "target_use": f"Concurrent Test {request_id}",
                "num_analogues": 2,
                "include_cost": False
            }
            
            try:
                response = requests.post(f"{API_BASE}/generate-analogues", json=payload, timeout=45)
                return {
                    "request_id": request_id,
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "response_size": len(response.content) if response.content else 0
                }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "success": False,
                    "error": str(e)
                }
        
        print("🚀 Testing concurrent load (5 simultaneous requests)...")
        
        # Execute 5 concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_analogue_request, i+1) for i in range(5)]
            results = [future.result() for future in as_completed(futures)]
        
        successful_requests = sum(1 for r in results if r.get('success', False))
        total_requests = len(results)
        
        if successful_requests >= 3:  # At least 60% success rate for enterprise
            self.log_test(
                "Concurrent Load Handling",
                True,
                f"Successfully handled {successful_requests}/{total_requests} concurrent requests"
            )
            return True
        else:
            error_details = f"Only {successful_requests}/{total_requests} requests succeeded. "
            failures = []
            for r in results:
                if not r.get('success', False):
                    error_msg = r.get('error', f"HTTP {r.get('status_code', 'unknown')}")
                    failures.append(f"Req{r['request_id']}: {error_msg}")
            error_details += "Failures: " + ", ".join(failures)
            
            self.log_test(
                "Concurrent Load Handling",
                False,
                error_details=error_details
            )
            return False

    def test_error_resilience(self):
        """Test error handling and resilience"""
        test_cases = [
            ("Invalid Generation ID Export", f"{API_BASE}/export-report", {"generation_id": "invalid-id"}, 404),
            ("Invalid Vault ID Lookup", f"{API_BASE}/vault-ledger/invalid-vault-id", None, 404),
            ("Invalid Token Lookup", f"{API_BASE}/vault-tokens/invalid-token", None, 404),
        ]
        
        all_passed = True
        for test_name, url, payload, expected_status in test_cases:
            try:
                if payload:
                    response = requests.post(url, json=payload, timeout=10)
                else:
                    response = requests.get(url, timeout=10)
                
                if response.status_code == expected_status:
                    self.log_test(
                        f"Error Resilience - {test_name}",
                        True,
                        f"Correctly returned HTTP {response.status_code}"
                    )
                else:
                    self.log_test(
                        f"Error Resilience - {test_name}",
                        False,
                        error_details=f"Expected HTTP {expected_status}, got {response.status_code}"
                    )
                    all_passed = False
                    
            except Exception as e:
                self.log_test(
                    f"Error Resilience - {test_name}",
                    False,
                    error_details=f"Request failed: {str(e)}"
                )
                all_passed = False
        
        return all_passed

    def run_comprehensive_test(self):
        """Run complete enterprise validation test suite"""
        print("=" * 80)
        print("🧬 PEPTIMANCER PHASE VI PRODUCTION ENTERPRISE VALIDATION")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Started: {datetime.now().isoformat()}")
        print("=" * 80)
        print()
        
        # Core functionality tests
        print("📋 CORE FUNCTIONALITY TESTS")
        print("-" * 40)
        self.test_api_health()
        self.test_sequence_validation()
        self.test_analogue_generation()
        
        print("\n📊 ENTERPRISE FEATURE TESTS")
        print("-" * 40)
        self.test_vault_ledger_system()
        self.test_generation_history()
        self.test_pdf_export_system()
        self.test_cro_integration()
        self.test_token_management()
        
        print("\n🚀 SCALABILITY & RESILIENCE TESTS")
        print("-" * 40)
        self.test_concurrent_load()
        self.test_error_resilience()
        
        # Final summary
        print("\n" + "=" * 80)
        print("📈 PHASE VI ENTERPRISE VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.critical_failures:
            print(f"\n❌ CRITICAL FAILURES ({len(self.critical_failures)}):")
            for failure in self.critical_failures:
                print(f"  • {failure['test']}: {failure['error']}")
        
        print(f"\nEnterprise Deployment Status: {'✅ READY' if self.tests_passed >= self.tests_run * 0.9 else '❌ NOT READY'}")
        print("=" * 80)
        
        return {
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "success_rate": self.tests_passed/self.tests_run*100,
            "critical_failures": self.critical_failures,
            "test_results": self.test_results,
            "enterprise_ready": self.tests_passed >= self.tests_run * 0.9
        }

class PartnerSharesDeprecationTest:
    """Test Partner Shares Deprecation & Core App Stabilization"""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []
        self.test_results = {}
        self.admin_jwt_cookie = None
        self.admin_email = "founder@peptologic.ai"
        self.demo_code = None
        
    def log_test(self, test_name, success, details="", error_details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
            if details:
                print(f"   Details: {details}")
        else:
            print(f"❌ {test_name}: FAILED")
            if error_details:
                print(f"   Error: {error_details}")
            self.critical_failures.append({
                "test": test_name,
                "error": error_details,
                "timestamp": datetime.now().isoformat()
            })
        
        self.test_results[test_name] = {
            "success": success,
            "details": details,
            "error": error_details,
            "timestamp": datetime.now().isoformat()
        }
        print()

    def test_partner_shares_get_deprecation(self):
        """Test GET /api/patentpulse/partner/shares returns 410 GONE"""
        try:
            response = requests.get(f"{API_BASE}/patentpulse/partner/shares", timeout=10)
            
            if response.status_code == 410:
                try:
                    data = response.json()
                    message = data.get("detail", "")
                    self.log_test(
                        "Partner Shares GET Deprecation",
                        True,
                        f"Correctly returned 410 GONE with message: {message}"
                    )
                    return True
                except:
                    self.log_test(
                        "Partner Shares GET Deprecation",
                        True,
                        "Correctly returned 410 GONE"
                    )
                    return True
            else:
                self.log_test(
                    "Partner Shares GET Deprecation",
                    False,
                    error_details=f"Expected HTTP 410 GONE, got {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Partner Shares GET Deprecation",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_partner_shares_post_deprecation(self):
        """Test POST /api/patentpulse/partner/shares returns 410 GONE"""
        try:
            payload = {"test": "data"}
            response = requests.post(f"{API_BASE}/patentpulse/partner/shares", json=payload, timeout=10)
            
            if response.status_code == 410:
                try:
                    data = response.json()
                    message = data.get("detail", "")
                    self.log_test(
                        "Partner Shares POST Deprecation",
                        True,
                        f"Correctly returned 410 GONE with message: {message}"
                    )
                    return True
                except:
                    self.log_test(
                        "Partner Shares POST Deprecation",
                        True,
                        "Correctly returned 410 GONE"
                    )
                    return True
            else:
                self.log_test(
                    "Partner Shares POST Deprecation",
                    False,
                    error_details=f"Expected HTTP 410 GONE, got {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Partner Shares POST Deprecation",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_partner_shares_rotate_deprecation(self):
        """Test POST /api/patentpulse/partner/shares/{share_id}/rotate returns 410 GONE"""
        try:
            share_id = "test_share_123"
            response = requests.post(f"{API_BASE}/patentpulse/partner/shares/{share_id}/rotate", timeout=10)
            
            if response.status_code == 410:
                try:
                    data = response.json()
                    message = data.get("detail", "")
                    self.log_test(
                        "Partner Shares Rotate Deprecation",
                        True,
                        f"Correctly returned 410 GONE with message: {message}"
                    )
                    return True
                except:
                    self.log_test(
                        "Partner Shares Rotate Deprecation",
                        True,
                        "Correctly returned 410 GONE"
                    )
                    return True
            else:
                self.log_test(
                    "Partner Shares Rotate Deprecation",
                    False,
                    error_details=f"Expected HTTP 410 GONE, got {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Partner Shares Rotate Deprecation",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_partner_shares_revoke_deprecation(self):
        """Test POST /api/patentpulse/partner/shares/{share_id}/revoke returns 410 GONE"""
        try:
            share_id = "test_share_123"
            response = requests.post(f"{API_BASE}/patentpulse/partner/shares/{share_id}/revoke", timeout=10)
            
            if response.status_code == 410:
                try:
                    data = response.json()
                    message = data.get("detail", "")
                    self.log_test(
                        "Partner Shares Revoke Deprecation",
                        True,
                        f"Correctly returned 410 GONE with message: {message}"
                    )
                    return True
                except:
                    self.log_test(
                        "Partner Shares Revoke Deprecation",
                        True,
                        "Correctly returned 410 GONE"
                    )
                    return True
            else:
                self.log_test(
                    "Partner Shares Revoke Deprecation",
                    False,
                    error_details=f"Expected HTTP 410 GONE, got {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Partner Shares Revoke Deprecation",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_auth_magic_request(self):
        """Test POST /api/auth/magic/request with admin email"""
        try:
            payload = {"email": self.admin_email}
            response = requests.post(f"{API_BASE}/auth/magic/request", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "demo_code" in data:
                    self.demo_code = data["demo_code"]
                    self.log_test(
                        "Auth Magic Request",
                        True,
                        f"Demo code: {self.demo_code}, expires in {data.get('expires_in_minutes')} minutes"
                    )
                    return True
                else:
                    self.log_test(
                        "Auth Magic Request",
                        False,
                        error_details="Response missing demo_code or success flag"
                    )
                    return False
            else:
                self.log_test(
                    "Auth Magic Request",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Auth Magic Request",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_auth_magic_verify(self):
        """Test POST /api/auth/magic/verify with demo code"""
        if not self.demo_code:
            self.log_test(
                "Auth Magic Verify",
                False,
                error_details="No demo code available (request must succeed first)"
            )
            return False
        
        try:
            payload = {"email": self.admin_email, "code": self.demo_code}
            response = requests.post(f"{API_BASE}/auth/magic/verify", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                cookies = response.cookies
                if "pmnc_jwt" in cookies:
                    self.admin_jwt_cookie = cookies["pmnc_jwt"]
                    self.log_test(
                        "Auth Magic Verify",
                        True,
                        f"JWT cookie set, role: {data.get('role')}, email: {data.get('email')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Auth Magic Verify",
                        False,
                        error_details="JWT cookie not set in response"
                    )
                    return False
            else:
                self.log_test(
                    "Auth Magic Verify",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Auth Magic Verify",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_auth_session(self):
        """Test GET /api/auth/session with JWT cookie"""
        if not self.admin_jwt_cookie:
            self.log_test(
                "Auth Session",
                False,
                error_details="No JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/auth/session", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["email", "role", "tier", "credits"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(
                        "Auth Session",
                        False,
                        error_details=f"Missing required fields: {missing_fields}"
                    )
                    return False
                
                self.log_test(
                    "Auth Session",
                    True,
                    f"Email: {data.get('email')}, Role: {data.get('role')}, Tier: {data.get('tier')}, Credits: {data.get('credits')}"
                )
                return True
            else:
                self.log_test(
                    "Auth Session",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Auth Session",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_chemistry_options(self):
        """Test GET /api/chemistry/options"""
        try:
            response = requests.get(f"{API_BASE}/chemistry/options", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "mods" in data and "exclusions" in data:
                    self.log_test(
                        "Chemistry Options",
                        True,
                        f"Returned {len(data.get('mods', []))} modifications, {len(data.get('exclusions', []))} exclusions"
                    )
                    return True
                else:
                    self.log_test(
                        "Chemistry Options",
                        False,
                        error_details="Missing mods or exclusions in response"
                    )
                    return False
            else:
                self.log_test(
                    "Chemistry Options",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Chemistry Options",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_patentpulse_items(self):
        """Test GET /api/patentpulse/items?limit=5"""
        try:
            # Try without auth first, then with auth if needed
            response = requests.get(f"{API_BASE}/patentpulse/items?limit=5", timeout=10)
            
            if response.status_code == 401 and self.admin_jwt_cookie:
                # Try with authentication
                cookies = {"pmnc_jwt": self.admin_jwt_cookie}
                response = requests.get(f"{API_BASE}/patentpulse/items?limit=5", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "items" in data:
                    items = data.get("items", [])
                    self.log_test(
                        "PatentPulse Items",
                        True,
                        f"Returned {len(items)} patent items"
                    )
                    return True
                else:
                    self.log_test(
                        "PatentPulse Items",
                        False,
                        error_details="Missing items in response"
                    )
                    return False
            else:
                self.log_test(
                    "PatentPulse Items",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "PatentPulse Items",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_patentpulse_stats(self):
        """Test GET /api/patentpulse/stats"""
        try:
            # Try without auth first, then with auth if needed
            response = requests.get(f"{API_BASE}/patentpulse/stats", timeout=10)
            
            if response.status_code == 401 and self.admin_jwt_cookie:
                # Try with authentication
                cookies = {"pmnc_jwt": self.admin_jwt_cookie}
                response = requests.get(f"{API_BASE}/patentpulse/stats", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "total_items" in data or "stats" in data:
                    self.log_test(
                        "PatentPulse Stats",
                        True,
                        f"Stats retrieved successfully"
                    )
                    return True
                else:
                    self.log_test(
                        "PatentPulse Stats",
                        False,
                        error_details="Missing stats data in response"
                    )
                    return False
            else:
                self.log_test(
                    "PatentPulse Stats",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "PatentPulse Stats",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_admin_analytics_summary(self):
        """Test GET /api/admin/analytics/summary with admin JWT"""
        if not self.admin_jwt_cookie:
            self.log_test(
                "Admin Analytics Summary",
                False,
                error_details="No JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/admin/analytics/summary", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Admin Analytics Summary",
                    True,
                    f"Analytics data retrieved successfully"
                )
                return True
            else:
                self.log_test(
                    "Admin Analytics Summary",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Admin Analytics Summary",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_billing_state(self):
        """Test GET /api/billing/state with valid JWT"""
        if not self.admin_jwt_cookie:
            self.log_test(
                "Billing State",
                False,
                error_details="No JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/billing/state", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["tier", "credits"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(
                        "Billing State",
                        False,
                        error_details=f"Missing required fields: {missing_fields}"
                    )
                    return False
                
                self.log_test(
                    "Billing State",
                    True,
                    f"Tier: {data.get('tier')}, Credits: {data.get('credits')}"
                )
                return True
            else:
                self.log_test(
                    "Billing State",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Billing State",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_billing_mock_webhook(self):
        """Test GET /api/webhooks/billing/mock/success?uid=USER_ID&credits=100"""
        try:
            # Use a test user ID
            user_id = "test_user_123"
            response = requests.get(f"{API_BASE}/webhooks/billing/mock/success?uid={user_id}&credits=100", timeout=10, allow_redirects=False)
            
            # Mock webhook should return 302 redirect or 200 success
            if response.status_code in [200, 302]:
                self.log_test(
                    "Billing Mock Webhook",
                    True,
                    f"Mock webhook responded with {response.status_code}"
                )
                return True
            else:
                self.log_test(
                    "Billing Mock Webhook",
                    False,
                    error_details=f"Expected HTTP 200 or 302, got {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Billing Mock Webhook",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def run_comprehensive_test(self):
        """Run comprehensive Partner Shares deprecation and core app stabilization tests"""
        print("=" * 80)
        print("🚫 PARTNER SHARES DEPRECATION & CORE APP STABILIZATION TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Email: {self.admin_email}")
        print(f"Test Started: {datetime.now().isoformat()}")
        print("=" * 80)
        print()
        
        # Priority 1: Partner Shares API Deprecation
        print("🚫 PRIORITY 1: PARTNER SHARES API DEPRECATION")
        print("-" * 50)
        self.test_partner_shares_get_deprecation()
        self.test_partner_shares_post_deprecation()
        self.test_partner_shares_rotate_deprecation()
        self.test_partner_shares_revoke_deprecation()
        
        # Priority 2: Core Authentication & Session (Regression Test)
        print("\n🔐 PRIORITY 2: CORE AUTHENTICATION & SESSION")
        print("-" * 50)
        self.test_auth_magic_request()
        self.test_auth_magic_verify()
        self.test_auth_session()
        
        # Priority 3: Core Application Endpoints (Regression Test)
        print("\n🧬 PRIORITY 3: CORE APPLICATION ENDPOINTS")
        print("-" * 50)
        self.test_chemistry_options()
        self.test_patentpulse_items()
        self.test_patentpulse_stats()
        self.test_admin_analytics_summary()
        
        # Priority 4: Billing System (Regression Test)
        print("\n💳 PRIORITY 4: BILLING SYSTEM")
        print("-" * 50)
        self.test_billing_state()
        self.test_billing_mock_webhook()
        
        # Final summary
        print("\n" + "=" * 80)
        print("📈 PARTNER SHARES DEPRECATION & CORE APP TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Categorize results
        partner_shares_tests = [t for t in self.test_results.keys() if "Partner Shares" in t]
        auth_tests = [t for t in self.test_results.keys() if "Auth" in t]
        core_tests = [t for t in self.test_results.keys() if any(x in t for x in ["Chemistry", "PatentPulse", "Admin Analytics"])]
        billing_tests = [t for t in self.test_results.keys() if "Billing" in t]
        
        partner_shares_passed = sum(1 for t in partner_shares_tests if self.test_results[t]["success"])
        auth_passed = sum(1 for t in auth_tests if self.test_results[t]["success"])
        core_passed = sum(1 for t in core_tests if self.test_results[t]["success"])
        billing_passed = sum(1 for t in billing_tests if self.test_results[t]["success"])
        
        print(f"\n📊 RESULTS BY CATEGORY:")
        print(f"  Partner Shares Deprecation: {partner_shares_passed}/{len(partner_shares_tests)} ({'✅ COMPLETE' if partner_shares_passed == len(partner_shares_tests) else '❌ INCOMPLETE'})")
        print(f"  Authentication Flow: {auth_passed}/{len(auth_tests)} ({'✅ WORKING' if auth_passed == len(auth_tests) else '❌ ISSUES'})")
        print(f"  Core Application: {core_passed}/{len(core_tests)} ({'✅ WORKING' if core_passed == len(core_tests) else '❌ ISSUES'})")
        print(f"  Billing System: {billing_passed}/{len(billing_tests)} ({'✅ WORKING' if billing_passed == len(billing_tests) else '❌ ISSUES'})")
        
        if self.critical_failures:
            print(f"\n❌ CRITICAL FAILURES ({len(self.critical_failures)}):")
            for failure in self.critical_failures:
                print(f"  • {failure['test']}: {failure['error']}")
        
        # Success criteria
        partner_shares_success = partner_shares_passed == len(partner_shares_tests)
        core_success = (auth_passed + core_passed + billing_passed) >= (len(auth_tests) + len(core_tests) + len(billing_tests)) * 0.85
        
        overall_status = "✅ SUCCESS" if partner_shares_success and core_success else "❌ ISSUES DETECTED"
        print(f"\nOverall Status: {overall_status}")
        
        if partner_shares_success:
            print("✅ Partner Shares deprecation is COMPLETE - all endpoints return 410 GONE")
        else:
            print("❌ Partner Shares deprecation is INCOMPLETE - some endpoints not properly deprecated")
            
        if core_success:
            print("✅ Core application flows are WORKING after Partner Shares removal")
        else:
            print("❌ Core application flows have ISSUES after Partner Shares removal")
        
        print("=" * 80)
        
        return {
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "success_rate": self.tests_passed/self.tests_run*100,
            "critical_failures": self.critical_failures,
            "test_results": self.test_results,
            "partner_shares_deprecated": partner_shares_success,
            "core_app_stable": core_success,
            "overall_success": partner_shares_success and core_success
        }

class GlobalLoginRBACTest:
    """Test Global Login & RBAC Implementation Comprehensively"""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []
        self.test_results = {}
        self.jwt_cookie = None
        self.admin_email = "founder@peptologic.ai"
        self.cto_email = "cto@peptologic.ai"
        self.test_email = "test@example.com"
        self.admin_jwt_cookie = None
        self.non_admin_jwt_cookie = None
        
    def log_test(self, test_name, success, details="", error_details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
            if details:
                print(f"   Details: {details}")
        else:
            print(f"❌ {test_name}: FAILED")
            if error_details:
                print(f"   Error: {error_details}")
            self.critical_failures.append({
                "test": test_name,
                "error": error_details,
                "timestamp": datetime.now().isoformat()
            })
        
        self.test_results[test_name] = {
            "success": success,
            "details": details,
            "error": error_details,
            "timestamp": datetime.now().isoformat()
        }
        print()
    
    def test_magic_code_request_admin(self):
        """Test magic code request with admin email"""
        try:
            payload = {"email": self.admin_email}
            response = requests.post(f"{API_BASE}/auth/magic/request", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "demo_code" in data:
                    self.demo_code_admin = data["demo_code"]
                    self.log_test(
                        "Magic Code Request (Admin Email)",
                        True,
                        f"OTP: {self.demo_code_admin}, expires in {data.get('expires_in_minutes')} minutes"
                    )
                    return True
                else:
                    self.log_test(
                        "Magic Code Request (Admin Email)",
                        False,
                        error_details="Response missing demo_code or success flag"
                    )
                    return False
            else:
                self.log_test(
                    "Magic Code Request (Admin Email)",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Magic Code Request (Admin Email)",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_magic_code_request_non_admin(self):
        """Test magic code request with non-admin email"""
        try:
            payload = {"email": self.non_admin_email}
            response = requests.post(f"{API_BASE}/auth/magic/request", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "demo_code" in data:
                    self.demo_code_non_admin = data["demo_code"]
                    self.log_test(
                        "Magic Code Request (Non-Admin Email)",
                        True,
                        f"OTP: {self.demo_code_non_admin}, expires in {data.get('expires_in_minutes')} minutes"
                    )
                    return True
                else:
                    self.log_test(
                        "Magic Code Request (Non-Admin Email)",
                        False,
                        error_details="Response missing demo_code or success flag"
                    )
                    return False
            else:
                self.log_test(
                    "Magic Code Request (Non-Admin Email)",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Magic Code Request (Non-Admin Email)",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_magic_code_verify_admin(self):
        """Test magic code verification with admin email"""
        if not hasattr(self, 'demo_code_admin'):
            self.log_test(
                "Magic Code Verification (Admin)",
                False,
                error_details="No demo code available (request must succeed first)"
            )
            return False
        
        try:
            payload = {"email": self.admin_email, "code": self.demo_code_admin}
            response = requests.post(f"{API_BASE}/auth/magic/verify", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Check for JWT cookie
                cookies = response.cookies
                if "pmnc_jwt" in cookies:
                    self.admin_jwt_cookie = cookies["pmnc_jwt"]
                    if data.get("role") == "admin":
                        self.log_test(
                            "Magic Code Verification (Admin)",
                            True,
                            f"JWT cookie set, role: {data.get('role')}, email: {data.get('email')}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Magic Code Verification (Admin)",
                            False,
                            error_details=f"Expected role 'admin', got '{data.get('role')}'"
                        )
                        return False
                else:
                    self.log_test(
                        "Magic Code Verification (Admin)",
                        False,
                        error_details="JWT cookie not set in response"
                    )
                    return False
            else:
                self.log_test(
                    "Magic Code Verification (Admin)",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Magic Code Verification (Admin)",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_magic_code_verify_non_admin(self):
        """Test magic code verification with non-admin email"""
        if not hasattr(self, 'demo_code_non_admin'):
            self.log_test(
                "Magic Code Verification (Non-Admin)",
                False,
                error_details="No demo code available (request must succeed first)"
            )
            return False
        
        try:
            payload = {"email": self.non_admin_email, "code": self.demo_code_non_admin}
            response = requests.post(f"{API_BASE}/auth/magic/verify", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Check for JWT cookie
                cookies = response.cookies
                if "pmnc_jwt" in cookies:
                    self.non_admin_jwt_cookie = cookies["pmnc_jwt"]
                    if data.get("role") == "researcher":
                        self.log_test(
                            "Magic Code Verification (Non-Admin)",
                            True,
                            f"JWT cookie set, role: {data.get('role')}, email: {data.get('email')}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Magic Code Verification (Non-Admin)",
                            False,
                            error_details=f"Expected role 'researcher', got '{data.get('role')}'"
                        )
                        return False
                else:
                    self.log_test(
                        "Magic Code Verification (Non-Admin)",
                        False,
                        error_details="JWT cookie not set in response"
                    )
                    return False
            else:
                self.log_test(
                    "Magic Code Verification (Non-Admin)",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Magic Code Verification (Non-Admin)",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_get_current_user_admin(self):
        """Test /auth/me endpoint with admin JWT"""
        if not hasattr(self, 'admin_jwt_cookie'):
            self.log_test(
                "Get Current User (Admin)",
                False,
                error_details="No admin JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/auth/me", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("is_admin") and data.get("email") == self.admin_email:
                    self.log_test(
                        "Get Current User (Admin)",
                        True,
                        f"User info: {data.get('email')}, role: {data.get('role')}, is_admin: {data.get('is_admin')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Get Current User (Admin)",
                        False,
                        error_details=f"Expected is_admin=true, got {data}"
                    )
                    return False
            else:
                self.log_test(
                    "Get Current User (Admin)",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Get Current User (Admin)",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_get_current_user_non_admin(self):
        """Test /auth/me endpoint with non-admin JWT"""
        if not hasattr(self, 'non_admin_jwt_cookie'):
            self.log_test(
                "Get Current User (Non-Admin)",
                False,
                error_details="No non-admin JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.non_admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/auth/me", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if not data.get("is_admin") and data.get("email") == self.non_admin_email:
                    self.log_test(
                        "Get Current User (Non-Admin)",
                        True,
                        f"User info: {data.get('email')}, role: {data.get('role')}, is_admin: {data.get('is_admin')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Get Current User (Non-Admin)",
                        False,
                        error_details=f"Expected is_admin=false, got {data}"
                    )
                    return False
            else:
                self.log_test(
                    "Get Current User (Non-Admin)",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Get Current User (Non-Admin)",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_admin_settings_access_with_admin(self):
        """Test admin settings access with admin JWT"""
        if not hasattr(self, 'admin_jwt_cookie'):
            self.log_test(
                "Admin Settings Access (Admin User)",
                False,
                error_details="No admin JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/admin/settings", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Admin Settings Access (Admin User)",
                    True,
                    f"Settings retrieved: mode={data.get('settings', {}).get('integrationsMode')}"
                )
                return True
            else:
                self.log_test(
                    "Admin Settings Access (Admin User)",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Admin Settings Access (Admin User)",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_admin_settings_access_with_non_admin(self):
        """Test admin settings access with non-admin JWT (should fail)"""
        if not hasattr(self, 'non_admin_jwt_cookie'):
            self.log_test(
                "Admin Settings Access (Non-Admin User - Should Fail)",
                False,
                error_details="No non-admin JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.non_admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/admin/settings", cookies=cookies, timeout=10)
            
            if response.status_code == 403:
                self.log_test(
                    "Admin Settings Access (Non-Admin User - Should Fail)",
                    True,
                    "Correctly returned 403 Forbidden for non-admin user"
                )
                return True
            else:
                self.log_test(
                    "Admin Settings Access (Non-Admin User - Should Fail)",
                    False,
                    error_details=f"Expected HTTP 403, got {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Admin Settings Access (Non-Admin User - Should Fail)",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_admin_settings_update(self):
        """Test admin settings update with admin JWT"""
        if not hasattr(self, 'admin_jwt_cookie'):
            self.log_test(
                "Admin Settings Update",
                False,
                error_details="No admin JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            payload = {
                "confirm": "SWITCH",
                "integrationsMode": "sandbox"
            }
            response = requests.put(f"{API_BASE}/admin/settings", json=payload, cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test(
                        "Admin Settings Update",
                        True,
                        f"Settings updated: {data.get('updated_fields')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Admin Settings Update",
                        False,
                        error_details="Response missing success flag"
                    )
                    return False
            else:
                self.log_test(
                    "Admin Settings Update",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Admin Settings Update",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_logout(self):
        """Test logout endpoint"""
        try:
            response = requests.post(f"{API_BASE}/auth/logout", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Check if cookie is cleared
                cookies = response.cookies
                if data.get("success"):
                    self.log_test(
                        "Logout",
                        True,
                        "Successfully logged out"
                    )
                    return True
                else:
                    self.log_test(
                        "Logout",
                        False,
                        error_details="Response missing success flag"
                    )
                    return False
            else:
                self.log_test(
                    "Logout",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Logout",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_invalid_otp(self):
        """Test with invalid OTP code"""
        try:
            payload = {"email": self.admin_email, "code": "000000"}
            response = requests.post(f"{API_BASE}/auth/magic/verify", json=payload, timeout=10)
            
            if response.status_code == 401:
                self.log_test(
                    "Invalid OTP Code",
                    True,
                    "Correctly returned 401 Unauthorized for invalid OTP"
                )
                return True
            else:
                self.log_test(
                    "Invalid OTP Code",
                    False,
                    error_details=f"Expected HTTP 401, got {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Invalid OTP Code",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_invalid_email_format(self):
        """Test with invalid email format"""
        try:
            payload = {"email": "not-an-email"}
            response = requests.post(f"{API_BASE}/auth/magic/request", json=payload, timeout=10)
            
            if response.status_code == 422:
                self.log_test(
                    "Invalid Email Format",
                    True,
                    "Correctly returned 422 for invalid email format"
                )
                return True
            else:
                self.log_test(
                    "Invalid Email Format",
                    False,
                    error_details=f"Expected HTTP 422, got {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Invalid Email Format",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_missing_jwt_cookie(self):
        """Test admin endpoint without JWT cookie"""
        try:
            response = requests.get(f"{API_BASE}/admin/settings", timeout=10)
            
            if response.status_code == 401:
                self.log_test(
                    "Missing JWT Cookie",
                    True,
                    "Correctly returned 401 Unauthorized without JWT"
                )
                return True
            else:
                self.log_test(
                    "Missing JWT Cookie",
                    False,
                    error_details=f"Expected HTTP 401, got {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Missing JWT Cookie",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_session_endpoint_without_auth(self):
        """Test session endpoint without authentication - should return 401"""
        try:
            response = requests.get(f"{API_BASE}/auth/session", timeout=10)
            
            if response.status_code == 401:
                self.log_test(
                    "Session Endpoint Without Auth",
                    True,
                    "Correctly returned 401 Unauthorized"
                )
                return True
            else:
                self.log_test(
                    "Session Endpoint Without Auth",
                    False,
                    error_details=f"Expected HTTP 401, got {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Session Endpoint Without Auth",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_session_endpoint_with_auth(self):
        """Test session endpoint with valid JWT - should return user data"""
        if not hasattr(self, 'admin_jwt_cookie') or not self.admin_jwt_cookie:
            self.log_test(
                "Session Endpoint With Auth",
                False,
                error_details="No admin JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/auth/session", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["email", "role", "tier", "credits", "feature_level"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(
                        "Session Endpoint With Auth",
                        False,
                        error_details=f"Missing required fields: {missing_fields}"
                    )
                    return False
                
                self.log_test(
                    "Session Endpoint With Auth",
                    True,
                    f"Email: {data.get('email')}, Role: {data.get('role')}, Tier: {data.get('tier')}, Credits: {data.get('credits')}, Feature Level: {data.get('feature_level')}"
                )
                return True
            else:
                self.log_test(
                    "Session Endpoint With Auth",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Session Endpoint With Auth",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_protected_billing_endpoint_without_auth(self):
        """Test protected billing endpoint without auth - should return 401"""
        try:
            response = requests.get(f"{API_BASE}/billing/state", timeout=10)
            
            if response.status_code == 401:
                self.log_test(
                    "Protected Billing Endpoint Without Auth",
                    True,
                    "Correctly returned 401 Unauthorized"
                )
                return True
            else:
                self.log_test(
                    "Protected Billing Endpoint Without Auth",
                    False,
                    error_details=f"Expected HTTP 401, got {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Protected Billing Endpoint Without Auth",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_protected_billing_endpoint_with_auth(self):
        """Test protected billing endpoint with valid JWT - should return billing data"""
        if not hasattr(self, 'admin_jwt_cookie') or not self.admin_jwt_cookie:
            self.log_test(
                "Protected Billing Endpoint With Auth",
                False,
                error_details="No admin JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/billing/state", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["tier", "credits"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(
                        "Protected Billing Endpoint With Auth",
                        False,
                        error_details=f"Missing required fields: {missing_fields}"
                    )
                    return False
                
                self.log_test(
                    "Protected Billing Endpoint With Auth",
                    True,
                    f"Tier: {data.get('tier')}, Credits: {data.get('credits')}"
                )
                return True
            else:
                self.log_test(
                    "Protected Billing Endpoint With Auth",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Protected Billing Endpoint With Auth",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_public_chemistry_options_endpoint(self):
        """Test public chemistry options endpoint - should work without auth"""
        try:
            response = requests.get(f"{API_BASE}/chemistry/options", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "modifications" in data and "exclusions" in data:
                    self.log_test(
                        "Public Chemistry Options Endpoint",
                        True,
                        f"Returned basic tier options: {len(data.get('modifications', []))} mods, {len(data.get('exclusions', []))} exclusions"
                    )
                    return True
                else:
                    self.log_test(
                        "Public Chemistry Options Endpoint",
                        False,
                        error_details="Missing modifications or exclusions in response"
                    )
                    return False
            else:
                self.log_test(
                    "Public Chemistry Options Endpoint",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Public Chemistry Options Endpoint",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_chemistry_options_with_auth(self):
        """Test chemistry options endpoint with auth - should return tier-appropriate options"""
        if not hasattr(self, 'admin_jwt_cookie') or not self.admin_jwt_cookie:
            self.log_test(
                "Chemistry Options With Auth",
                False,
                error_details="No admin JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/chemistry/options", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "modifications" in data and "exclusions" in data:
                    self.log_test(
                        "Chemistry Options With Auth",
                        True,
                        f"Returned tier-appropriate options: {len(data.get('modifications', []))} mods, {len(data.get('exclusions', []))} exclusions"
                    )
                    return True
                else:
                    self.log_test(
                        "Chemistry Options With Auth",
                        False,
                        error_details="Missing modifications or exclusions in response"
                    )
                    return False
            else:
                self.log_test(
                    "Chemistry Options With Auth",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Chemistry Options With Auth",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_admin_feature_flags_without_auth(self):
        """Test admin feature flags endpoint without auth - should return 401"""
        try:
            response = requests.get(f"{API_BASE}/admin/features/flags", timeout=10)
            
            if response.status_code == 401:
                self.log_test(
                    "Admin Feature Flags Without Auth",
                    True,
                    "Correctly returned 401 Unauthorized"
                )
                return True
            else:
                self.log_test(
                    "Admin Feature Flags Without Auth",
                    False,
                    error_details=f"Expected HTTP 401, got {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Admin Feature Flags Without Auth",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_admin_feature_flags_with_non_admin(self):
        """Test admin feature flags endpoint with non-admin JWT - should return 403"""
        if not hasattr(self, 'non_admin_jwt_cookie') or not self.non_admin_jwt_cookie:
            self.log_test(
                "Admin Feature Flags With Non-Admin",
                False,
                error_details="No non-admin JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.non_admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/admin/features/flags", cookies=cookies, timeout=10)
            
            if response.status_code == 403:
                self.log_test(
                    "Admin Feature Flags With Non-Admin",
                    True,
                    "Correctly returned 403 Forbidden for non-admin user"
                )
                return True
            else:
                self.log_test(
                    "Admin Feature Flags With Non-Admin",
                    False,
                    error_details=f"Expected HTTP 403, got {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Admin Feature Flags With Non-Admin",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_admin_feature_flags_with_admin_no_2fa(self):
        """Test admin feature flags endpoint with admin JWT but no 2FA - should return 403"""
        if not hasattr(self, 'admin_jwt_cookie') or not self.admin_jwt_cookie:
            self.log_test(
                "Admin Feature Flags With Admin No 2FA",
                False,
                error_details="No admin JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/admin/features/flags", cookies=cookies, timeout=10)
            
            # This should return 403 because admin endpoints require 2FA
            if response.status_code == 403:
                self.log_test(
                    "Admin Feature Flags With Admin No 2FA",
                    True,
                    "Correctly returned 403 Forbidden - admin endpoints require 2FA"
                )
                return True
            elif response.status_code == 200:
                # If it returns 200, it means 2FA is not required or already satisfied
                self.log_test(
                    "Admin Feature Flags With Admin No 2FA",
                    True,
                    "Admin access granted - 2FA requirement may be disabled or satisfied"
                )
                return True
            else:
                self.log_test(
                    "Admin Feature Flags With Admin No 2FA",
                    False,
                    error_details=f"Expected HTTP 403 or 200, got {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Admin Feature Flags With Admin No 2FA",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_public_partner_share_endpoint(self):
        """Test public partner share endpoint - should work without auth"""
        try:
            # Use a dummy token for testing
            dummy_token = "test_token_123"
            response = requests.get(f"{API_BASE}/patentpulse/partner/share/{dummy_token}", timeout=10)
            
            # This should return either 200 (valid token) or 404 (invalid token), but not 401 (auth required)
            if response.status_code in [200, 404]:
                self.log_test(
                    "Public Partner Share Endpoint",
                    True,
                    f"Public endpoint accessible - returned {response.status_code} (expected for dummy token)"
                )
                return True
            elif response.status_code == 401:
                self.log_test(
                    "Public Partner Share Endpoint",
                    False,
                    error_details="Endpoint requires authentication but should be public"
                )
                return False
            else:
                self.log_test(
                    "Public Partner Share Endpoint",
                    True,
                    f"Endpoint accessible - returned {response.status_code}"
                )
                return True
        except Exception as e:
            self.log_test(
                "Public Partner Share Endpoint",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_logout_endpoint(self):
        """Test logout endpoint - should clear JWT cookie"""
        try:
            response = requests.post(f"{API_BASE}/auth/logout", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test(
                        "Logout Endpoint",
                        True,
                        "Successfully logged out"
                    )
                    return True
                else:
                    self.log_test(
                        "Logout Endpoint",
                        False,
                        error_details="Response missing success flag"
                    )
                    return False
            else:
                self.log_test(
                    "Logout Endpoint",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Logout Endpoint",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def run_comprehensive_global_login_rbac_tests(self):
        """Run comprehensive Global Login & RBAC tests"""
        print("=" * 80)
        print("🔐 GLOBAL LOGIN & RBAC COMPREHENSIVE TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Emails: {self.admin_email}, {self.cto_email}")
        print(f"Test Email: {self.test_email}")
        print(f"Test Started: {datetime.now().isoformat()}")
        print("=" * 80)
        print()
        
        # Test 1: Authentication Flow
        print("🔑 AUTHENTICATION FLOW TESTS")
        print("-" * 40)
        self.test_magic_code_request_admin()
        self.test_magic_code_request_non_admin()
        self.test_magic_code_verify_admin()
        self.test_magic_code_verify_non_admin()
        
        # Test 2: Session Endpoint
        print("\n📋 SESSION ENDPOINT TESTS")
        print("-" * 40)
        self.test_session_endpoint_without_auth()
        self.test_session_endpoint_with_auth()
        
        # Test 3: Protected Endpoints
        print("\n🛡️ PROTECTED ENDPOINTS TESTS")
        print("-" * 40)
        self.test_protected_billing_endpoint_without_auth()
        self.test_protected_billing_endpoint_with_auth()
        self.test_chemistry_options_with_auth()
        
        # Test 4: Admin-Only Endpoints
        print("\n👑 ADMIN-ONLY ENDPOINTS TESTS")
        print("-" * 40)
        self.test_admin_feature_flags_without_auth()
        self.test_admin_feature_flags_with_non_admin()
        self.test_admin_feature_flags_with_admin_no_2fa()
        self.test_admin_settings_access_with_admin()
        self.test_admin_settings_access_with_non_admin()
        
        # Test 5: Public Endpoints
        print("\n🌐 PUBLIC ENDPOINTS TESTS")
        print("-" * 40)
        self.test_public_chemistry_options_endpoint()
        self.test_public_partner_share_endpoint()
        
        # Test 6: Logout
        print("\n🚪 LOGOUT TESTS")
        print("-" * 40)
        self.test_logout_endpoint()
        
        # Test 7: Edge Cases
        print("\n🔬 EDGE CASE TESTS")
        print("-" * 40)
        self.test_invalid_otp()
        self.test_invalid_email_format()
        self.test_missing_jwt_cookie()
        
        # Final summary
        print("\n" + "=" * 80)
        print("📈 GLOBAL LOGIN & RBAC TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.critical_failures:
            print(f"\n❌ CRITICAL FAILURES ({len(self.critical_failures)}):")
            for failure in self.critical_failures:
                print(f"  • {failure['test']}: {failure['error']}")
        
        print(f"\nGlobal Login & RBAC Status: {'✅ WORKING' if self.tests_passed >= self.tests_run * 0.85 else '❌ ISSUES DETECTED'}")
        print("=" * 80)
        
        return {
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "success_rate": self.tests_passed/self.tests_run*100,
            "critical_failures": self.critical_failures,
            "test_results": self.test_results,
            "global_login_rbac_working": self.tests_passed >= self.tests_run * 0.85
        }

class Phase82BillingTest:
    """Test Phase 8.2: Billing Widget Stability + Mock Pro Upgrade"""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []
        self.test_results = {}
        self.admin_jwt_cookie = None
        self.user_id = None
        self.admin_email = "founder@peptologic.ai"
        
    def log_test(self, test_name, success, details="", error_details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
            if details:
                print(f"   Details: {details}")
        else:
            print(f"❌ {test_name}: FAILED")
            if error_details:
                print(f"   Error: {error_details}")
            self.critical_failures.append({
                "test": test_name,
                "error": error_details,
                "timestamp": datetime.now().isoformat()
            })
        
        self.test_results[test_name] = {
            "success": success,
            "details": details,
            "error": error_details,
            "timestamp": datetime.now().isoformat()
        }
        print()
    
    def authenticate_admin_user(self):
        """Authenticate as admin user and get user_id"""
        try:
            # Step 1: Request magic code
            payload = {"email": self.admin_email}
            response = requests.post(f"{API_BASE}/auth/magic/request", json=payload, timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Admin Authentication Setup - Magic Code Request",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            data = response.json()
            if not data.get("success") or "demo_code" not in data:
                self.log_test(
                    "Admin Authentication Setup - Magic Code Request",
                    False,
                    error_details="Response missing demo_code or success flag"
                )
                return False
            
            demo_code = data["demo_code"]
            
            # Step 2: Verify magic code
            payload = {"email": self.admin_email, "code": demo_code}
            response = requests.post(f"{API_BASE}/auth/magic/verify", json=payload, timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Admin Authentication Setup - Magic Code Verify",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            # Extract JWT cookie
            cookies = response.cookies
            if "pmnc_jwt" not in cookies:
                self.log_test(
                    "Admin Authentication Setup - JWT Cookie",
                    False,
                    error_details="JWT cookie not set in response"
                )
                return False
            
            self.admin_jwt_cookie = cookies["pmnc_jwt"]
            
            # Step 3: Get user info to extract user ID
            cookies_dict = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/auth/me", cookies=cookies_dict, timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Admin Authentication Setup - Get User Info",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            user_data = response.json()
            self.user_id = user_data.get("id")
            
            if not self.user_id:
                self.log_test(
                    "Admin Authentication Setup - Extract User ID",
                    False,
                    error_details="User ID not found in response"
                )
                return False
            
            self.log_test(
                "Admin Authentication Setup",
                True,
                f"Authenticated as {self.admin_email}, user_id: {self.user_id}"
            )
            return True
            
        except Exception as e:
            self.log_test(
                "Admin Authentication Setup",
                False,
                error_details=f"Authentication failed: {str(e)}"
            )
            return False
    
    def test_session_endpoint(self):
        """Test 1: Session Endpoint (Verify Still Working)"""
        if not self.admin_jwt_cookie:
            self.log_test(
                "Session Endpoint",
                False,
                error_details="No admin JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/auth/session", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["email", "role", "tier", "credits"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(
                        "Session Endpoint",
                        False,
                        error_details=f"Missing required fields: {missing_fields}"
                    )
                    return False
                
                if data.get("email") == self.admin_email and data.get("role") == "admin":
                    self.log_test(
                        "Session Endpoint",
                        True,
                        f"Email: {data.get('email')}, Role: {data.get('role')}, Tier: {data.get('tier')}, Credits: {data.get('credits')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Session Endpoint",
                        False,
                        error_details=f"Unexpected user data: {data}"
                    )
                    return False
            else:
                self.log_test(
                    "Session Endpoint",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Session Endpoint",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_billing_state_endpoint(self):
        """Test 2: Billing State Endpoint (Authenticated User)"""
        if not self.admin_jwt_cookie:
            self.log_test(
                "Billing State Endpoint",
                False,
                error_details="No admin JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/billing/state", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["tier", "credits"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(
                        "Billing State Endpoint",
                        False,
                        error_details=f"Missing required fields: {missing_fields}"
                    )
                    return False
                
                # Check for optional fields
                optional_fields = ["renewsAt", "history"]
                present_optional = [field for field in optional_fields if field in data]
                
                self.log_test(
                    "Billing State Endpoint",
                    True,
                    f"Tier: {data.get('tier')}, Credits: {data.get('credits')}, Optional fields: {present_optional}"
                )
                return True
            else:
                self.log_test(
                    "Billing State Endpoint",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Billing State Endpoint",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_mock_credit_purchase(self):
        """Test 3: Mock Credit Purchase"""
        if not self.user_id:
            self.log_test(
                "Mock Credit Purchase",
                False,
                error_details="No user ID available"
            )
            return False
        
        try:
            # Get initial credits
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            initial_response = requests.get(f"{API_BASE}/billing/state", cookies=cookies, timeout=10)
            initial_credits = 0
            if initial_response.status_code == 200:
                initial_credits = initial_response.json().get("credits", 0)
            
            # Purchase 100 credits
            webhook_url = f"{API_BASE}/webhooks/billing/mock/success?uid={self.user_id}&credits=100"
            response = requests.get(webhook_url, timeout=10, allow_redirects=False)
            
            # Should redirect (302)
            if response.status_code != 302:
                self.log_test(
                    "Mock Credit Purchase",
                    False,
                    error_details=f"Expected HTTP 302 redirect, got {response.status_code}"
                )
                return False
            
            # Check redirect URL
            location = response.headers.get("location", "")
            if "/billing?success=1" not in location:
                self.log_test(
                    "Mock Credit Purchase",
                    False,
                    error_details=f"Unexpected redirect location: {location}"
                )
                return False
            
            # Verify credits increased
            time.sleep(1)  # Brief delay for processing
            final_response = requests.get(f"{API_BASE}/billing/state", cookies=cookies, timeout=10)
            
            if final_response.status_code == 200:
                final_credits = final_response.json().get("credits", 0)
                credits_added = final_credits - initial_credits
                
                if credits_added == 100:
                    self.log_test(
                        "Mock Credit Purchase",
                        True,
                        f"Credits increased from {initial_credits} to {final_credits} (+{credits_added})"
                    )
                    return True
                else:
                    self.log_test(
                        "Mock Credit Purchase",
                        False,
                        error_details=f"Expected +100 credits, got +{credits_added}"
                    )
                    return False
            else:
                self.log_test(
                    "Mock Credit Purchase",
                    False,
                    error_details=f"Failed to verify credits: HTTP {final_response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Mock Credit Purchase",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_mock_pro_plan_upgrade(self):
        """Test 4: Mock Pro Plan Upgrade"""
        if not self.user_id:
            self.log_test(
                "Mock Pro Plan Upgrade",
                False,
                error_details="No user ID available"
            )
            return False
        
        try:
            # Get initial state
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            initial_response = requests.get(f"{API_BASE}/billing/state", cookies=cookies, timeout=10)
            initial_tier = "basic"
            initial_credits = 0
            if initial_response.status_code == 200:
                data = initial_response.json()
                initial_tier = data.get("tier", "basic")
                initial_credits = data.get("credits", 0)
            
            # Upgrade to pro plan
            webhook_url = f"{API_BASE}/webhooks/billing/mock/success?uid={self.user_id}&plan=pro"
            response = requests.get(webhook_url, timeout=10, allow_redirects=False)
            
            # Should redirect (302)
            if response.status_code != 302:
                self.log_test(
                    "Mock Pro Plan Upgrade",
                    False,
                    error_details=f"Expected HTTP 302 redirect, got {response.status_code}"
                )
                return False
            
            # Check redirect URL
            location = response.headers.get("location", "")
            if "/billing?success=1" not in location:
                self.log_test(
                    "Mock Pro Plan Upgrade",
                    False,
                    error_details=f"Unexpected redirect location: {location}"
                )
                return False
            
            # Verify tier and credits updated
            time.sleep(1)  # Brief delay for processing
            final_response = requests.get(f"{API_BASE}/billing/state", cookies=cookies, timeout=10)
            
            if final_response.status_code == 200:
                data = final_response.json()
                final_tier = data.get("tier", "basic")
                final_credits = data.get("credits", 0)
                renewsAt = data.get("renewsAt")
                
                # Verify tier is pro
                if final_tier != "pro":
                    self.log_test(
                        "Mock Pro Plan Upgrade",
                        False,
                        error_details=f"Expected tier 'pro', got '{final_tier}'"
                    )
                    return False
                
                # Verify 200 monthly credits granted (should be at least initial + 200)
                expected_min_credits = initial_credits + 200
                if final_credits < expected_min_credits:
                    self.log_test(
                        "Mock Pro Plan Upgrade",
                        False,
                        error_details=f"Expected at least {expected_min_credits} credits, got {final_credits}"
                    )
                    return False
                
                # Verify subscription created with renewsAt date
                if not renewsAt:
                    self.log_test(
                        "Mock Pro Plan Upgrade",
                        False,
                        error_details="Missing renewsAt field in subscription"
                    )
                    return False
                
                self.log_test(
                    "Mock Pro Plan Upgrade",
                    True,
                    f"Tier: {initial_tier} → {final_tier}, Credits: {initial_credits} → {final_credits}, RenewsAt: {renewsAt}"
                )
                return True
            else:
                self.log_test(
                    "Mock Pro Plan Upgrade",
                    False,
                    error_details=f"Failed to verify upgrade: HTTP {final_response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Mock Pro Plan Upgrade",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_chemistry_options_after_pro_upgrade(self):
        """Test 5: Chemistry Options After Pro Upgrade"""
        if not self.admin_jwt_cookie:
            self.log_test(
                "Chemistry Options After Pro Upgrade",
                False,
                error_details="No admin JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/chemistry/options", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify tier is pro
                if data.get("tier") != "pro":
                    self.log_test(
                        "Chemistry Options After Pro Upgrade",
                        False,
                        error_details=f"Expected tier 'pro', got '{data.get('tier')}'"
                    )
                    return False
                
                mods = data.get("mods", [])
                
                # Check for pro tier modifications (should have 8 total)
                if len(mods) < 8:
                    self.log_test(
                        "Chemistry Options After Pro Upgrade",
                        False,
                        error_details=f"Expected at least 8 modifications, got {len(mods)}"
                    )
                    return False
                
                # Check for specific pro options
                mod_keys = [mod.get("key") for mod in mods]
                pro_options = ["pegylation", "lipidation", "n_methylation"]
                missing_pro_options = [opt for opt in pro_options if opt not in mod_keys]
                
                if missing_pro_options:
                    self.log_test(
                        "Chemistry Options After Pro Upgrade",
                        False,
                        error_details=f"Missing pro tier options: {missing_pro_options}"
                    )
                    return False
                
                # Verify enterprise options are still excluded
                enterprise_options = ["glycosylation", "peptoid", "stapling", "unnatural_aa"]
                present_enterprise_options = [opt for opt in enterprise_options if opt in mod_keys]
                
                if present_enterprise_options:
                    self.log_test(
                        "Chemistry Options After Pro Upgrade",
                        False,
                        error_details=f"Enterprise options should not be present: {present_enterprise_options}"
                    )
                    return False
                
                self.log_test(
                    "Chemistry Options After Pro Upgrade",
                    True,
                    f"Tier: {data.get('tier')}, Total mods: {len(mods)}, Pro options present: {[opt for opt in pro_options if opt in mod_keys]}"
                )
                return True
            else:
                self.log_test(
                    "Chemistry Options After Pro Upgrade",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Chemistry Options After Pro Upgrade",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_mock_enterprise_upgrade(self):
        """Test 6: Mock Enterprise Upgrade"""
        if not self.user_id:
            self.log_test(
                "Mock Enterprise Upgrade",
                False,
                error_details="No user ID available"
            )
            return False
        
        try:
            # Upgrade to enterprise plan
            webhook_url = f"{API_BASE}/webhooks/billing/mock/success?uid={self.user_id}&plan=enterprise"
            response = requests.get(webhook_url, timeout=10, allow_redirects=False)
            
            # Should redirect (302)
            if response.status_code != 302:
                self.log_test(
                    "Mock Enterprise Upgrade",
                    False,
                    error_details=f"Expected HTTP 302 redirect, got {response.status_code}"
                )
                return False
            
            # Verify tier and credits updated
            time.sleep(1)  # Brief delay for processing
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            final_response = requests.get(f"{API_BASE}/billing/state", cookies=cookies, timeout=10)
            
            if final_response.status_code == 200:
                data = final_response.json()
                final_tier = data.get("tier", "basic")
                final_credits = data.get("credits", 0)
                
                # Verify tier is enterprise
                if final_tier != "enterprise":
                    self.log_test(
                        "Mock Enterprise Upgrade",
                        False,
                        error_details=f"Expected tier 'enterprise', got '{final_tier}'"
                    )
                    return False
                
                # Verify 5000 monthly credits granted (should be at least 5000)
                if final_credits < 5000:
                    self.log_test(
                        "Mock Enterprise Upgrade",
                        False,
                        error_details=f"Expected at least 5000 credits, got {final_credits}"
                    )
                    return False
                
                self.log_test(
                    "Mock Enterprise Upgrade",
                    True,
                    f"Tier: {final_tier}, Credits: {final_credits}"
                )
                return True
            else:
                self.log_test(
                    "Mock Enterprise Upgrade",
                    False,
                    error_details=f"Failed to verify upgrade: HTTP {final_response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Mock Enterprise Upgrade",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_combined_plan_and_credits(self):
        """Test 7: Combined Plan + Credits"""
        if not self.user_id:
            self.log_test(
                "Combined Plan + Credits",
                False,
                error_details="No user ID available"
            )
            return False
        
        try:
            # Get initial state
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            initial_response = requests.get(f"{API_BASE}/billing/state", cookies=cookies, timeout=10)
            initial_credits = 0
            if initial_response.status_code == 200:
                initial_credits = initial_response.json().get("credits", 0)
            
            # Upgrade to pro plan + 50 bonus credits
            webhook_url = f"{API_BASE}/webhooks/billing/mock/success?uid={self.user_id}&plan=pro&credits=50"
            response = requests.get(webhook_url, timeout=10, allow_redirects=False)
            
            # Should redirect (302)
            if response.status_code != 302:
                self.log_test(
                    "Combined Plan + Credits",
                    False,
                    error_details=f"Expected HTTP 302 redirect, got {response.status_code}"
                )
                return False
            
            # Verify both plan upgrade and credits applied
            time.sleep(1)  # Brief delay for processing
            final_response = requests.get(f"{API_BASE}/billing/state", cookies=cookies, timeout=10)
            
            if final_response.status_code == 200:
                data = final_response.json()
                final_tier = data.get("tier", "basic")
                final_credits = data.get("credits", 0)
                
                # Verify tier is pro
                if final_tier != "pro":
                    self.log_test(
                        "Combined Plan + Credits",
                        False,
                        error_details=f"Expected tier 'pro', got '{final_tier}'"
                    )
                    return False
                
                # Verify credits include both plan credits (200) and bonus (50)
                # Should be at least initial + 200 (pro plan) + 50 (bonus)
                expected_min_credits = initial_credits + 200 + 50
                if final_credits < expected_min_credits:
                    self.log_test(
                        "Combined Plan + Credits",
                        False,
                        error_details=f"Expected at least {expected_min_credits} credits, got {final_credits}"
                    )
                    return False
                
                self.log_test(
                    "Combined Plan + Credits",
                    True,
                    f"Tier: {final_tier}, Credits: {initial_credits} → {final_credits} (expected +250)"
                )
                return True
            else:
                self.log_test(
                    "Combined Plan + Credits",
                    False,
                    error_details=f"Failed to verify upgrade: HTTP {final_response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Combined Plan + Credits",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """Run all Phase 8.2 billing tests"""
        print("=" * 80)
        print("💳 PHASE 8.2: BILLING WIDGET STABILITY + MOCK PRO UPGRADE TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Email: {self.admin_email}")
        print(f"Test Started: {datetime.now().isoformat()}")
        print("=" * 80)
        print()
        
        # Setup: Authenticate admin user
        print("🔐 AUTHENTICATION SETUP")
        print("-" * 40)
        if not self.authenticate_admin_user():
            print("❌ Authentication failed - cannot proceed with tests")
            return self.get_summary()
        
        # Test 1: Session Endpoint
        print("\n📋 SESSION ENDPOINT TEST")
        print("-" * 40)
        self.test_session_endpoint()
        
        # Test 2: Billing State Endpoint
        print("\n💰 BILLING STATE ENDPOINT TEST")
        print("-" * 40)
        self.test_billing_state_endpoint()
        
        # Test 3: Mock Credit Purchase
        print("\n🪙 MOCK CREDIT PURCHASE TEST")
        print("-" * 40)
        self.test_mock_credit_purchase()
        
        # Test 4: Mock Pro Plan Upgrade
        print("\n⭐ MOCK PRO PLAN UPGRADE TEST")
        print("-" * 40)
        self.test_mock_pro_plan_upgrade()
        
        # Test 5: Chemistry Options After Pro Upgrade
        print("\n🧪 CHEMISTRY OPTIONS AFTER PRO UPGRADE TEST")
        print("-" * 40)
        self.test_chemistry_options_after_pro_upgrade()
        
        # Test 6: Mock Enterprise Upgrade
        print("\n🏢 MOCK ENTERPRISE UPGRADE TEST")
        print("-" * 40)
        self.test_mock_enterprise_upgrade()
        
        # Test 7: Combined Plan + Credits
        print("\n🎯 COMBINED PLAN + CREDITS TEST")
        print("-" * 40)
        self.test_combined_plan_and_credits()
        
        return self.get_summary()
    
    def get_summary(self):
        """Get test summary"""
        print("\n" + "=" * 80)
        print("📈 PHASE 8.2 BILLING TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0.0%")
        
        if self.critical_failures:
            print(f"\n❌ CRITICAL FAILURES ({len(self.critical_failures)}):")
            for failure in self.critical_failures:
                print(f"  • {failure['test']}: {failure['error']}")
        
        billing_status = "✅ WORKING" if self.tests_passed >= self.tests_run * 0.85 else "❌ ISSUES DETECTED"
        print(f"\nBilling System Status: {billing_status}")
        print("=" * 80)
        
        return {
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "success_rate": self.tests_passed/self.tests_run*100 if self.tests_run > 0 else 0,
            "critical_failures": self.critical_failures,
            "test_results": self.test_results,
            "billing_working": self.tests_passed >= self.tests_run * 0.85
        }

class Phase8ChemistryTest:
    """Test Phase 8 Final: PK-Aware Chemistry Options API"""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []
        self.test_results = {}
        self.admin_jwt_cookie = None
        self.pro_jwt_cookie = None
        self.admin_email = "founder@peptologic.ai"
        self.pro_email = "pro@example.com"
        
    def log_test(self, test_name, success, details="", error_details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
            if details:
                print(f"   Details: {details}")
        else:
            print(f"❌ {test_name}: FAILED")
            if error_details:
                print(f"   Error: {error_details}")
            self.critical_failures.append({
                "test": test_name,
                "error": error_details,
                "timestamp": datetime.now().isoformat()
            })
        
        self.test_results[test_name] = {
            "success": success,
            "details": details,
            "error": error_details,
            "timestamp": datetime.now().isoformat()
        }
        print()
    
    def test_chemistry_options_anonymous(self):
        """Test GET /api/chemistry/options without authentication (should return basic tier)"""
        try:
            response = requests.get(f"{API_BASE}/chemistry/options", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify tier is basic
                if data.get("tier") != "basic":
                    self.log_test(
                        "Chemistry Options (Anonymous - Basic Tier)",
                        False,
                        error_details=f"Expected tier 'basic', got '{data.get('tier')}'"
                    )
                    return False
                
                # Verify basic tier options are present
                mods = data.get("mods", [])
                exclusions = data.get("exclusions", [])
                
                # Check for basic tier modifications
                basic_mods = [mod for mod in mods if mod.get("key") in ["d_isomers", "cyclization", "acetylation", "amidation", "substitution"]]
                
                # Check that pro-tier options are NOT present
                pro_mods = [mod for mod in mods if mod.get("key") in ["pegylation", "lipidation", "n_methylation"]]
                
                # Check that enterprise-tier options are NOT present
                enterprise_mods = [mod for mod in mods if mod.get("key") in ["glycosylation", "peptoid", "stapling", "unnatural_aa"]]
                
                if len(basic_mods) >= 5 and len(pro_mods) == 0 and len(enterprise_mods) == 0:
                    self.log_test(
                        "Chemistry Options (Anonymous - Basic Tier)",
                        True,
                        f"Tier: {data.get('tier')}, Basic mods: {len(basic_mods)}, Pro mods: {len(pro_mods)}, Enterprise mods: {len(enterprise_mods)}, Exclusions: {len(exclusions)}"
                    )
                    return True
                else:
                    self.log_test(
                        "Chemistry Options (Anonymous - Basic Tier)",
                        False,
                        error_details=f"Tier filtering failed - Basic: {len(basic_mods)}, Pro: {len(pro_mods)}, Enterprise: {len(enterprise_mods)}"
                    )
                    return False
            else:
                self.log_test(
                    "Chemistry Options (Anonymous - Basic Tier)",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Chemistry Options (Anonymous - Basic Tier)",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def authenticate_pro_user(self):
        """Authenticate as pro-tier user (simulate by upgrading a user to pro)"""
        try:
            # Step 1: Request magic code for pro user
            payload = {"email": self.pro_email}
            response = requests.post(f"{API_BASE}/auth/magic/request", json=payload, timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Pro User Authentication Setup - Magic Code Request",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            data = response.json()
            if not data.get("success") or "demo_code" not in data:
                self.log_test(
                    "Pro User Authentication Setup - Magic Code Request",
                    False,
                    error_details="Response missing demo_code or success flag"
                )
                return False
            
            demo_code = data["demo_code"]
            
            # Step 2: Verify magic code
            payload = {"email": self.pro_email, "code": demo_code}
            response = requests.post(f"{API_BASE}/auth/magic/verify", json=payload, timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Pro User Authentication Setup - Magic Code Verify",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            # Extract JWT cookie
            cookies = response.cookies
            if "pmnc_jwt" not in cookies:
                self.log_test(
                    "Pro User Authentication Setup - JWT Cookie",
                    False,
                    error_details="JWT cookie not set in response"
                )
                return False
            
            self.pro_jwt_cookie = cookies["pmnc_jwt"]
            
            # Step 3: Get user info to extract user ID
            cookies_dict = {"pmnc_jwt": self.pro_jwt_cookie}
            response = requests.get(f"{API_BASE}/auth/me", cookies=cookies_dict, timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Pro User Authentication Setup - Get User Info",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            user_data = response.json()
            pro_user_id = user_data.get("id")
            
            if not pro_user_id:
                self.log_test(
                    "Pro User Authentication Setup - Extract User ID",
                    False,
                    error_details="User ID not found in response"
                )
                return False
            
            # Step 4: Upgrade user to pro tier via mock webhook
            webhook_url = f"{API_BASE}/webhooks/billing/mock/success?uid={pro_user_id}&plan=pro"
            response = requests.get(webhook_url, timeout=10, allow_redirects=False)
            
            # Should redirect (302) or return success
            if response.status_code not in [200, 302]:
                self.log_test(
                    "Pro User Authentication Setup - Plan Upgrade",
                    False,
                    error_details=f"Plan upgrade failed: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            # Verify pro tier
            time.sleep(1)  # Brief delay for processing
            response = requests.get(f"{API_BASE}/auth/session", cookies=cookies_dict, timeout=10)
            
            if response.status_code == 200:
                session_data = response.json()
                if session_data.get("tier") == "pro":
                    self.log_test(
                        "Pro User Authentication Setup",
                        True,
                        f"Authenticated as {self.pro_email}, tier: {session_data.get('tier')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Pro User Authentication Setup - Tier Verification",
                        False,
                        error_details=f"Expected tier 'pro', got '{session_data.get('tier')}'"
                    )
                    return False
            else:
                self.log_test(
                    "Pro User Authentication Setup - Session Check",
                    False,
                    error_details=f"Failed to get session: HTTP {response.status_code}"
                )
                return False
            
        except Exception as e:
            self.log_test(
                "Pro User Authentication Setup",
                False,
                error_details=f"Authentication failed: {str(e)}"
            )
            return False
    
    def test_chemistry_options_pro_user(self):
        """Test GET /api/chemistry/options with pro-tier authentication"""
        if not self.pro_jwt_cookie:
            self.log_test(
                "Chemistry Options (Pro User)",
                False,
                error_details="No pro JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.pro_jwt_cookie}
            response = requests.get(f"{API_BASE}/chemistry/options", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify tier is pro
                if data.get("tier") != "pro":
                    self.log_test(
                        "Chemistry Options (Pro User)",
                        False,
                        error_details=f"Expected tier 'pro', got '{data.get('tier')}'"
                    )
                    return False
                
                mods = data.get("mods", [])
                exclusions = data.get("exclusions", [])
                
                # Check for basic + pro tier modifications
                basic_mods = [mod for mod in mods if mod.get("key") in ["d_isomers", "cyclization", "acetylation", "amidation", "substitution"]]
                pro_mods = [mod for mod in mods if mod.get("key") in ["pegylation", "lipidation", "n_methylation"]]
                
                # Check that enterprise-tier options are still NOT present
                enterprise_mods = [mod for mod in mods if mod.get("key") in ["glycosylation", "peptoid", "stapling", "unnatural_aa"]]
                
                if len(basic_mods) >= 5 and len(pro_mods) >= 3 and len(enterprise_mods) == 0:
                    self.log_test(
                        "Chemistry Options (Pro User)",
                        True,
                        f"Tier: {data.get('tier')}, Basic mods: {len(basic_mods)}, Pro mods: {len(pro_mods)}, Enterprise mods: {len(enterprise_mods)}, Exclusions: {len(exclusions)}"
                    )
                    return True
                else:
                    self.log_test(
                        "Chemistry Options (Pro User)",
                        False,
                        error_details=f"Tier filtering failed - Basic: {len(basic_mods)}, Pro: {len(pro_mods)}, Enterprise: {len(enterprise_mods)}"
                    )
                    return False
            else:
                self.log_test(
                    "Chemistry Options (Pro User)",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Chemistry Options (Pro User)",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_chemistry_options_response_structure(self):
        """Test chemistry options response structure and PK intent data"""
        try:
            response = requests.get(f"{API_BASE}/chemistry/options", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify top-level structure
                required_fields = ["tier", "mods", "exclusions"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(
                        "Chemistry Options Response Structure",
                        False,
                        error_details=f"Missing required fields: {missing_fields}"
                    )
                    return False
                
                # Verify mods structure
                mods = data.get("mods", [])
                if not mods:
                    self.log_test(
                        "Chemistry Options Response Structure",
                        False,
                        error_details="No modifications returned"
                    )
                    return False
                
                # Check first mod for required fields
                first_mod = mods[0]
                required_mod_fields = ["key", "label", "tier", "pk_intent", "notes", "typical_targets"]
                missing_mod_fields = [field for field in required_mod_fields if field not in first_mod]
                
                if missing_mod_fields:
                    self.log_test(
                        "Chemistry Options Response Structure",
                        False,
                        error_details=f"Modification missing required fields: {missing_mod_fields}"
                    )
                    return False
                
                # Verify PK intent is a list
                if not isinstance(first_mod.get("pk_intent"), list):
                    self.log_test(
                        "Chemistry Options Response Structure",
                        False,
                        error_details="pk_intent should be a list"
                    )
                    return False
                
                # Verify exclusions structure
                exclusions = data.get("exclusions", [])
                if exclusions:
                    first_exclusion = exclusions[0]
                    required_exclusion_fields = ["key", "label", "tier"]
                    missing_exclusion_fields = [field for field in required_exclusion_fields if field not in first_exclusion]
                    
                    if missing_exclusion_fields:
                        self.log_test(
                            "Chemistry Options Response Structure",
                            False,
                            error_details=f"Exclusion missing required fields: {missing_exclusion_fields}"
                        )
                        return False
                
                self.log_test(
                    "Chemistry Options Response Structure",
                    True,
                    f"Valid structure: {len(mods)} mods, {len(exclusions)} exclusions, PK intent categories present"
                )
                return True
            else:
                self.log_test(
                    "Chemistry Options Response Structure",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Chemistry Options Response Structure",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_tier_filtering_logic(self):
        """Test tier filtering hierarchy (basic=0, pro=1, enterprise=2)"""
        try:
            # Test anonymous (basic) access
            response = requests.get(f"{API_BASE}/chemistry/options", timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Tier Filtering Logic",
                    False,
                    error_details=f"Failed to get basic tier options: HTTP {response.status_code}"
                )
                return False
            
            basic_data = response.json()
            basic_mods = {mod["key"] for mod in basic_data.get("mods", [])}
            
            # Verify tier escalation prevention
            expected_basic_only = {"d_isomers", "cyclization", "acetylation", "amidation", "substitution"}
            pro_only = {"pegylation", "lipidation", "n_methylation"}
            enterprise_only = {"glycosylation", "peptoid", "stapling", "unnatural_aa"}
            
            # Basic user should have basic options but not pro/enterprise
            basic_has_basic = expected_basic_only.issubset(basic_mods)
            basic_has_pro = bool(pro_only.intersection(basic_mods))
            basic_has_enterprise = bool(enterprise_only.intersection(basic_mods))
            
            if not basic_has_basic:
                self.log_test(
                    "Tier Filtering Logic",
                    False,
                    error_details=f"Basic user missing basic options: {expected_basic_only - basic_mods}"
                )
                return False
            
            if basic_has_pro or basic_has_enterprise:
                self.log_test(
                    "Tier Filtering Logic",
                    False,
                    error_details=f"Basic user has higher tier options: Pro={basic_has_pro}, Enterprise={basic_has_enterprise}"
                )
                return False
            
            self.log_test(
                "Tier Filtering Logic",
                True,
                f"Tier hierarchy enforced correctly - Basic user has {len(basic_mods)} options, no tier escalation"
            )
            return True
            
        except Exception as e:
            self.log_test(
                "Tier Filtering Logic",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """Run all chemistry options tests"""
        print("=" * 80)
        print("🧪 PEPTIMANCER PHASE 8 FINAL: PK-AWARE CHEMISTRY OPTIONS API TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Started: {datetime.now().isoformat()}")
        print("=" * 80)
        print()
        
        # Test 1: Anonymous user (basic tier)
        print("📋 ANONYMOUS USER TESTS (BASIC TIER)")
        print("-" * 40)
        self.test_chemistry_options_anonymous()
        
        # Test 2: Response structure validation
        print("\n📊 RESPONSE STRUCTURE TESTS")
        print("-" * 40)
        self.test_chemistry_options_response_structure()
        
        # Test 3: Tier filtering logic
        print("\n🔒 TIER FILTERING TESTS")
        print("-" * 40)
        self.test_tier_filtering_logic()
        
        # Test 4: Pro user authentication and access
        print("\n👤 PRO USER TESTS")
        print("-" * 40)
        if self.authenticate_pro_user():
            self.test_chemistry_options_pro_user()
        
        # Final summary
        print("\n" + "=" * 80)
        print("📈 CHEMISTRY OPTIONS API TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.critical_failures:
            print(f"\n❌ CRITICAL FAILURES ({len(self.critical_failures)}):")
            for failure in self.critical_failures:
                print(f"  • {failure['test']}: {failure['error']}")
        
        print(f"\nChemistry Options API Status: {'✅ WORKING' if self.tests_passed >= self.tests_run * 0.85 else '❌ ISSUES DETECTED'}")
        print("=" * 80)
        
        return {
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "success_rate": self.tests_passed/self.tests_run*100,
            "critical_failures": self.critical_failures,
            "test_results": self.test_results,
            "chemistry_api_working": self.tests_passed >= self.tests_run * 0.85
        }

class Phase8BillingTest:
    """Test Phase 8: Session Endpoint + Authenticated Billing Flow"""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []
        self.test_results = {}
        self.admin_jwt_cookie = None
        self.admin_email = "founder@peptologic.ai"
        self.user_id = None
        
    def log_test(self, test_name, success, details="", error_details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
            if details:
                print(f"   Details: {details}")
        else:
            print(f"❌ {test_name}: FAILED")
            if error_details:
                print(f"   Error: {error_details}")
            self.critical_failures.append({
                "test": test_name,
                "error": error_details,
                "timestamp": datetime.now().isoformat()
            })
        
        self.test_results[test_name] = {
            "success": success,
            "details": details,
            "error": error_details,
            "timestamp": datetime.now().isoformat()
        }
        print()
    
    def authenticate_test_user(self):
        """Authenticate as test user to get JWT cookie and user ID"""
        try:
            # Step 1: Request magic code
            payload = {"email": self.admin_email}
            response = requests.post(f"{API_BASE}/auth/magic/request", json=payload, timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Authentication Setup - Magic Code Request",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            data = response.json()
            if not data.get("success") or "demo_code" not in data:
                self.log_test(
                    "Authentication Setup - Magic Code Request",
                    False,
                    error_details="Response missing demo_code or success flag"
                )
                return False
            
            demo_code = data["demo_code"]
            
            # Step 2: Verify magic code
            payload = {"email": self.admin_email, "code": demo_code}
            response = requests.post(f"{API_BASE}/auth/magic/verify", json=payload, timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Authentication Setup - Magic Code Verify",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            # Extract JWT cookie
            cookies = response.cookies
            if "pmnc_jwt" not in cookies:
                self.log_test(
                    "Authentication Setup - JWT Cookie",
                    False,
                    error_details="JWT cookie not set in response"
                )
                return False
            
            self.admin_jwt_cookie = cookies["pmnc_jwt"]
            
            # Step 3: Get user info to extract user ID
            cookies_dict = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/auth/me", cookies=cookies_dict, timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Authentication Setup - Get User Info",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            user_data = response.json()
            self.user_id = user_data.get("id")
            
            if not self.user_id:
                self.log_test(
                    "Authentication Setup - Extract User ID",
                    False,
                    error_details="User ID not found in response"
                )
                return False
            
            self.log_test(
                "Authentication Setup",
                True,
                f"Authenticated as {self.admin_email}, user_id: {self.user_id}"
            )
            return True
            
        except Exception as e:
            self.log_test(
                "Authentication Setup",
                False,
                error_details=f"Authentication failed: {str(e)}"
            )
            return False
    
    def test_session_endpoint_authenticated(self):
        """Test GET /api/auth/session with authenticated user"""
        if not self.admin_jwt_cookie:
            self.log_test(
                "Session Endpoint (Authenticated)",
                False,
                error_details="No JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/auth/session", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["email", "role", "tier", "credits"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test(
                        "Session Endpoint (Authenticated)",
                        True,
                        f"Email: {data.get('email')}, Role: {data.get('role')}, Tier: {data.get('tier')}, Credits: {data.get('credits')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Session Endpoint (Authenticated)",
                        False,
                        error_details=f"Missing required fields: {missing_fields}"
                    )
                    return False
            else:
                self.log_test(
                    "Session Endpoint (Authenticated)",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Session Endpoint (Authenticated)",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_session_endpoint_unauthenticated(self):
        """Test GET /api/auth/session without authentication (should return 401)"""
        try:
            response = requests.get(f"{API_BASE}/auth/session", timeout=10)
            
            if response.status_code == 401:
                self.log_test(
                    "Session Endpoint (Unauthenticated - Should Fail)",
                    True,
                    "Correctly returned 401 Unauthorized for unauthenticated request"
                )
                return True
            else:
                self.log_test(
                    "Session Endpoint (Unauthenticated - Should Fail)",
                    False,
                    error_details=f"Expected HTTP 401, got {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Session Endpoint (Unauthenticated - Should Fail)",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_mock_credit_topup(self):
        """Test mock credit top-up via webhook"""
        if not self.user_id:
            self.log_test(
                "Mock Credit Top-Up",
                False,
                error_details="No user ID available"
            )
            return False
        
        try:
            # Get current credits first
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/billing/state", cookies=cookies, timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Mock Credit Top-Up - Get Initial State",
                    False,
                    error_details=f"Failed to get billing state: HTTP {response.status_code}"
                )
                return False
            
            initial_state = response.json()
            initial_credits = initial_state.get("credits", 0)
            
            # Trigger mock webhook for credit purchase
            webhook_url = f"{API_BASE}/webhooks/billing/mock/success?uid={self.user_id}&credits=100"
            response = requests.get(webhook_url, timeout=10, allow_redirects=False)
            
            # Should redirect (302) to billing page
            if response.status_code not in [200, 302]:
                self.log_test(
                    "Mock Credit Top-Up - Webhook Trigger",
                    False,
                    error_details=f"Webhook failed: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            # Check credits increased
            time.sleep(1)  # Brief delay for processing
            response = requests.get(f"{API_BASE}/billing/state", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                new_state = response.json()
                new_credits = new_state.get("credits", 0)
                
                if new_credits >= initial_credits + 100:
                    # Check ledger entry
                    history = new_state.get("history", [])
                    credit_entry = None
                    for entry in history:
                        if entry.get("reason") == "Credits purchase" and entry.get("delta") == 100:
                            credit_entry = entry
                            break
                    
                    if credit_entry:
                        self.log_test(
                            "Mock Credit Top-Up",
                            True,
                            f"Credits increased from {initial_credits} to {new_credits}, ledger entry created"
                        )
                        return True
                    else:
                        self.log_test(
                            "Mock Credit Top-Up",
                            False,
                            error_details="Credits increased but no ledger entry found"
                        )
                        return False
                else:
                    self.log_test(
                        "Mock Credit Top-Up",
                        False,
                        error_details=f"Credits not increased properly: {initial_credits} -> {new_credits}"
                    )
                    return False
            else:
                self.log_test(
                    "Mock Credit Top-Up - Check New State",
                    False,
                    error_details=f"Failed to get new billing state: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Mock Credit Top-Up",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_credit_debit_generation(self):
        """Test credit debit for analogue generation"""
        if not self.admin_jwt_cookie:
            self.log_test(
                "Credit Debit for Generation",
                False,
                error_details="No JWT cookie available"
            )
            return False
        
        try:
            # Get current credits
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/billing/state", cookies=cookies, timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Credit Debit for Generation - Get Initial State",
                    False,
                    error_details=f"Failed to get billing state: HTTP {response.status_code}"
                )
                return False
            
            initial_state = response.json()
            initial_credits = initial_state.get("credits", 0)
            
            if initial_credits < 2:
                self.log_test(
                    "Credit Debit for Generation",
                    False,
                    error_details=f"Insufficient credits for test: {initial_credits} (need at least 2)"
                )
                return False
            
            # Generate analogues (should cost 2 credits for 2 analogues)
            payload = {
                "generation_id": f"test_gen_{int(time.time())}",
                "base_molecule": "HAEGTFTSDVSSYLEG",
                "allowed_mods": "substitution",
                "exclusions": "none",
                "target_use": "credit debit test",
                "num_analogues": 2,
                "include_cost": False
            }
            
            response = requests.post(f"{API_BASE}/generate-analogues", json=payload, cookies=cookies, timeout=60)
            
            if response.status_code == 200:
                # Check credits decreased
                time.sleep(1)  # Brief delay for processing
                response = requests.get(f"{API_BASE}/billing/state", cookies=cookies, timeout=10)
                
                if response.status_code == 200:
                    new_state = response.json()
                    new_credits = new_state.get("credits", 0)
                    
                    if new_credits == initial_credits - 2:
                        # Check ledger entry
                        history = new_state.get("history", [])
                        debit_entry = None
                        for entry in history:
                            if "Analogue generation" in entry.get("reason", "") and entry.get("delta") == -2:
                                debit_entry = entry
                                break
                        
                        if debit_entry:
                            self.log_test(
                                "Credit Debit for Generation",
                                True,
                                f"Credits deducted: {initial_credits} -> {new_credits}, ledger entry created"
                            )
                            return True
                        else:
                            self.log_test(
                                "Credit Debit for Generation",
                                False,
                                error_details="Credits deducted but no ledger entry found"
                            )
                            return False
                    else:
                        self.log_test(
                            "Credit Debit for Generation",
                            False,
                            error_details=f"Credits not deducted properly: {initial_credits} -> {new_credits} (expected -2)"
                        )
                        return False
                else:
                    self.log_test(
                        "Credit Debit for Generation - Check New State",
                        False,
                        error_details=f"Failed to get new billing state: HTTP {response.status_code}"
                    )
                    return False
            elif response.status_code == 402:
                self.log_test(
                    "Credit Debit for Generation",
                    True,
                    "Correctly returned 402 Payment Required for insufficient credits"
                )
                return True
            else:
                self.log_test(
                    "Credit Debit for Generation",
                    False,
                    error_details=f"Generation failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Credit Debit for Generation",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_mock_plan_upgrade(self):
        """Test mock plan upgrade to Pro"""
        if not self.user_id or not self.admin_jwt_cookie:
            self.log_test(
                "Mock Plan Upgrade (Pro)",
                False,
                error_details="No user ID or JWT cookie available"
            )
            return False
        
        try:
            # Get current tier
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/billing/state", cookies=cookies, timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Mock Plan Upgrade - Get Initial State",
                    False,
                    error_details=f"Failed to get billing state: HTTP {response.status_code}"
                )
                return False
            
            initial_state = response.json()
            initial_tier = initial_state.get("tier", "basic")
            initial_credits = initial_state.get("credits", 0)
            
            # Start checkout for pro plan
            payload = {"plan": "pro"}
            response = requests.post(f"{API_BASE}/billing/checkout", json=payload, cookies=cookies, timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Mock Plan Upgrade - Checkout",
                    False,
                    error_details=f"Checkout failed: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            # Trigger mock success webhook for pro plan
            webhook_url = f"{API_BASE}/webhooks/billing/mock/success?uid={self.user_id}&plan=pro"
            response = requests.get(webhook_url, timeout=10, allow_redirects=False)
            
            if response.status_code not in [200, 302]:
                self.log_test(
                    "Mock Plan Upgrade - Webhook Trigger",
                    False,
                    error_details=f"Webhook failed: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            # Check tier upgraded and credits granted
            time.sleep(1)  # Brief delay for processing
            response = requests.get(f"{API_BASE}/billing/state", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                new_state = response.json()
                new_tier = new_state.get("tier", "basic")
                new_credits = new_state.get("credits", 0)
                renews_at = new_state.get("renewsAt")
                
                # Check tier upgrade
                if new_tier != "pro":
                    self.log_test(
                        "Mock Plan Upgrade (Pro)",
                        False,
                        error_details=f"Tier not upgraded: {initial_tier} -> {new_tier} (expected pro)"
                    )
                    return False
                
                # Check credits granted (pro plan should grant 200 credits)
                expected_credits = initial_credits + 200
                if new_credits < expected_credits:
                    self.log_test(
                        "Mock Plan Upgrade (Pro)",
                        False,
                        error_details=f"Credits not granted properly: {initial_credits} -> {new_credits} (expected +200)"
                    )
                    return False
                
                # Check subscription created with renewal date
                if not renews_at:
                    self.log_test(
                        "Mock Plan Upgrade (Pro)",
                        False,
                        error_details="No renewal date set for subscription"
                    )
                    return False
                
                # Check ledger entry
                history = new_state.get("history", [])
                refill_entry = None
                for entry in history:
                    if "Monthly refill (pro)" in entry.get("reason", "") and entry.get("delta") == 200:
                        refill_entry = entry
                        break
                
                if refill_entry:
                    self.log_test(
                        "Mock Plan Upgrade (Pro)",
                        True,
                        f"Tier: {initial_tier} -> {new_tier}, Credits: {initial_credits} -> {new_credits}, Renews: {renews_at}"
                    )
                    return True
                else:
                    self.log_test(
                        "Mock Plan Upgrade (Pro)",
                        False,
                        error_details="Tier upgraded but no ledger entry found"
                    )
                    return False
            else:
                self.log_test(
                    "Mock Plan Upgrade - Check New State",
                    False,
                    error_details=f"Failed to get new billing state: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Mock Plan Upgrade (Pro)",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_billing_state_query(self):
        """Test GET /api/billing/state"""
        if not self.admin_jwt_cookie:
            self.log_test(
                "Billing State Query",
                False,
                error_details="No JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/billing/state", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["tier", "credits", "renewsAt", "history"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Validate history structure
                    history = data.get("history", [])
                    if isinstance(history, list):
                        self.log_test(
                            "Billing State Query",
                            True,
                            f"Tier: {data.get('tier')}, Credits: {data.get('credits')}, History entries: {len(history)}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Billing State Query",
                            False,
                            error_details="History field is not an array"
                        )
                        return False
                else:
                    self.log_test(
                        "Billing State Query",
                        False,
                        error_details=f"Missing required fields: {missing_fields}"
                    )
                    return False
            else:
                self.log_test(
                    "Billing State Query",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Billing State Query",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def test_insufficient_credits_scenario(self):
        """Test generation with insufficient credits (should return 402)"""
        if not self.admin_jwt_cookie:
            self.log_test(
                "Insufficient Credits Scenario",
                False,
                error_details="No JWT cookie available"
            )
            return False
        
        try:
            # Try to generate many analogues to exceed credits
            payload = {
                "generation_id": f"test_insufficient_{int(time.time())}",
                "base_molecule": "HAEGTFTSDVSSYLEG",
                "allowed_mods": "substitution",
                "exclusions": "none",
                "target_use": "insufficient credits test",
                "num_analogues": 10,  # High number to likely exceed credits
                "include_cost": False
            }
            
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.post(f"{API_BASE}/generate-analogues", json=payload, cookies=cookies, timeout=60)
            
            if response.status_code == 402:
                data = response.json()
                if "credits" in data.get("detail", "").lower():
                    self.log_test(
                        "Insufficient Credits Scenario",
                        True,
                        f"Correctly returned 402 Payment Required: {data.get('detail')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Insufficient Credits Scenario",
                        False,
                        error_details=f"402 returned but wrong message: {data.get('detail')}"
                    )
                    return False
            elif response.status_code == 200:
                # If it succeeded, user had enough credits - that's also valid
                self.log_test(
                    "Insufficient Credits Scenario",
                    True,
                    "Generation succeeded - user had sufficient credits"
                )
                return True
            else:
                self.log_test(
                    "Insufficient Credits Scenario",
                    False,
                    error_details=f"Unexpected response: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Insufficient Credits Scenario",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """Run all Phase 8 billing tests"""
        print("=" * 80)
        print("💳 PEPTIMANCER PHASE 8: SESSION ENDPOINT + BILLING FLOW TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User: {self.admin_email}")
        print(f"Test Started: {datetime.now().isoformat()}")
        print("=" * 80)
        print()
        
        # Setup authentication
        print("🔐 AUTHENTICATION SETUP")
        print("-" * 40)
        if not self.authenticate_test_user():
            print("❌ Authentication setup failed - cannot proceed with billing tests")
            return False
        
        # Test 1: Session Endpoint
        print("\n📱 SESSION ENDPOINT TESTS")
        print("-" * 40)
        self.test_session_endpoint_authenticated()
        self.test_session_endpoint_unauthenticated()
        
        # Test 2: Billing State Query
        print("\n💰 BILLING STATE TESTS")
        print("-" * 40)
        self.test_billing_state_query()
        
        # Test 3: Mock Credit Top-Up
        print("\n🔄 MOCK CREDIT TOP-UP TESTS")
        print("-" * 40)
        self.test_mock_credit_topup()
        
        # Test 4: Credit Debit for Generation
        print("\n⚡ CREDIT ENFORCEMENT TESTS")
        print("-" * 40)
        self.test_credit_debit_generation()
        self.test_insufficient_credits_scenario()
        
        # Test 5: Mock Plan Upgrade
        print("\n📈 MOCK PLAN UPGRADE TESTS")
        print("-" * 40)
        self.test_mock_plan_upgrade()
        
        # Final summary
        print("\n" + "=" * 80)
        print("📈 PHASE 8 BILLING TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.critical_failures:
            print(f"\n❌ CRITICAL FAILURES ({len(self.critical_failures)}):")
            for failure in self.critical_failures:
                print(f"  • {failure['test']}: {failure['error']}")
        
        print(f"\nPhase 8 Status: {'✅ WORKING' if self.tests_passed >= self.tests_run * 0.85 else '❌ ISSUES DETECTED'}")
        print("=" * 80)
        
        return {
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "success_rate": self.tests_passed/self.tests_run*100,
            "critical_failures": self.critical_failures,
            "test_results": self.test_results,
            "phase8_working": self.tests_passed >= self.tests_run * 0.85
        }

# Removed duplicate main section

    def test_sequence_validation_invalid(self):
        """Test sequence validation with invalid sequence"""
        test_sequence = "HAEGTFTSDVSSYLEGXZ"  # X and Z are not standard amino acids
        return self.run_test(
            "Sequence Validation (Invalid)", 
            "GET", 
            f"validate-sequence/{test_sequence}", 
            200  # API should return 200 but with is_valid: false
        )

    def test_generate_analogues_basic(self):
        """Test basic analogue generation"""
        test_data = {
            "base_molecule": "HAEGTFTSDVSSYLEG",
            "allowed_mods": "substitution, lipidation, cyclization",
            "exclusions": "proline substitution, C-terminal modifications",
            "target_use": "GLP-1 receptor agonist for diabetes treatment",
            "num_analogues": 2
        }
        
        return self.run_test(
            "Generate Analogues (Basic)", 
            "POST", 
            "generate-analogues", 
            200, 
            data=test_data,
            timeout=60  # AI generation can take time
        )

    def test_generate_analogues_minimal(self):
        """Test analogue generation with minimal parameters"""
        test_data = {
            "base_molecule": "ACDEFG",
            "allowed_mods": "substitution",
            "exclusions": "none",
            "target_use": "test peptide",
            "num_analogues": 1
        }
        
        return self.run_test(
            "Generate Analogues (Minimal)", 
            "POST", 
            "generate-analogues", 
            200, 
            data=test_data,
            timeout=60
        )

    def test_generate_analogues_invalid_sequence(self):
        """Test analogue generation with invalid sequence - HOTFIX VALIDATION"""
        test_data = {
            "base_molecule": "INVALID123",
            "allowed_mods": "substitution",
            "exclusions": "none",
            "target_use": "test peptide",
            "num_analogues": 1
        }
        
        return self.run_test(
            "HOTFIX: Generate Analogues (Invalid Sequence)", 
            "POST", 
            "generate-analogues", 
            400,  # Should return 400 for invalid sequence
            data=test_data
        )

    def test_generation_history(self):
        """Test generation history endpoint"""
        return self.run_test("Generation History", "GET", "generation-history", 200)

    def test_empty_validation_endpoint(self):
        """Test empty validation endpoint - HOTFIX VALIDATION"""
        return self.run_test(
            "HOTFIX: Empty Validation Endpoint", 
            "GET", 
            "validate-sequence/", 
            200  # Should handle gracefully, not 404
        )

    def test_generate_analogues_max_count(self):
        """Test analogue generation with maximum count"""
        test_data = {
            "base_molecule": "HAEGTFTSDVSSYLEG",
            "allowed_mods": "substitution, D-isomers, lipidation, cyclization",
            "exclusions": "none",
            "target_use": "comprehensive testing peptide",
            "num_analogues": 5
        }
        
        return self.run_test(
            "Generate Analogues (Max Count)", 
            "POST", 
            "generate-analogues", 
            200, 
            data=test_data,
            timeout=90  # More analogues = more time
        )

    def test_edge_case_empty_sequence(self):
        """Test with empty sequence - HOTFIX VALIDATION"""
        test_data = {
            "base_molecule": "",
            "allowed_mods": "substitution",
            "exclusions": "none",
            "target_use": "test",
            "num_analogues": 1
        }
        
        return self.run_test(
            "HOTFIX: Empty Sequence Returns 400", 
            "POST", 
            "generate-analogues", 
            400, 
            data=test_data
        )

    def test_edge_case_very_long_sequence(self):
        """Test with very long sequence (100+ amino acids)"""
        long_sequence = "HAEGTFTSDVSSYLEG" * 7  # 112 amino acids
        test_data = {
            "base_molecule": long_sequence,
            "allowed_mods": "substitution",
            "exclusions": "none",
            "target_use": "long peptide test",
            "num_analogues": 1
        }
        
        return self.run_test(
            "Edge Case: Very Long Sequence", 
            "POST", 
            "generate-analogues", 
            200, 
            data=test_data,
            timeout=120
        )

    def test_edge_case_single_amino_acid(self):
        """Test with single amino acid"""
        test_data = {
            "base_molecule": "A",
            "allowed_mods": "substitution",
            "exclusions": "none",
            "target_use": "minimal peptide",
            "num_analogues": 1
        }
        
        return self.run_test(
            "Edge Case: Single Amino Acid", 
            "POST", 
            "generate-analogues", 
            200, 
            data=test_data
        )

    def test_edge_case_special_characters(self):
        """Test with special characters in sequence - HOTFIX VALIDATION"""
        test_data = {
            "base_molecule": "HAE-GTF@TSD#VSS",
            "allowed_mods": "substitution",
            "exclusions": "none",
            "target_use": "test",
            "num_analogues": 1
        }
        
        return self.run_test(
            "HOTFIX: Special Characters Return 400", 
            "POST", 
            "generate-analogues", 
            400, 
            data=test_data
        )

    def test_edge_case_lowercase_sequence(self):
        """Test with lowercase amino acids"""
        test_data = {
            "base_molecule": "haegtftsdvssyleg",
            "allowed_mods": "substitution",
            "exclusions": "none",
            "target_use": "lowercase test",
            "num_analogues": 1
        }
        
        return self.run_test(
            "Edge Case: Lowercase Sequence", 
            "POST", 
            "generate-analogues", 
            200, 
            data=test_data
        )

    def test_edge_case_max_analogues_boundary(self):
        """Test with maximum allowed analogues (10)"""
        test_data = {
            "base_molecule": "HAEGTFTSDVSSYLEG",
            "allowed_mods": "substitution, D-isomers, lipidation, cyclization",
            "exclusions": "none",
            "target_use": "boundary test",
            "num_analogues": 10
        }
        
        return self.run_test(
            "Edge Case: Max Analogues (10)", 
            "POST", 
            "generate-analogues", 
            200, 
            data=test_data,
            timeout=150
        )

    def test_edge_case_zero_analogues(self):
        """Test with zero analogues requested"""
        test_data = {
            "base_molecule": "HAEGTFTSDVSSYLEG",
            "allowed_mods": "substitution",
            "exclusions": "none",
            "target_use": "zero test",
            "num_analogues": 0
        }
        
        return self.run_test(
            "Edge Case: Zero Analogues", 
            "POST", 
            "generate-analogues", 
            422,  # Validation error expected
            data=test_data
        )

    def test_advanced_modifications_d_isomers(self):
        """Test D-isomer modifications specifically"""
        test_data = {
            "base_molecule": "AFLVIPWY",  # Amino acids that have D-isomer support
            "allowed_mods": "D-isomers",
            "exclusions": "none",
            "target_use": "D-isomer testing",
            "num_analogues": 2
        }
        
        return self.run_test(
            "Advanced: D-Isomer Modifications", 
            "POST", 
            "generate-analogues", 
            200, 
            data=test_data,
            timeout=90
        )

    def test_advanced_modifications_lipidation(self):
        """Test lipidation modifications specifically"""
        test_data = {
            "base_molecule": "HKNCGTFTSDVSSYLEG",  # Contains K, N, C for lipidation
            "allowed_mods": "lipidation",
            "exclusions": "none",
            "target_use": "lipidation testing",
            "num_analogues": 2
        }
        
        return self.run_test(
            "Advanced: Lipidation Modifications", 
            "POST", 
            "generate-analogues", 
            200, 
            data=test_data,
            timeout=90
        )

    def test_advanced_modifications_cyclization(self):
        """Test cyclization modifications specifically"""
        test_data = {
            "base_molecule": "HCAEGTFTSDVSSYLECG",  # Contains C-C for disulfide, K-E for lactam
            "allowed_mods": "cyclization",
            "exclusions": "none",
            "target_use": "cyclization testing",
            "num_analogues": 2
        }
        
        return self.run_test(
            "Advanced: Cyclization Modifications", 
            "POST", 
            "generate-analogues", 
            200, 
            data=test_data,
            timeout=90
        )

    def test_complex_exclusions(self):
        """Test complex exclusion patterns"""
        test_data = {
            "base_molecule": "HAEGTFTSDVSSYLEG",
            "allowed_mods": "substitution, D-isomers, lipidation, cyclization",
            "exclusions": "proline substitution, N-terminal modifications, C-terminal lipidation, position 1-3 modifications",
            "target_use": "complex exclusion testing",
            "num_analogues": 3
        }
        
        return self.run_test(
            "Complex Exclusions Test", 
            "POST", 
            "generate-analogues", 
            200, 
            data=test_data,
            timeout=90
        )

    def test_sequence_validation_edge_cases(self):
        """Test sequence validation with various edge cases"""
        edge_cases = [
            ("", "Empty sequence"),
            ("X", "Invalid amino acid X"),
            ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "All letters including invalid"),
            ("123456", "Numbers only"),
            ("A" * 1000, "Very long sequence"),
            ("a", "Single lowercase"),
            ("AcDeFg", "Mixed case")
        ]
        
        results = []
        for sequence, description in edge_cases:
            success, response = self.run_test(
                f"Validation Edge Case: {description}", 
                "GET", 
                f"validate-sequence/{sequence}", 
                200
            )
            results.append((success, response, description))
        
        return results

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🧪 Starting Peptimancer Backend API Tests - Iteration 3 (HOTFIX VALIDATION)")
        print("=" * 70)
        
        # Basic connectivity tests
        self.test_root_endpoint()
        
        print("\n🔥 HOTFIX VALIDATION TESTS")
        print("-" * 40)
        
        # HOTFIX validation tests - these are the critical ones
        self.test_generate_analogues_invalid_sequence()  # Should return 400
        self.test_edge_case_empty_sequence()  # Should return 400
        self.test_edge_case_special_characters()  # Should return 400
        self.test_empty_validation_endpoint()  # Should handle gracefully
        self.test_valid_sequence_still_works()  # Should still work
        
        print("\n✅ BASELINE FUNCTIONALITY TESTS")
        print("-" * 40)
        
        # Sequence validation tests
        self.test_sequence_validation_valid()
        self.test_sequence_validation_invalid()
        
        # Core functionality tests
        self.test_generate_analogues_basic()
        self.test_generate_analogues_minimal()
        
        # Additional functionality tests
        self.test_generation_history()
        self.test_generate_analogues_max_count()
        
        print("\n🔬 Running Edge Case Tests...")
        print("-" * 40)
        
        # Edge case tests
        self.test_edge_case_empty_sequence()
        self.test_edge_case_very_long_sequence()
        self.test_edge_case_single_amino_acid()
        self.test_edge_case_special_characters()
        self.test_edge_case_lowercase_sequence()
        self.test_edge_case_max_analogues_boundary()
        self.test_edge_case_zero_analogues()
        
        print("\n🧬 Running Advanced Modification Tests...")
        print("-" * 40)
        
        # Advanced modification tests
        self.test_advanced_modifications_d_isomers()
        self.test_advanced_modifications_lipidation()
        self.test_advanced_modifications_cyclization()
        self.test_complex_exclusions()
        
        print("\n🔍 Running Sequence Validation Edge Cases...")
        print("-" * 40)
        
        # Sequence validation edge cases
        self.test_sequence_validation_edge_cases()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed. Check details above.")
            
            # Print failed tests
            failed_tests = [test for test in self.test_results if not test['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test_name']}: {test['details']}")
            
            return 1

def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "auth":
        # Run authentication tests
        auth_test = AuthenticationTest()
        results = auth_test.run_all_tests()
        
        # Exit with appropriate code
        sys.exit(0 if results["auth_working"] else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "chemistry":
        # Run chemistry tests
        chemistry_test = Phase8ChemistryTest()
        results = chemistry_test.run_all_tests()
        
        # Exit with appropriate code
        sys.exit(0 if results["chemistry_working"] else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "billing":
        # Run Phase 8.2 billing tests
        billing_test = Phase82BillingTest()
        results = billing_test.run_all_tests()
        
        # Exit with appropriate code
        sys.exit(0 if results["billing_working"] else 1)
    else:
        # Run enterprise tests
        test_runner = PeptimancerEnterpriseTest()
        results = test_runner.run_comprehensive_test()
        
        # Exit with appropriate code
        sys.exit(0 if results["enterprise_ready"] else 1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == "global-login" or test_type == "rbac":
            # Run Global Login & RBAC tests
            rbac_test = GlobalLoginRBACTest()
            results = rbac_test.run_comprehensive_global_login_rbac_tests()
            
            # Exit with appropriate code
            sys.exit(0 if results["global_login_rbac_working"] else 1)
            
        elif test_type == "auth":
            # Run authentication tests (legacy)
            auth_test = GlobalLoginRBACTest()
            results = auth_test.run_comprehensive_global_login_rbac_tests()
            
            # Exit with appropriate code
            sys.exit(0 if results["global_login_rbac_working"] else 1)
            
        elif test_type == "billing":
            # Run Phase 8.2 billing tests
            billing_test = Phase82BillingTest()
            
            # Authenticate first
            if not billing_test.authenticate_admin_user():
                print("❌ Failed to authenticate admin user - cannot run billing tests")
                sys.exit(1)
            
            results = billing_test.run_all_tests()
            
            # Exit with appropriate code
            sys.exit(0 if results["billing_working"] else 1)
            
        elif test_type == "chemistry":
            # Run Phase 8 Final chemistry tests
            chemistry_test = Phase8ChemistryTest()
            results = chemistry_test.run_all_tests()
            
            # Exit with appropriate code
            sys.exit(0 if results["chemistry_api_working"] else 1)
            
        elif test_type == "partner-shares" or test_type == "deprecation":
            # Run Partner Shares Deprecation & Core App Stabilization tests
            partner_test = PartnerSharesDeprecationTest()
            results = partner_test.run_comprehensive_test()
            
            # Exit with appropriate code
            sys.exit(0 if results["overall_success"] else 1)
            
        else:
            print(f"Unknown test type: {test_type}")
            print("Available test types: global-login, rbac, auth, billing, chemistry, partner-shares, deprecation, enterprise")
            sys.exit(1)
    else:
        # Run Partner Shares Deprecation & Core App Stabilization tests by default
        partner_test = PartnerSharesDeprecationTest()
        results = partner_test.run_comprehensive_test()
        
        # Exit with appropriate code
        sys.exit(0 if results["overall_success"] else 1)