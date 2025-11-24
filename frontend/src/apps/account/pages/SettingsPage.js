/**
 * Unified Settings Page
 * 
 * All authenticated users can see:
 * - Account Overview (email, role, user ID)
 * - Billing & Credits
 * 
 * Admins additionally see:
 * - Admin Tools (Analytics, Feature Flags, etc.)
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  User, 
  Copy, 
  Check, 
  CreditCard, 
  BarChart3, 
  Shield,
  Settings as SettingsIcon,
  Sliders,
  FileText,
  Info
} from 'lucide-react';
import { fetchSession } from '@/lib/session';
import { canAccessAdmin } from '@/lib/roles';
import { getRoleLabel, getRoleColor } from '@/lib/roles';
import BillingWidget from '@/components/billing/BillingWidget';

function SettingsPage() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copiedUserId, setCopiedUserId] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const session = await fetchSession();
      if (session) {
        setUser(session);
      }
    } catch (error) {
      console.error('Failed to load user data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyUserId = async () => {
    if (user?.id || user?._id || user?.user_id) {
      const userId = user.id || user._id || user.user_id;
      try {
        await navigator.clipboard.writeText(userId);
        setCopiedUserId(true);
        setTimeout(() => setCopiedUserId(false), 2000);
      } catch (error) {
        console.error('Failed to copy user ID:', error);
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <p className="text-center text-gray-600 dark:text-gray-400">
              Unable to load user data. Please try logging in again.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const isAdmin = canAccessAdmin(user);
  const userId = user.id || user._id || user.user_id || 'N/A';

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-5xl mx-auto">
        {/* Page Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
            <SettingsIcon className="h-8 w-8 text-blue-600" />
            Settings
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your account, billing, and preferences
          </p>
        </div>

        <div className="space-y-6">
          {/* Section A: Account Overview - All Users */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5 text-blue-600" />
                Account Overview
              </CardTitle>
              <CardDescription>
                Your account information and role
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Email */}
              <div className="flex items-center justify-between py-2">
                <div className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Email
                </div>
                <div className="text-sm text-gray-900 dark:text-white font-mono">
                  {user.email}
                </div>
              </div>

              <Separator />

              {/* Role */}
              <div className="flex items-center justify-between py-2">
                <div className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Role
                </div>
                <Badge className={getRoleColor(user)}>
                  {getRoleLabel(user)}
                </Badge>
              </div>

              <Separator />

              {/* User ID */}
              <div className="flex items-center justify-between py-2">
                <div className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  User ID
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-xs text-gray-900 dark:text-white font-mono bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                    {userId.length > 20 ? `${userId.substring(0, 20)}...` : userId}
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleCopyUserId}
                    className="h-8"
                  >
                    {copiedUserId ? (
                      <>
                        <Check className="h-3 w-3 mr-1" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-3 w-3 mr-1" />
                        Copy
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {/* Tier Info */}
              {user.tier && (
                <>
                  <Separator />
                  <div className="flex items-center justify-between py-2">
                    <div className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Subscription Tier
                    </div>
                    <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-300">
                      {user.tier.charAt(0).toUpperCase() + user.tier.slice(1)}
                    </Badge>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Section B: Billing & Credits - All Users */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-green-600" />
                Billing & Credits
              </CardTitle>
              <CardDescription>
                Manage your subscription and view credit balance
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Embed BillingWidget component */}
              <BillingWidget />
              
              <Separator className="my-4" />
              
              {/* Link to full billing page */}
              <div className="flex items-center justify-between bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                <div>
                  <div className="text-sm font-medium">Need more options?</div>
                  <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    Visit the full billing page for detailed history and invoices
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate('/billing')}
                >
                  Full Billing Page →
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Section C: Admin Tools - Admins Only */}
          {isAdmin && (
            <Card className="border-2 border-purple-200 dark:border-purple-800">
              <CardHeader className="bg-purple-50 dark:bg-purple-900/20">
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-purple-600" />
                  Admin Tools
                  <Badge variant="outline" className="ml-2 bg-purple-100 text-purple-700 border-purple-300">
                    Admin Only
                  </Badge>
                </CardTitle>
                <CardDescription>
                  Advanced tools and analytics for administrators
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                {/* Info Alert */}
                <Alert className="mb-4 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-700">
                  <Info className="h-4 w-4 text-blue-600" />
                  <AlertDescription className="text-xs text-blue-800 dark:text-blue-200">
                    These admin tools are visible because you are logged in as an administrator. 
                    Regular users will only see account and billing information.
                  </AlertDescription>
                </Alert>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Analytics - Removed as standalone page, may be reintroduced as embedded panel */}
                  
                  {/* Feature Flags */}
                  <Card className="bg-white dark:bg-gray-800 hover:shadow-md transition-shadow">
                    <CardContent className="pt-6">
                      <div className="flex items-start gap-3 mb-3">
                        <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded">
                          <Sliders className="h-5 w-5 text-purple-600" />
                        </div>
                        <div>
                          <div className="font-semibold text-sm">Feature Flags</div>
                          <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                            Manage feature toggles and DAC controls
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        onClick={() => navigate('/admin')}
                      >
                        Open Admin Panel →
                      </Button>
                    </CardContent>
                  </Card>

                  {/* Guardrail Editor */}
                  <Card className="bg-white dark:bg-gray-800 hover:shadow-md transition-shadow">
                    <CardContent className="pt-6">
                      <div className="flex items-start gap-3 mb-3">
                        <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded">
                          <Shield className="h-5 w-5 text-orange-600" />
                        </div>
                        <div>
                          <div className="font-semibold text-sm">Guardrail Rules</div>
                          <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                            Edit modification compatibility rules
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        onClick={() => navigate('/admin/guardrails')}
                      >
                        Open Editor →
                      </Button>
                    </CardContent>
                  </Card>

                  {/* PatentPulse Manual Review - No longer includes Partner Shares */}
                  <Card className="bg-white dark:bg-gray-800 hover:shadow-md transition-shadow">
                    <CardContent className="pt-6">
                      <div className="flex items-start gap-3 mb-3">
                        <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded">
                          <FileText className="h-5 w-5 text-green-600" />
                        </div>
                        <div>
                          <div className="font-semibold text-sm">PatentPulse Admin</div>
                          <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                            Manual IP candidate review (beta)
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        onClick={() => navigate('/admin/patentpulse')}
                      >
                        Open PatentPulse →
                      </Button>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;
