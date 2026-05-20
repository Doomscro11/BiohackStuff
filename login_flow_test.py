#!/usr/bin/env python3
"""
Login and Admin Navigation Flow Test
Test the complete login and admin navigation flow as requested in the review
"""

import requests
import json
import time
from datetime import datetime
import sys

# Use production endpoint from frontend .env
BACKEND_URL = "https://partner-purge.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class LoginAdminNavigationTest:
    """Test the complete login and admin navigation flow as requested"""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []
        self.test_results = {}
        self.admin_email = "founder@peptologic.ai"
        self.demo_code = None
        self.jwt_cookie = None
        
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

    def test_1_magic_code_request(self):
        """Test 1: POST /api/auth/magic/request with email=founder@peptologic.ai"""
        try:
            payload = {"email": self.admin_email}
            response = requests.post(f"{API_BASE}/auth/magic/request", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "demo_code" in data:
                    self.demo_code = data["demo_code"]
                    self.log_test(
                        "Step 1: Magic Code Request",
                        True,
                        f"Demo code received: {self.demo_code}, expires in {data.get('expires_in_minutes')} minutes"
                    )
                    return True
                else:
                    self.log_test(
                        "Step 1: Magic Code Request",
                        False,
                        error_details="Response missing demo_code or success flag"
                    )
                    return False
            else:
                self.log_test(
                    "Step 1: Magic Code Request",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Step 1: Magic Code Request",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_2_extract_demo_code(self):
        """Test 2: Extract the demo_code from response"""
        if self.demo_code:
            self.log_test(
                "Step 2: Extract Demo Code",
                True,
                f"Demo code extracted successfully: {self.demo_code}"
            )
            return True
        else:
            self.log_test(
                "Step 2: Extract Demo Code",
                False,
                error_details="No demo code available from previous step"
            )
            return False

    def test_3_magic_code_verify(self):
        """Test 3: POST /api/auth/magic/verify with the demo_code - verify JWT cookie is set"""
        if not self.demo_code:
            self.log_test(
                "Step 3: Magic Code Verification",
                False,
                error_details="No demo code available"
            )
            return False
        
        try:
            payload = {"email": self.admin_email, "code": self.demo_code}
            response = requests.post(f"{API_BASE}/auth/magic/verify", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Check for JWT cookie
                cookies = response.cookies
                if "pmnc_jwt" in cookies:
                    self.jwt_cookie = cookies["pmnc_jwt"]
                    if data.get("role") == "admin" and data.get("success"):
                        self.log_test(
                            "Step 3: Magic Code Verification",
                            True,
                            f"JWT cookie set successfully, role: {data.get('role')}, email: {data.get('email')}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Step 3: Magic Code Verification",
                            False,
                            error_details=f"Expected admin role and success=true, got role='{data.get('role')}', success={data.get('success')}"
                        )
                        return False
                else:
                    self.log_test(
                        "Step 3: Magic Code Verification",
                        False,
                        error_details="JWT cookie (pmnc_jwt) not set in response"
                    )
                    return False
            else:
                self.log_test(
                    "Step 3: Magic Code Verification",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Step 3: Magic Code Verification",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_4_session_endpoint(self):
        """Test 4: GET /api/auth/session with the JWT cookie - should return admin user data"""
        if not self.jwt_cookie:
            self.log_test(
                "Step 4: Session Endpoint Test",
                False,
                error_details="No JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.jwt_cookie}
            response = requests.get(f"{API_BASE}/auth/session", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["email", "role", "tier", "credits", "feature_level"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(
                        "Step 4: Session Endpoint Test",
                        False,
                        error_details=f"Missing required fields: {missing_fields}"
                    )
                    return False
                
                if data.get("email") == self.admin_email and data.get("role") == "admin":
                    self.log_test(
                        "Step 4: Session Endpoint Test",
                        True,
                        f"Admin user data returned correctly - Email: {data.get('email')}, Role: {data.get('role')}, Tier: {data.get('tier')}, Credits: {data.get('credits')}, Feature Level: {data.get('feature_level')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Step 4: Session Endpoint Test",
                        False,
                        error_details=f"Expected admin user data, got email='{data.get('email')}', role='{data.get('role')}'"
                    )
                    return False
            else:
                self.log_test(
                    "Step 4: Session Endpoint Test",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Step 4: Session Endpoint Test",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_5_admin_feature_flags(self):
        """Test 5: GET /api/admin/features/flags with the JWT cookie - should work (or 403 if 2FA required)"""
        if not self.jwt_cookie:
            self.log_test(
                "Step 5: Admin Feature Flags Test",
                False,
                error_details="No JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.jwt_cookie}
            response = requests.get(f"{API_BASE}/admin/features/flags", cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "flags" in data:
                    self.log_test(
                        "Step 5: Admin Feature Flags Test",
                        True,
                        f"Feature flags retrieved successfully - {len(data.get('flags', []))} flags returned"
                    )
                    return True
                else:
                    self.log_test(
                        "Step 5: Admin Feature Flags Test",
                        False,
                        error_details="Response missing 'flags' field"
                    )
                    return False
            elif response.status_code == 403:
                # This is expected if 2FA is required
                self.log_test(
                    "Step 5: Admin Feature Flags Test",
                    True,
                    "Correctly returned 403 Forbidden - 2FA required for admin endpoints (expected behavior)"
                )
                return True
            else:
                self.log_test(
                    "Step 5: Admin Feature Flags Test",
                    False,
                    error_details=f"Unexpected HTTP status {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Step 5: Admin Feature Flags Test",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def run_login_admin_navigation_test(self):
        """Run the complete login and admin navigation flow test"""
        print("=" * 80)
        print("🔐 LOGIN AND ADMIN NAVIGATION FLOW TEST")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Email: {self.admin_email}")
        print(f"Test Started: {datetime.now().isoformat()}")
        print("=" * 80)
        print()
        
        print("🔑 TESTING COMPLETE LOGIN AND ADMIN NAVIGATION FLOW")
        print("-" * 60)
        
        # Run all tests in sequence
        self.test_1_magic_code_request()
        self.test_2_extract_demo_code()
        self.test_3_magic_code_verify()
        self.test_4_session_endpoint()
        self.test_5_admin_feature_flags()
        
        # Final summary
        print("\n" + "=" * 80)
        print("📈 LOGIN AND ADMIN NAVIGATION TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.critical_failures:
            print(f"\n❌ CRITICAL FAILURES ({len(self.critical_failures)}):")
            for failure in self.critical_failures:
                print(f"  • {failure['test']}: {failure['error']}")
        
        print(f"\nLogin & Admin Navigation Status: {'✅ WORKING' if self.tests_passed >= self.tests_run * 0.8 else '❌ ISSUES DETECTED'}")
        print("=" * 80)
        
        return {
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "success_rate": self.tests_passed/self.tests_run*100,
            "critical_failures": self.critical_failures,
            "test_results": self.test_results,
            "flow_working": self.tests_passed >= self.tests_run * 0.8
        }


if __name__ == "__main__":
    # Run the specific login and admin navigation flow test as requested
    login_test = LoginAdminNavigationTest()
    results = login_test.run_login_admin_navigation_test()
    
    # Exit with appropriate code
    sys.exit(0 if results["flow_working"] else 1)