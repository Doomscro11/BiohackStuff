// User Billing Widget Component - Auth-aware with credit refresh
import React, { useEffect, useState, useRef } from 'react';
import { fetchBillingState, startCheckout } from '../../lib/billing.ts';
import { redirectToLogin } from '../../lib/http.ts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CreditCard, Coins, TrendingUp, Clock, AlertCircle, CheckCircle } from 'lucide-react';

export default function BillingWidget() {
  const [state, setState] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const prevCredits = useRef<number | null>(null);

  const reload = async () => {
    setLoading(true);
    const result = await fetchBillingState();
    
    if (!result.ok) {
      if (result.status === 401) {
        setAuthError(true);
      }
      setLoading(false);
      return;
    }
    
    setAuthError(false);
    setState(result.data);
    setLoading(false);
  };

  // Initial load + post-checkout polling for credit refresh
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const cameFromCheckout = params.get('success') === '1';
    
    let timer: any = null;
    let tries = 0;
    
    const poll = async () => {
      await reload();
      tries++;
      
      const currentCredits = state?.credits;
      if (prevCredits.current == null) {
        prevCredits.current = currentCredits ?? null;
      }
      
      const creditsChanged = 
        prevCredits.current != null && 
        currentCredits != null && 
        currentCredits !== prevCredits.current;
      
      // Stop polling if credits changed, not from checkout, or max tries
      if (creditsChanged || !cameFromCheckout || tries > 6) {
        if (creditsChanged) {
          // Dispatch credit update event for header badge
          window.dispatchEvent(
            new CustomEvent('credits:update', { 
              detail: { credits: currentCredits } 
            })
          );
          prevCredits.current = currentCredits;
        }
        return;
      }
      
      // Continue polling (5 second intervals, max 30 seconds)
      timer = setTimeout(poll, 5000);
    };
    
    poll();
    
    return () => {
      if (timer) clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const upgrade = async (plan: 'pro' | 'enterprise') => {
    setActionLoading(true);
    const result = await startCheckout({ plan });
    
    if (!result.ok) {
      alert(`Failed to start checkout: ${result.text || 'Unknown error'}`);
      setActionLoading(false);
      return;
    }
    
    window.location.href = (result as any).data.url;
  };

  const buyCredits = async (credits: number) => {
    setActionLoading(true);
    const result = await startCheckout({ purchase_credits: credits });
    
    if (!result.ok) {
      alert(`Failed to start checkout: ${result.text || 'Unknown error'}`);
      setActionLoading(false);
      return;
    }
    
    window.location.href = (result as any).data.url;
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
            <span className="ml-2">Loading billing information...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Show sign-in prompt for unauthenticated users
  if (authError) {
    return (
      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="pt-6">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 mx-auto mb-3 text-amber-600" />
            <h3 className="font-semibold text-lg text-amber-900 mb-2">
              Sign in required
            </h3>
            <p className="text-sm text-amber-800 mb-4">
              Please sign in to view your plan, credits, and purchase options.
            </p>
            <Button
              onClick={() => redirectToLogin('/billing')}
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              Sign in to continue
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'basic': return 'bg-gray-100 text-gray-700';
      case 'pro': return 'bg-blue-100 text-blue-700';
      case 'enterprise': return 'bg-purple-100 text-purple-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="space-y-6">
      {/* Current Plan & Credits */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-blue-600" />
            Your Plan & Credits
          </CardTitle>
          <CardDescription>Manage your subscription and credit balance</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 border rounded-lg">
              <div className="text-sm text-gray-500 mb-1">Current Tier</div>
              <Badge className={`${getTierColor(state.tier)} text-lg font-semibold`}>
                {state.tier.charAt(0).toUpperCase() + state.tier.slice(1)}
              </Badge>
            </div>
            
            <div className="text-center p-4 border rounded-lg">
              <div className="text-sm text-gray-500 mb-1">Credits Balance</div>
              <div className="text-2xl font-bold text-blue-600 flex items-center justify-center gap-1">
                <Coins className="h-5 w-5" />
                {state.credits}
              </div>
            </div>
            
            <div className="text-center p-4 border rounded-lg">
              <div className="text-sm text-gray-500 mb-1">Renews</div>
              <div className="text-sm font-medium">
                {state.renewsAt ? (
                  <div className="flex items-center justify-center gap-1">
                    <Clock className="h-4 w-4" />
                    {new Date(state.renewsAt).toLocaleDateString()}
                  </div>
                ) : '—'}
              </div>
            </div>
            
            <div className="text-center p-4 border rounded-lg">
              <div className="text-sm text-gray-500 mb-1">Provider</div>
              <div className="text-sm font-medium capitalize">
                {state.provider || 'None'}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Upgrade Options */}
      {state.tier === 'basic' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-purple-600" />
              Upgrade Your Plan
            </CardTitle>
            <CardDescription>Get more credits and unlock advanced features</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="border rounded-lg p-4 hover:border-blue-500 transition">
                <h4 className="font-semibold text-lg mb-2">Pro Plan</h4>
                <p className="text-3xl font-bold text-blue-600 mb-2">$49<span className="text-sm text-gray-500">/month</span></p>
                <ul className="text-sm space-y-2 mb-4">
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    200 credits per month
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    Priority support
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    Advanced analytics
                  </li>
                </ul>
                <Button 
                  onClick={() => upgrade('pro')} 
                  disabled={actionLoading}
                  className="w-full bg-blue-600 hover:bg-blue-700"
                >
                  Upgrade to Pro
                </Button>
              </div>

              <div className="border-2 border-purple-500 rounded-lg p-4 relative">
                <div className="absolute -top-3 right-4 bg-purple-500 text-white px-3 py-1 rounded text-xs font-semibold">
                  BEST VALUE
                </div>
                <h4 className="font-semibold text-lg mb-2">Enterprise Plan</h4>
                <p className="text-3xl font-bold text-purple-600 mb-2">$499<span className="text-sm text-gray-500">/month</span></p>
                <ul className="text-sm space-y-2 mb-4">
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    5,000 credits per month
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    Dedicated support
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    Custom integrations
                  </li>
                </ul>
                <Button 
                  onClick={() => upgrade('enterprise')} 
                  disabled={actionLoading}
                  className="w-full bg-purple-600 hover:bg-purple-700"
                >
                  Upgrade to Enterprise
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Buy Credits */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Coins className="h-5 w-5 text-amber-600" />
            Buy Additional Credits
          </CardTitle>
          <CardDescription>One-time credit purchases</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            {[
              { amount: 100, price: 5 },
              { amount: 250, price: 12 },
              { amount: 500, price: 20 },
              { amount: 1000, price: 35 }
            ].map(({ amount, price }) => (
              <Button
                key={amount}
                onClick={() => buyCredits(amount)}
                disabled={actionLoading}
                variant="outline"
                className="flex-1 min-w-[150px] h-auto py-4 flex-col hover:border-amber-500"
              >
                <div className="text-2xl font-bold text-amber-600">{amount}</div>
                <div className="text-xs text-gray-500">credits</div>
                <div className="text-sm font-semibold mt-1">${price}</div>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Transaction History */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Your credit transaction history</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="max-h-64 overflow-auto">
            {state.history && state.history.length > 0 ? (
              <div className="space-y-2">
                {state.history.map((h: any) => (
                  <div key={h._id} className="flex items-center justify-between py-2 border-b text-sm">
                    <div className="flex items-center gap-2">
                      <span className={`font-semibold ${h.delta > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {h.delta > 0 ? '+' : ''}{h.delta}
                      </span>
                      <span className="text-gray-700">{h.reason}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-gray-500">
                        Balance: {h.balanceAfter}
                      </div>
                      <div className="text-xs text-gray-400">
                        {new Date(h.timestamp || h.ts).toLocaleString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                No transaction history yet
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
