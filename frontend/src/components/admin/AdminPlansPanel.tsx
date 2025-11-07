// Admin Plans Management Panel
import React, { useEffect, useState } from 'react';
import { getPlans, upsertPlan } from '../../lib/billing.ts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DollarSign, Coins, RefreshCw, AlertCircle, Save } from 'lucide-react';

export default function AdminPlansPanel() {
  const [plans, setPlans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    reload();
  }, []);

  const reload = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getPlans();
      setPlans(data.items || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load plans');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (code: string) => {
    try {
      setSaving(code);
      
      const priceInput = document.getElementById(`price-${code}`) as HTMLInputElement;
      const creditsInput = document.getElementById(`credits-${code}`) as HTMLInputElement;
      
      await upsertPlan({
        code,
        price: Number(priceInput.value),
        credits: Number(creditsInput.value)
      });
      
      await reload();
      alert(`Plan "${code}" updated successfully`);
    } catch (err: any) {
      alert(`Failed to update plan: ${err.message}`);
    } finally {
      setSaving(null);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
            <span className="ml-2">Loading plans...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-red-600">
            <AlertCircle className="h-8 w-8 mx-auto mb-2" />
            <p>{error}</p>
            <Button onClick={reload} className="mt-4" variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const getPlanColor = (code: string) => {
    switch (code) {
      case 'basic': return 'bg-gray-100 text-gray-700';
      case 'pro': return 'bg-blue-100 text-blue-700';
      case 'enterprise': return 'bg-purple-100 text-purple-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-green-600" />
              Billing Plans
            </CardTitle>
            <CardDescription>
              Manage subscription plans, pricing, and credit allocations
            </CardDescription>
          </div>
          <Button onClick={reload} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </CardHeader>
      
      <CardContent>
        {plans.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No plans configured
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="py-3 px-2">Plan</th>
                  <th className="py-3 px-2 text-right">Price (USD/month)</th>
                  <th className="py-3 px-2 text-right">Monthly Credits</th>
                  <th className="py-3 px-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {plans.map((plan) => (
                  <tr key={plan.code} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-2">
                      <Badge className={`${getPlanColor(plan.code)} text-sm font-semibold`}>
                        {plan.code.charAt(0).toUpperCase() + plan.code.slice(1)}
                      </Badge>
                    </td>
                    
                    <td className="py-3 px-2 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <DollarSign className="h-4 w-4 text-gray-400" />
                        <input
                          id={`price-${plan.code}`}
                          type="number"
                          defaultValue={plan.price}
                          min="0"
                          className="w-24 px-2 py-1 border rounded text-right"
                        />
                      </div>
                    </td>
                    
                    <td className="py-3 px-2 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Coins className="h-4 w-4 text-gray-400" />
                        <input
                          id={`credits-${plan.code}`}
                          type="number"
                          defaultValue={plan.credits}
                          min="0"
                          className="w-24 px-2 py-1 border rounded text-right"
                        />
                      </div>
                    </td>
                    
                    <td className="py-3 px-2 text-right">
                      <Button
                        size="sm"
                        onClick={() => handleSave(plan.code)}
                        disabled={saving === plan.code}
                        className="bg-green-600 hover:bg-green-700"
                      >
                        <Save className="h-3 w-3 mr-1" />
                        {saving === plan.code ? 'Saving...' : 'Save'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        <div className="mt-4 text-xs text-gray-500 space-y-1">
          <p>• Price changes apply to new subscriptions immediately</p>
          <p>• Credit allocations are granted on monthly renewal or upgrade</p>
          <p>• Basic plan is typically free ($0) for new users</p>
        </div>
      </CardContent>
    </Card>
  );
}
