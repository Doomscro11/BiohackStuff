#!/usr/bin/env python3
"""
Phase VI Production Enterprise Launch - Backend API Testing
Comprehensive validation for Peptimancer enterprise deployment
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
BACKEND_URL = "https://peptide-architect-1.preview.emergentagent.com"
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
            error_details += "Failures: " + ", ".join([
                f"Req{r['request_id']}: {r.get('error', f'HTTP {r.get(\"status_code\", \"unknown\")}')} "
                for r in results if not r.get('success', False)
            ])
            
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

if __name__ == "__main__":
    tester = PeptimancerEnterpriseTest()
    results = tester.run_comprehensive_test()
    
    # Save results for analysis
    with open('/app/phase6_enterprise_validation.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Exit with appropriate code
    sys.exit(0 if results['enterprise_ready'] else 1)
                try:
                    response_data = response.json()
                    details = f"Status: {response.status_code}, Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}"
                except:
                    details = f"Status: {response.status_code}, Response length: {len(response.text)}"
            else:
                details = f"Expected {expected_status}, got {response.status_code}. Response: {response.text[:200]}"
            
            self.log_test(name, success, details)
            return success, response.json() if success and response.text else {}

        except requests.exceptions.Timeout:
            self.log_test(name, False, f"Request timed out after {timeout} seconds")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_sequence_validation_valid(self):
        """Test sequence validation with valid sequence"""
        test_sequence = "HAEGTFTSDVSSYLEG"
        return self.run_test(
            "Sequence Validation (Valid)", 
            "GET", 
            f"validate-sequence/{test_sequence}", 
            200
        )

    def test_valid_sequence_still_works(self):
        """Test that valid sequences still work correctly after hotfixes"""
        test_sequence = "HAEGTFTSDVSSYLEG"
        success, response = self.run_test(
            "HOTFIX: Valid Sequences Still Work", 
            "GET", 
            f"validate-sequence/{test_sequence}", 
            200
        )
        
        if success and response.get('is_valid') == True:
            self.log_test("Valid Sequence Processing", True, f"Sequence correctly validated as valid")
            return True, response
        else:
            self.log_test("Valid Sequence Processing", False, f"Valid sequence not properly validated")
            return False, response

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
    tester = PeptimancerAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())