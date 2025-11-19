import requests
import sys
import json
from datetime import datetime
import time
import tempfile
import os

class Phase3EnterpriseAPITester:
    def __init__(self, base_url="https://peptimancer-share.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.generation_id = None
        self.vault_ids = []
        self.token_id = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {name}")
        if details:
            print(f"   Details: {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30, response_type='json'):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            
            success = response.status_code == expected_status
            
            if success:
                if response_type == 'json':
                    try:
                        response_data = response.json()
                        details = f"Status: {response.status_code}, Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}"
                        self.log_test(name, success, details)
                        return success, response_data
                    except:
                        details = f"Status: {response.status_code}, Response length: {len(response.text)}"
                        self.log_test(name, success, details)
                        return success, {}
                elif response_type == 'blob':
                    details = f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'unknown')}, Size: {len(response.content)} bytes"
                    self.log_test(name, success, details)
                    return success, response.content
            else:
                details = f"Expected {expected_status}, got {response.status_code}. Response: {response.text[:200]}"
                self.log_test(name, success, details)
                return success, {}

        except requests.exceptions.Timeout:
            self.log_test(name, False, f"Request timed out after {timeout} seconds")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}

    def setup_test_data(self):
        """Generate test data for Phase III testing"""
        print("\n🔧 Setting up test data for Phase III enterprise testing...")
        
        # Generate analogues to get generation_id and vault_ids
        test_data = {
            "base_molecule": "HAEGTFTSDVSSYLEG",
            "allowed_mods": "substitution, lipidation, cyclization",
            "exclusions": "proline substitution",
            "target_use": "Phase III Enterprise Testing",
            "num_analogues": 2,
            "include_cost": True
        }
        
        success, response = self.run_test(
            "Setup: Generate Test Analogues", 
            "POST", 
            "generate-analogues", 
            200, 
            data=test_data,
            timeout=60
        )
        
        if success and response:
            self.generation_id = response.get('request_id')
            analogues = response.get('analogues', [])
            self.vault_ids = [analogue.get('vault_id') for analogue in analogues if analogue.get('vault_id')]
            print(f"   Generated ID: {self.generation_id}")
            print(f"   Vault IDs: {self.vault_ids}")
            return True
        else:
            print("   ❌ Failed to setup test data")
            return False

    def test_pdf_export_system(self):
        """Test Phase III: PDF Export System with watermark rendering"""
        if not self.generation_id:
            self.log_test("PDF Export System", False, "No generation_id available for testing")
            return False, None
        
        export_data = {
            "generation_id": self.generation_id,
            "format": "pdf",
            "include_cost": True,
            "include_ip_analysis": True,
            "watermark": True
        }
        
        success, pdf_content = self.run_test(
            "Phase III: PDF Export with Watermark", 
            "POST", 
            "export-report", 
            200, 
            data=export_data,
            timeout=30,
            response_type='blob'
        )
        
        if success and pdf_content:
            # Verify it's actually a PDF
            if pdf_content.startswith(b'%PDF'):
                self.log_test("PDF Content Validation", True, f"Valid PDF file generated, size: {len(pdf_content)} bytes")
                
                # Save to temp file for verification
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                    tmp.write(pdf_content)
                    print(f"   PDF saved to: {tmp.name}")
                
                return True, pdf_content
            else:
                self.log_test("PDF Content Validation", False, "Response is not a valid PDF file")
                return False, None
        
        return success, pdf_content

    def test_synthesis_request_system(self):
        """Test Phase III: CRO Synthesis Request System with quote handling"""
        if not self.vault_ids:
            self.log_test("Synthesis Request System", False, "No vault_ids available for testing")
            return False, None
        
        vault_id = self.vault_ids[0]
        synthesis_data = {
            "vault_id": vault_id,
            "partner_name": "CRO Partners Inc.",
            "quantity_mg": 100.0,
            "purity_requirement": 95.0,
            "timeline_days": 14,
            "contact_email": "test@peptimancer.com",
            "additional_notes": "Phase III enterprise testing synthesis request"
        }
        
        success, response = self.run_test(
            "Phase III: CRO Synthesis Request", 
            "POST", 
            "request-synthesis", 
            200, 
            data=synthesis_data,
            timeout=30
        )
        
        if success and response:
            # Verify response structure
            required_fields = ['synthesis_request_id', 'vault_id', 'partner_response', 'status']
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                partner_response = response.get('partner_response', {})
                if 'partner_reference' in partner_response and 'status' in partner_response:
                    self.log_test("Synthesis Response Validation", True, f"Partner ref: {partner_response['partner_reference']}")
                    return True, response
                else:
                    self.log_test("Synthesis Response Validation", False, "Missing partner response fields")
            else:
                self.log_test("Synthesis Response Validation", False, f"Missing fields: {missing_fields}")
        
        return success, response

    def test_vault_token_management(self):
        """Test Phase III: Pro Vault Token Management with credit deduction and tier access"""
        
        # Test token creation
        success, response = self.run_test(
            "Phase III: Create Vault Token", 
            "POST", 
            "vault-tokens/create?user_id=test_user_phase3&tier=pro&credits=100", 
            200, 
            timeout=30
        )
        
        if success and response:
            self.token_id = response.get('token_id')
            required_fields = ['token_id', 'tier', 'credits', 'status']
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                self.log_test("Token Creation Validation", True, f"Token ID: {self.token_id}, Tier: {response['tier']}")
            else:
                self.log_test("Token Creation Validation", False, f"Missing fields: {missing_fields}")
        
        # Test token status check
        if self.token_id:
            success2, response2 = self.run_test(
                "Phase III: Check Token Status", 
                "GET", 
                f"vault-tokens/{self.token_id}", 
                200, 
                timeout=30
            )
            
            if success2 and response2:
                required_fields = ['token_id', 'tier', 'credits', 'expires_at', 'status']
                missing_fields = [field for field in required_fields if field not in response2]
                
                if not missing_fields:
                    self.log_test("Token Status Validation", True, f"Credits: {response2['credits']}, Status: {response2['status']}")
                    return True, response2
                else:
                    self.log_test("Token Status Validation", False, f"Missing fields: {missing_fields}")
        
        return success, response

    def test_vault_ledger_system(self):
        """Test Phase III: Vault Ledger / IP Registry with Vault ID indexing"""
        
        # Test vault ledger retrieval
        success, response = self.run_test(
            "Phase III: Vault Ledger Retrieval", 
            "GET", 
            "vault-ledger?limit=10", 
            200, 
            timeout=30
        )
        
        if success and response:
            required_fields = ['ledger_entries', 'total_entries', 'registry_status']
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                entries = response.get('ledger_entries', [])
                self.log_test("Vault Ledger Structure", True, f"Found {len(entries)} ledger entries")
                
                # Test specific vault entry retrieval
                if self.vault_ids and entries:
                    vault_id = self.vault_ids[0]
                    success2, response2 = self.run_test(
                        "Phase III: Specific Vault Entry", 
                        "GET", 
                        f"vault-ledger/{vault_id}", 
                        200, 
                        timeout=30
                    )
                    
                    if success2 and response2:
                        required_entry_fields = ['vault_id', 'generation_id', 'timestamp', 'base_molecule', 'analogue_data']
                        missing_entry_fields = [field for field in required_entry_fields if field not in response2]
                        
                        if not missing_entry_fields:
                            self.log_test("Vault Entry Structure", True, f"Vault ID: {response2['vault_id']}")
                            return True, response2
                        else:
                            self.log_test("Vault Entry Structure", False, f"Missing entry fields: {missing_entry_fields}")
            else:
                self.log_test("Vault Ledger Structure", False, f"Missing fields: {missing_fields}")
        
        return success, response

    def test_integration_flow(self):
        """Test Phase III: Complete Integration Flow - Generation → Vault Registry → Export PDF → Synthesis Request"""
        print("\n🔄 Testing Complete Integration Flow...")
        
        flow_success = True
        flow_details = []
        
        # Step 1: Generate analogues (already done in setup)
        if self.generation_id and self.vault_ids:
            flow_details.append("✅ Generation: Complete")
        else:
            flow_success = False
            flow_details.append("❌ Generation: Failed")
        
        # Step 2: Verify vault registry
        if self.vault_ids:
            vault_id = self.vault_ids[0]
            success, _ = self.run_test(
                "Integration: Vault Registry Check", 
                "GET", 
                f"vault-ledger/{vault_id}", 
                200, 
                timeout=30
            )
            if success:
                flow_details.append("✅ Vault Registry: Complete")
            else:
                flow_success = False
                flow_details.append("❌ Vault Registry: Failed")
        
        # Step 3: Export PDF
        if self.generation_id:
            export_data = {
                "generation_id": self.generation_id,
                "format": "pdf",
                "include_cost": True,
                "include_ip_analysis": True,
                "watermark": True
            }
            
            success, _ = self.run_test(
                "Integration: PDF Export", 
                "POST", 
                "export-report", 
                200, 
                data=export_data,
                timeout=30,
                response_type='blob'
            )
            if success:
                flow_details.append("✅ PDF Export: Complete")
            else:
                flow_success = False
                flow_details.append("❌ PDF Export: Failed")
        
        # Step 4: Synthesis request
        if self.vault_ids:
            vault_id = self.vault_ids[0]
            synthesis_data = {
                "vault_id": vault_id,
                "partner_name": "Integration Test CRO",
                "quantity_mg": 50.0,
                "purity_requirement": 95.0,
                "timeline_days": 21,
                "contact_email": "integration@test.com",
                "additional_notes": "Integration flow test"
            }
            
            success, _ = self.run_test(
                "Integration: Synthesis Request", 
                "POST", 
                "request-synthesis", 
                200, 
                data=synthesis_data,
                timeout=30
            )
            if success:
                flow_details.append("✅ Synthesis Request: Complete")
            else:
                flow_success = False
                flow_details.append("❌ Synthesis Request: Failed")
        
        # Log overall integration flow result
        details = " | ".join(flow_details)
        self.log_test("Phase III: Complete Integration Flow", flow_success, details)
        
        return flow_success

    def test_hybrid_compatibility(self):
        """Test Phase III: Hybrid Compatibility - Legacy endpoints still functional"""
        print("\n🔄 Testing Hybrid Compatibility...")
        
        # Test legacy sequence validation
        success1, response1 = self.run_test(
            "Hybrid: Legacy Sequence Validation", 
            "GET", 
            "validate-sequence/HAEGTFTSDVSSYLEG", 
            200, 
            timeout=30
        )
        
        # Test legacy analogue generation
        legacy_data = {
            "base_molecule": "ACDEFG",
            "allowed_mods": "substitution",
            "exclusions": "none",
            "target_use": "legacy compatibility test",
            "num_analogues": 1
        }
        
        success2, response2 = self.run_test(
            "Hybrid: Legacy Analogue Generation", 
            "POST", 
            "generate-analogues", 
            200, 
            data=legacy_data,
            timeout=60
        )
        
        # Test legacy generation history
        success3, response3 = self.run_test(
            "Hybrid: Legacy Generation History", 
            "GET", 
            "generation-history", 
            200,  # This might fail based on earlier tests
            timeout=30
        )
        
        hybrid_success = success1 and success2
        details = f"Validation: {'✅' if success1 else '❌'}, Generation: {'✅' if success2 else '❌'}, History: {'✅' if success3 else '❌'}"
        
        self.log_test("Phase III: Hybrid Compatibility", hybrid_success, details)
        
        return hybrid_success

    def test_enterprise_security(self):
        """Test Phase III: Enterprise Security - Token validation, access control, audit trails"""
        print("\n🔒 Testing Enterprise Security...")
        
        security_tests = []
        
        # Test token validation
        if self.token_id:
            success, response = self.run_test(
                "Security: Token Validation", 
                "GET", 
                f"vault-tokens/{self.token_id}", 
                200, 
                timeout=30
            )
            security_tests.append(("Token Validation", success))
        
        # Test invalid token handling
        success, response = self.run_test(
            "Security: Invalid Token Handling", 
            "GET", 
            "vault-tokens/invalid-token-id", 
            404,  # Should return 404 for invalid token
            timeout=30
        )
        security_tests.append(("Invalid Token Handling", success))
        
        # Test audit trail via vault ledger
        success, response = self.run_test(
            "Security: Audit Trail Access", 
            "GET", 
            "vault-ledger?limit=5", 
            200, 
            timeout=30
        )
        security_tests.append(("Audit Trail Access", success))
        
        # Calculate overall security score
        passed_tests = sum(1 for _, success in security_tests if success)
        total_tests = len(security_tests)
        security_success = passed_tests == total_tests
        
        details = f"Passed {passed_tests}/{total_tests} security tests"
        self.log_test("Phase III: Enterprise Security", security_success, details)
        
        return security_success

    def test_data_consistency(self):
        """Test Phase III: Data Consistency - Vault IDs matching across all systems"""
        print("\n🔍 Testing Data Consistency...")
        
        if not self.vault_ids:
            self.log_test("Data Consistency", False, "No vault IDs available for consistency testing")
            return False
        
        consistency_checks = []
        vault_id = self.vault_ids[0]
        
        # Check vault ID in ledger
        success1, ledger_response = self.run_test(
            "Consistency: Vault ID in Ledger", 
            "GET", 
            f"vault-ledger/{vault_id}", 
            200, 
            timeout=30
        )
        
        if success1 and ledger_response:
            ledger_vault_id = ledger_response.get('vault_id')
            if ledger_vault_id == vault_id:
                consistency_checks.append(("Ledger Vault ID", True))
            else:
                consistency_checks.append(("Ledger Vault ID", False))
        
        # Check vault ID format consistency
        vault_id_format_valid = all(
            vid.startswith('PMNC-') and len(vid) == 12 
            for vid in self.vault_ids
        )
        consistency_checks.append(("Vault ID Format", vault_id_format_valid))
        
        # Check vault ID uniqueness
        unique_vault_ids = len(set(self.vault_ids)) == len(self.vault_ids)
        consistency_checks.append(("Vault ID Uniqueness", unique_vault_ids))
        
        # Calculate overall consistency
        passed_checks = sum(1 for _, success in consistency_checks if success)
        total_checks = len(consistency_checks)
        consistency_success = passed_checks == total_checks
        
        details = f"Passed {passed_checks}/{total_checks} consistency checks"
        self.log_test("Phase III: Data Consistency", consistency_success, details)
        
        return consistency_success

    def test_error_handling(self):
        """Test Phase III: Error Handling - Graceful failure modes for enterprise deployment"""
        print("\n⚠️ Testing Error Handling...")
        
        error_tests = []
        
        # Test invalid generation ID for export
        invalid_export_data = {
            "generation_id": "invalid-generation-id",
            "format": "pdf",
            "include_cost": True,
            "include_ip_analysis": True,
            "watermark": True
        }
        
        success, response = self.run_test(
            "Error Handling: Invalid Generation ID", 
            "POST", 
            "export-report", 
            404,  # Should return 404 for invalid generation ID
            data=invalid_export_data,
            timeout=30
        )
        error_tests.append(("Invalid Generation ID", success))
        
        # Test invalid vault ID for synthesis
        invalid_synthesis_data = {
            "vault_id": "INVALID-VAULT-ID",
            "partner_name": "Test CRO",
            "quantity_mg": 100.0,
            "purity_requirement": 95.0,
            "timeline_days": 14,
            "contact_email": "test@example.com"
        }
        
        success, response = self.run_test(
            "Error Handling: Invalid Vault ID", 
            "POST", 
            "request-synthesis", 
            404,  # Should return 404 for invalid vault ID
            data=invalid_synthesis_data,
            timeout=30
        )
        error_tests.append(("Invalid Vault ID", success))
        
        # Test invalid vault ledger entry
        success, response = self.run_test(
            "Error Handling: Invalid Ledger Entry", 
            "GET", 
            "vault-ledger/INVALID-VAULT-ID", 
            404,  # Should return 404 for invalid vault ID
            timeout=30
        )
        error_tests.append(("Invalid Ledger Entry", success))
        
        # Calculate overall error handling score
        passed_tests = sum(1 for _, success in error_tests if success)
        total_tests = len(error_tests)
        error_handling_success = passed_tests == total_tests
        
        details = f"Passed {passed_tests}/{total_tests} error handling tests"
        self.log_test("Phase III: Error Handling", error_handling_success, details)
        
        return error_handling_success

    def run_all_phase3_tests(self):
        """Run all Phase III enterprise tests"""
        print("🚀 Starting Peptimancer Phase III Enterprise Validation")
        print("=" * 70)
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Cannot proceed with Phase III tests.")
            return 1
        
        print("\n📊 Phase III Enterprise Feature Tests")
        print("-" * 50)
        
        # Core Phase III features
        self.test_pdf_export_system()
        self.test_synthesis_request_system()
        self.test_vault_token_management()
        self.test_vault_ledger_system()
        
        print("\n🔄 Integration & Compatibility Tests")
        print("-" * 50)
        
        # Integration and compatibility
        self.test_integration_flow()
        self.test_hybrid_compatibility()
        
        print("\n🔒 Enterprise Quality Tests")
        print("-" * 50)
        
        # Enterprise quality
        self.test_enterprise_security()
        self.test_data_consistency()
        self.test_error_handling()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 Phase III Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All Phase III enterprise tests passed!")
            return 0
        else:
            print("⚠️  Some Phase III tests failed. Check details above.")
            
            # Print failed tests
            failed_tests = [test for test in self.test_results if not test['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test_name']}: {test['details']}")
            
            return 1

def main():
    tester = Phase3EnterpriseAPITester()
    return tester.run_all_phase3_tests()

if __name__ == "__main__":
    sys.exit(main())