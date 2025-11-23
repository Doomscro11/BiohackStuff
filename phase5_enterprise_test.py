#!/usr/bin/env python3
"""
Phase V Commercial Rollout Validation - Backend API Testing
Comprehensive validation of all Phase III systems under production conditions
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class PeptimancerEnterpriseValidator:
    def __init__(self, base_url="https://rbac-shield.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []
        self.test_results = []
        
        # Test data for enterprise validation
        self.test_sequence = "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR"
        self.invalid_sequence = "INVALID123"
        self.test_generation_id = None
        self.test_vault_ids = []
        self.test_token_id = None

    def log_test(self, name: str, success: bool, details: str = "", error: str = "", critical: bool = False):
        """Log test result with enterprise-grade detail"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            if critical:
                self.critical_failures.append(f"{name}: {error}")
        
        result = {
            "test_name": name,
            "status": "PASS" if success else "FAIL",
            "details": details,
            "error": error,
            "critical": critical,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        print(f"{status} {name}")
        if details:
            print(f"    Details: {details}")
        if error:
            print(f"    Error: {error}")
        print()

    def test_api_health(self) -> bool:
        """Test basic API connectivity and health"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"API Version: {data.get('version', 'Unknown')}"
            else:
                details = f"Status Code: {response.status_code}"
                
            self.log_test("API Health Check", success, details, 
                         "" if success else f"HTTP {response.status_code}", critical=True)
            return success
            
        except Exception as e:
            self.log_test("API Health Check", False, "", str(e), critical=True)
            return False

    def test_sequence_validation(self) -> bool:
        """Test sequence validation system"""
        try:
            # Test valid sequence
            response = requests.get(f"{self.api_url}/validate-sequence/{self.test_sequence}", timeout=10)
            valid_success = response.status_code == 200 and response.json().get('is_valid', False)
            
            # Test invalid sequence
            response2 = requests.get(f"{self.api_url}/validate-sequence/{self.invalid_sequence}", timeout=10)
            invalid_success = response2.status_code == 200 and not response2.json().get('is_valid', True)
            
            success = valid_success and invalid_success
            details = f"Valid seq: {valid_success}, Invalid seq: {invalid_success}"
            
            self.log_test("Sequence Validation System", success, details, 
                         "" if success else "Validation logic failed")
            return success
            
        except Exception as e:
            self.log_test("Sequence Validation System", False, "", str(e))
            return False

    def test_analogue_generation(self) -> bool:
        """Test core analogue generation with enterprise parameters"""
        try:
            payload = {
                "base_molecule": self.test_sequence,
                "allowed_mods": "Substitution, Lipidation, Cyclization, D-isomers",
                "exclusions": "No Aib or γ-Glu residues",
                "target_use": "Enterprise Validation Testing",
                "num_analogues": 3,
                "include_cost": True
            }
            
            response = requests.post(f"{self.api_url}/generate-analogues", json=payload, timeout=60)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.test_generation_id = data.get('request_id')
                analogues = data.get('analogues', [])
                self.test_vault_ids = [a.get('vault_id') for a in analogues if a.get('vault_id')]
                
                details = f"Generated {len(analogues)} analogues, Generation ID: {self.test_generation_id}"
                
                # Validate enterprise-grade fields
                enterprise_fields_valid = all(
                    analogue.get('vault_id') and 
                    analogue.get('patent_similarity_risk') and
                    analogue.get('novelty_score') is not None and
                    analogue.get('binding_affinity') is not None
                    for analogue in analogues
                )
                
                if not enterprise_fields_valid:
                    success = False
                    details += " - Missing enterprise fields"
            else:
                details = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    details += f" - {error_detail}"
                except:
                    pass
            
            self.log_test("Analogue Generation (Enterprise)", success, details, 
                         "" if success else f"Generation failed: {details}", critical=True)
            return success
            
        except Exception as e:
            self.log_test("Analogue Generation (Enterprise)", False, "", str(e), critical=True)
            return False

    def test_pdf_export_system(self) -> bool:
        """Test PDF export consistency and watermark rendering"""
        if not self.test_generation_id:
            self.log_test("PDF Export System", False, "", "No generation ID available", critical=True)
            return False
            
        try:
            payload = {
                "generation_id": self.test_generation_id,
                "format": "pdf",
                "include_cost": True,
                "include_ip_analysis": True,
                "watermark": True
            }
            
            response = requests.post(f"{self.api_url}/export-report", json=payload, timeout=30)
            success = response.status_code == 200
            
            if success:
                # Check if we got a PDF file
                content_type = response.headers.get('content-type', '')
                is_pdf = 'application/pdf' in content_type
                file_size = len(response.content)
                
                details = f"PDF generated, Size: {file_size} bytes, Content-Type: {content_type}"
                
                if not is_pdf or file_size < 1000:  # Minimum reasonable PDF size
                    success = False
                    details += " - Invalid PDF format or too small"
            else:
                details = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    details += f" - {error_detail}"
                except:
                    pass
            
            self.log_test("PDF Export System", success, details, 
                         "" if success else f"PDF export failed: {details}", critical=True)
            return success
            
        except Exception as e:
            self.log_test("PDF Export System", False, "", str(e), critical=True)
            return False

    def test_cro_integration(self) -> bool:
        """Test CRO webhook integration and partner response synchronization"""
        if not self.test_vault_ids:
            self.log_test("CRO Integration System", False, "", "No vault IDs available")
            return False
            
        try:
            vault_id = self.test_vault_ids[0]
            payload = {
                "vault_id": vault_id,
                "partner_name": "Enterprise Test CRO",
                "quantity_mg": 500.0,
                "purity_requirement": 98.0,
                "timeline_days": 21,
                "contact_email": "enterprise@test.com",
                "additional_notes": "Phase V commercial validation test"
            }
            
            response = requests.post(f"{self.api_url}/request-synthesis", json=payload, timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                partner_response = data.get('partner_response', {})
                partner_ref = partner_response.get('partner_reference', '')
                
                details = f"Partner Ref: {partner_ref}, Status: {data.get('status')}"
                
                # Validate enterprise integration fields
                required_fields = ['synthesis_request_id', 'vault_id', 'partner_response', 'status']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details += f" - Missing fields: {missing_fields}"
            else:
                details = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    details += f" - {error_detail}"
                except:
                    pass
            
            self.log_test("CRO Integration System", success, details, 
                         "" if success else f"CRO integration failed: {details}")
            return success
            
        except Exception as e:
            self.log_test("CRO Integration System", False, "", str(e))
            return False

    def test_token_management(self) -> bool:
        """Test Pro Vault token management under load"""
        try:
            # Create token
            response = requests.post(f"{self.api_url}/vault-tokens/create", 
                                   params={"user_id": "enterprise_test_user", "tier": "enterprise", "credits": 1000}, 
                                   timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.test_token_id = data.get('token_id')
                details = f"Token ID: {self.test_token_id}, Tier: {data.get('tier')}, Credits: {data.get('credits')}"
                
                # Test token retrieval
                if self.test_token_id:
                    response2 = requests.get(f"{self.api_url}/vault-tokens/{self.test_token_id}", timeout=10)
                    retrieval_success = response2.status_code == 200
                    
                    if not retrieval_success:
                        success = False
                        details += " - Token retrieval failed"
            else:
                details = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    details += f" - {error_detail}"
                except:
                    pass
            
            self.log_test("Token Management System", success, details, 
                         "" if success else f"Token management failed: {details}", critical=True)
            return success
            
        except Exception as e:
            self.log_test("Token Management System", False, "", str(e), critical=True)
            return False

    def test_vault_ledger_integrity(self) -> bool:
        """Test vault ledger audit trail integrity"""
        try:
            response = requests.get(f"{self.api_url}/vault-ledger", params={"limit": 10}, timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                ledger_entries = data.get('ledger_entries', [])
                total_entries = data.get('total_entries', 0)
                
                details = f"Retrieved {len(ledger_entries)} entries, Total: {total_entries}"
                
                # Validate ledger entry structure
                if ledger_entries:
                    first_entry = ledger_entries[0]
                    required_fields = ['vault_id', 'generation_id', 'timestamp', 'analogue_data']
                    missing_fields = [field for field in required_fields if field not in first_entry]
                    
                    if missing_fields:
                        success = False
                        details += f" - Missing fields: {missing_fields}"
                    
                    # Test specific vault entry retrieval
                    if success and self.test_vault_ids:
                        vault_id = self.test_vault_ids[0]
                        response2 = requests.get(f"{self.api_url}/vault-ledger/{vault_id}", timeout=10)
                        specific_success = response2.status_code == 200
                        
                        if not specific_success:
                            details += f" - Specific entry retrieval failed for {vault_id}"
            else:
                details = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    details += f" - {error_detail}"
                except:
                    pass
            
            self.log_test("Vault Ledger Integrity", success, details, 
                         "" if success else f"Vault ledger failed: {details}", critical=True)
            return success
            
        except Exception as e:
            self.log_test("Vault Ledger Integrity", False, "", str(e), critical=True)
            return False

    def test_generation_history(self) -> bool:
        """Test generation history retrieval for audit trails"""
        try:
            response = requests.get(f"{self.api_url}/generation-history", timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                history_count = len(data) if isinstance(data, list) else 0
                details = f"Retrieved {history_count} generation records"
                
                # Validate history entry structure
                if data and isinstance(data, list) and len(data) > 0:
                    first_record = data[0]
                    required_fields = ['request_id', 'timestamp', 'base_molecule', 'analogues']
                    missing_fields = [field for field in required_fields if field not in first_record]
                    
                    if missing_fields:
                        success = False
                        details += f" - Missing fields: {missing_fields}"
            else:
                details = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    details += f" - {error_detail}"
                except:
                    pass
            
            self.log_test("Generation History System", success, details, 
                         "" if success else f"History retrieval failed: {details}")
            return success
            
        except Exception as e:
            self.log_test("Generation History System", False, "", str(e))
            return False

    def test_error_resilience(self) -> bool:
        """Test graceful handling of network failures, database timeouts, API errors"""
        try:
            # Test invalid generation ID for export
            response = requests.post(f"{self.api_url}/export-report", 
                                   json={"generation_id": "invalid-id-12345"}, timeout=10)
            
            # Should return 404, not 500
            proper_error_handling = response.status_code == 404
            
            # Test invalid vault ID
            response2 = requests.get(f"{self.api_url}/vault-ledger/invalid-vault-id", timeout=10)
            proper_error_handling2 = response2.status_code == 404
            
            # Test invalid token ID
            response3 = requests.get(f"{self.api_url}/vault-tokens/invalid-token-id", timeout=10)
            proper_error_handling3 = response3.status_code == 404
            
            success = proper_error_handling and proper_error_handling2 and proper_error_handling3
            details = f"Export: {response.status_code}, Vault: {response2.status_code}, Token: {response3.status_code}"
            
            if not success:
                details += " - Should return 404 for not found, not 500"
            
            self.log_test("Error Resilience & HTTP Status Codes", success, details, 
                         "" if success else "Improper error handling detected")
            return success
            
        except Exception as e:
            self.log_test("Error Resilience & HTTP Status Codes", False, "", str(e))
            return False

    def test_load_simulation(self) -> bool:
        """Test multiple simultaneous users generating analogues"""
        try:
            # Simulate 3 concurrent requests
            import threading
            import time
            
            results = []
            
            def generate_analogue(thread_id):
                try:
                    payload = {
                        "base_molecule": "HAEGTFTSDVSSYLEG",
                        "allowed_mods": "Substitution, D-isomers",
                        "exclusions": "none",
                        "target_use": f"Load test thread {thread_id}",
                        "num_analogues": 2,
                        "include_cost": False
                    }
                    
                    response = requests.post(f"{self.api_url}/generate-analogues", json=payload, timeout=60)
                    results.append((thread_id, response.status_code == 200))
                except Exception as e:
                    results.append((thread_id, False))
            
            # Start threads
            threads = []
            for i in range(3):
                thread = threading.Thread(target=generate_analogue, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for completion
            for thread in threads:
                thread.join()
            
            # Check results
            successful_requests = sum(1 for _, success in results if success)
            success = successful_requests >= 2  # At least 2 out of 3 should succeed
            
            details = f"Concurrent requests: {len(results)}, Successful: {successful_requests}"
            
            self.log_test("Load Testing (Concurrent Users)", success, details, 
                         "" if success else "Load testing failed")
            return success
            
        except Exception as e:
            self.log_test("Load Testing (Concurrent Users)", False, "", str(e))
            return False

    def run_enterprise_validation(self) -> Dict[str, Any]:
        """Run complete Phase V commercial rollout validation"""
        print("🚀 PHASE V COMMERCIAL ROLLOUT VALIDATION")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print()
        
        # Core Infrastructure Tests
        print("📋 CORE INFRASTRUCTURE VALIDATION")
        print("-" * 40)
        self.test_api_health()
        self.test_sequence_validation()
        self.test_analogue_generation()
        
        # Phase III Enterprise Features
        print("🏢 PHASE III ENTERPRISE FEATURES")
        print("-" * 40)
        self.test_pdf_export_system()
        self.test_cro_integration()
        self.test_token_management()
        self.test_vault_ledger_integrity()
        self.test_generation_history()
        
        # Enterprise Readiness
        print("🔒 ENTERPRISE READINESS VALIDATION")
        print("-" * 40)
        self.test_error_resilience()
        self.test_load_simulation()
        
        # Results Summary
        print("📊 VALIDATION RESULTS")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Critical Failures: {len(self.critical_failures)}")
        
        if self.critical_failures:
            print("\n🚨 CRITICAL DEPLOYMENT BLOCKERS:")
            for failure in self.critical_failures:
                print(f"  - {failure}")
        
        # Commercial Readiness Assessment
        commercial_ready = success_rate >= 90 and len(self.critical_failures) == 0
        
        print(f"\n🎯 COMMERCIAL READINESS: {'✅ READY' if commercial_ready else '❌ NOT READY'}")
        
        if not commercial_ready:
            print("⚠️  Enterprise deployment NOT RECOMMENDED until critical issues are resolved")
        else:
            print("✅ System validated for enterprise deployment")
        
        return {
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "success_rate": success_rate,
            "critical_failures": self.critical_failures,
            "commercial_ready": commercial_ready,
            "test_results": self.test_results,
            "validation_timestamp": datetime.now().isoformat()
        }

def main():
    """Main validation execution"""
    validator = PeptimancerEnterpriseValidator()
    results = validator.run_enterprise_validation()
    
    # Save detailed results
    with open('/app/phase5_validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Return appropriate exit code
    return 0 if results['commercial_ready'] else 1

if __name__ == "__main__":
    sys.exit(main())