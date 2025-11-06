import requests
import sys
import json
from datetime import datetime
import time

class PeptimancerAPITester:
    def __init__(self, base_url="https://peptide-architect-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

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

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
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
        print("🧪 Starting Peptimancer Backend API Tests - Iteration 2 (Edge Cases)")
        print("=" * 70)
        
        # Basic connectivity tests
        self.test_root_endpoint()
        
        # Sequence validation tests
        self.test_sequence_validation_valid()
        self.test_sequence_validation_invalid()
        
        # Core functionality tests
        self.test_generate_analogues_basic()
        self.test_generate_analogues_minimal()
        
        # Error handling tests
        self.test_generate_analogues_invalid_sequence()
        
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