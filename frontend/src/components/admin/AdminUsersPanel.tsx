// User & Tier Management Panel Component
import React, { useEffect, useState } from 'react';
import { listUsers, adjustCredits, setTier } from '../../lib/admin.ts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Users, RefreshCw, Plus, Minus, AlertCircle } from 'lucide-react';

interface User {
  id: string;
  email: string;
  role: string;
  tier: string;
  credits: number;
  lastLogin: string | null;
}

export default function AdminUsersPanel() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await listUsers();
      setUsers(data.items || []);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleAdjustCredits = async (userId: string, delta: number, reason: string) => {
    try {
      setActionLoading(`${userId}-credits`);
      await adjustCredits({ userId, delta, reason });
      await loadUsers(); // Reload to show updated credits
    } catch (err: any) {
      alert(`Failed to adjust credits: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleSetTier = async (userId: string, newTier: string) => {
    try {
      setActionLoading(`${userId}-tier`);
      await setTier({ userId, tier: newTier });
      await loadUsers(); // Reload to show updated tier
    } catch (err: any) {
      alert(`Failed to set tier: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'basic': return 'bg-gray-100 text-gray-700';
      case 'pro': return 'bg-blue-100 text-blue-700';
      case 'enterprise': return 'bg-purple-100 text-purple-700';
      case 'admin': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin': return 'bg-red-100 text-red-700';
      case 'researcher': return 'bg-green-100 text-green-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
            <span className="ml-2">Loading users...</span>
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
            <Button onClick={loadUsers} className="mt-4" variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-blue-600" />
              Users & Tiers
            </CardTitle>
            <CardDescription>
              Manage user tiers and credits allocation
            </CardDescription>
          </div>
          <Button onClick={loadUsers} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </CardHeader>
      
      <CardContent>
        {users.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No users found
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="py-3 px-2">Email</th>
                  <th className="py-3 px-2">Role</th>
                  <th className="py-3 px-2">Tier</th>
                  <th className="py-3 px-2 text-right">Credits</th>
                  <th className="py-3 px-2">Last Login</th>
                  <th className="py-3 px-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-2 font-medium">{user.email}</td>
                    
                    <td className="py-3 px-2">
                      <Badge className={`${getRoleColor(user.role)} text-xs`}>
                        {user.role}
                      </Badge>
                    </td>
                    
                    <td className="py-3 px-2">
                      <Select
                        defaultValue={user.tier}
                        onValueChange={(value) => handleSetTier(user.id, value)}
                        disabled={actionLoading === `${user.id}-tier`}
                      >
                        <SelectTrigger className="w-32 h-8">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="basic">
                            <Badge className="bg-gray-100 text-gray-700 text-xs">Basic</Badge>
                          </SelectItem>
                          <SelectItem value="pro">
                            <Badge className="bg-blue-100 text-blue-700 text-xs">Pro</Badge>
                          </SelectItem>
                          <SelectItem value="enterprise">
                            <Badge className="bg-purple-100 text-purple-700 text-xs">Enterprise</Badge>
                          </SelectItem>
                          <SelectItem value="admin">
                            <Badge className="bg-red-100 text-red-700 text-xs">Admin</Badge>
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </td>
                    
                    <td className="py-3 px-2 text-right font-mono font-semibold">
                      {user.credits}
                    </td>
                    
                    <td className="py-3 px-2 text-xs text-gray-500">
                      {user.lastLogin 
                        ? new Date(user.lastLogin).toLocaleString()
                        : '—'
                      }
                    </td>
                    
                    <td className="py-3 px-2">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleAdjustCredits(user.id, 50, 'admin grant')}
                          disabled={actionLoading === `${user.id}-credits`}
                          className="h-7 px-2"
                        >
                          <Plus className="h-3 w-3 mr-1" />
                          50
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleAdjustCredits(user.id, -50, 'admin revoke')}
                          disabled={actionLoading === `${user.id}-credits`}
                          className="h-7 px-2"
                        >
                          <Minus className="h-3 w-3 mr-1" />
                          50
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        <div className="mt-4 text-xs text-gray-500 text-center">
          Showing {users.length} user{users.length !== 1 ? 's' : ''} • Limited to 200 most recent
        </div>
      </CardContent>
    </Card>
  );
}
