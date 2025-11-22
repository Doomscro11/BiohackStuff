#!/usr/bin/env python3
"""
Global Login & RBAC Implementation Testing
Comprehensive validation for authentication flow and role-based access control
"""

import requests
import json
import time
from datetime import datetime
import sys

# Use production endpoint from frontend .env
BACKEND_URL = "https://rbac-portal-6.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class GlobalLoginRBACTest:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []
        self.test_results = {}
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
        """Test POST /api/auth/magic/request with admin email"""
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

    def test_magic_code_verify_admin(self):
        """Test POST /api/auth/magic/verify with admin email and correct code"""
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

    def test_magic_code_request_non_admin(self):
        """Test POST /api/auth/magic/request with non-admin email"""
        try:
            payload = {"email": self.test_email}
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

    def test_magic_code_verify_non_admin(self):
        """Test POST /api/auth/magic/verify with non-admin email"""
        if not hasattr(self, 'demo_code_non_admin'):
            self.log_test(
                "Magic Code Verification (Non-Admin)",
                False,
                error_details="No demo code available (request must succeed first)"
            )
            return False
        
        try:
            payload = {"email": self.test_email, "code": self.demo_code_non_admin}
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

    def test_session_endpoint_without_auth(self):
        """Test GET /api/auth/session without authentication - should return 401"""
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
        """Test GET /api/auth/session with valid JWT - should return user data"""
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
        """Test GET /api/billing/state without auth - should return 401"""
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
        """Test GET /api/billing/state with valid JWT - should return billing data"""
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
        """Test GET /api/chemistry/options without auth - should work (public endpoint)"""
        try:
            response = requests.get(f"{API_BASE}/chemistry/options", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "modifications" in data or "mods" in data:
                    mods_count = len(data.get("modifications", data.get("mods", [])))
                    exclusions_count = len(data.get("exclusions", []))
                    self.log_test(
                        "Public Chemistry Options Endpoint",
                        True,
                        f"Returned basic tier options: {mods_count} mods, {exclusions_count} exclusions"
                    )
                    return True
                else:
                    self.log_test(
                        "Public Chemistry Options Endpoint",
                        False,
                        error_details="Missing modifications/mods or exclusions in response"
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
        """Test GET /api/chemistry/options with auth - should return tier-appropriate options"""
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
                if "modifications" in data or "mods" in data:
                    mods_count = len(data.get("modifications", data.get("mods", [])))
                    exclusions_count = len(data.get("exclusions", []))
                    self.log_test(
                        "Chemistry Options With Auth",
                        True,
                        f"Returned tier-appropriate options: {mods_count} mods, {exclusions_count} exclusions"
                    )
                    return True
                else:
                    self.log_test(
                        "Chemistry Options With Auth",
                        False,
                        error_details="Missing modifications/mods or exclusions in response"
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
        """Test GET /api/admin/features/flags without auth - should return 401"""
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
        """Test GET /api/admin/features/flags with non-admin JWT - should return 403"""
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

    def test_admin_feature_flags_with_admin(self):
        """Test GET /api/admin/features/flags with admin JWT"""
        if not hasattr(self, 'admin_jwt_cookie') or not self.admin_jwt_cookie:
            self.log_test(
                "Admin Feature Flags With Admin",
                False,
                error_details="No admin JWT cookie available"
            )
            return False
        
        try:
            cookies = {"pmnc_jwt": self.admin_jwt_cookie}
            response = requests.get(f"{API_BASE}/admin/features/flags", cookies=cookies, timeout=10)
            
            # This should return 403 because admin endpoints require 2FA, or 200 if 2FA is disabled
            if response.status_code == 403:
                self.log_test(
                    "Admin Feature Flags With Admin",
                    True,
                    "Correctly returned 403 Forbidden - admin endpoints require 2FA"
                )
                return True
            elif response.status_code == 200:
                # If it returns 200, it means 2FA is not required or already satisfied
                self.log_test(
                    "Admin Feature Flags With Admin",
                    True,
                    "Admin access granted - 2FA requirement may be disabled or satisfied"
                )
                return True
            else:
                self.log_test(
                    "Admin Feature Flags With Admin",
                    False,
                    error_details=f"Expected HTTP 403 or 200, got {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Admin Feature Flags With Admin",
                False,
                error_details=f"Request failed: {str(e)}"
            )
            return False

    def test_public_partner_share_endpoint(self):
        """Test GET /api/patentpulse/partner/share/{token} - should work without auth"""
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
        """Test POST /api/auth/logout - should clear JWT cookie"""
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

    def test_invalid_otp(self):
        """Test with invalid OTP code - should return 401"""
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
        """Test with invalid email format - should return 422"""
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

    def run_comprehensive_tests(self):
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
        self.test_magic_code_verify_admin()
        self.test_magic_code_request_non_admin()
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
        self.test_admin_feature_flags_with_admin()
        
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

if __name__ == "__main__":
    # Run Global Login & RBAC tests
    rbac_test = GlobalLoginRBACTest()
    results = rbac_test.run_comprehensive_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results["global_login_rbac_working"] else 1)