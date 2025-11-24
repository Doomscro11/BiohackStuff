// PatentPulse Dashboard - Patent Mining & Commercialization
import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  FileText, TrendingUp, DollarSign, AlertCircle, 
  Award, Building2, Globe, Calendar, Dna, Share2 
} from 'lucide-react';
import { 
  getPatentItems, 
  getPatentStats, 
  getTopOpportunities
} from '@/lib/patentpulse';
// PartnerSharesAdmin removed - feature deprecated

export default function PatentPulsePage() {
  const [stats, setStats] = useState(null);
  const [opportunities, setOpportunities] = useState([]);
  const [patents, setPatents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    loadPatentPulseData();
  }, [statusFilter]);

  const loadPatentPulseData = async () => {
    setLoading(true);
    setError(null);

    try {
      const filters = statusFilter !== 'all' ? { status: statusFilter, limit: 20 } : { limit: 20 };
      
      const [statsResult, oppsResult, patentsResult] = await Promise.all([
        getPatentStats(),
        getTopOpportunities(5),
        getPatentItems(filters)
      ]);

      if (!statsResult.ok) {
        throw new Error(`Failed to load stats: ${statsResult.text || statsResult.status}`);
      }

      if (!oppsResult.ok) {
        throw new Error(`Failed to load opportunities: ${oppsResult.text || oppsResult.status}`);
      }

      if (!patentsResult.ok) {
        throw new Error(`Failed to load patents: ${patentsResult.text || patentsResult.status}`);
      }

      setStats(statsResult.data);
      setOpportunities(oppsResult.data.opportunities);
      setPatents(patentsResult.data.items);
    } catch (err) {
      setError(err.message || 'Failed to load PatentPulse data');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !stats) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold mb-6">PatentPulse Dashboard</h1>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {[1, 2, 3, 4].map(i => (
              <Card key={i} className="animate-pulse">
                <CardContent className="pt-6">
                  <div className="h-16 bg-gray-200 rounded"></div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-red-900">
                <AlertCircle className="h-5 w-5" />
                <span>{error}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!stats) return null;

  const getStatusBadgeColor = (status) => {
    switch (status) {
      case 'Expired': return 'bg-green-100 text-green-800';
      case 'Lapsed': return 'bg-blue-100 text-blue-800';
      case 'Expiring': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getScoreBadge = (score, inverse = false) => {
    const value = inverse ? (1 - score) : score;
    if (value >= 0.7) return 'bg-green-100 text-green-800';
    if (value >= 0.4) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">PatentPulse Dashboard</h1>
          <p className="text-gray-600">Patent Mining & Commercialization Intelligence</p>
        </div>

        {/* Partner Shares tab removed - feature deprecated */}
        <div className="space-y-6">

        {/* Stats Tiles */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {/* Total Patents */}
          <Card>
            <CardHeader className="pb-3">
              <CardDescription className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-blue-600" />
                Total Patents Tracked
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">{stats.total}</div>
            </CardContent>
          </Card>

          {/* Expired/Ready */}
          <Card>
            <CardHeader className="pb-3">
              <CardDescription className="flex items-center gap-2">
                <Award className="h-4 w-4 text-green-600" />
                Ready to Commercialize
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">
                {(stats.by_status['Expired'] || 0) + (stats.by_status['Lapsed'] || 0)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {stats.by_status['Expired'] || 0} expired · {stats.by_status['Lapsed'] || 0} lapsed
              </div>
            </CardContent>
          </Card>

          {/* Expiring Soon */}
          <Card>
            <CardHeader className="pb-3">
              <CardDescription className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-orange-600" />
                Expiring Soon (24mo)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-orange-600">{stats.expiring_soon_24mo}</div>
            </CardContent>
          </Card>

          {/* Avg Commercial Score */}
          <Card>
            <CardHeader className="pb-3">
              <CardDescription className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-purple-600" />
                Avg Commercial Score
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-600">
                {(stats.avg_commercial_score * 100).toFixed(0)}%
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Top Opportunities */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="h-5 w-5 text-yellow-600" />
              Top 5 Opportunities
            </CardTitle>
            <CardDescription>Ranked by composite viability score (commercial × ease × FTO)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {opportunities.map((opp, idx) => (
                <div key={opp._id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-bold text-lg text-blue-600">#{idx + 1}</span>
                        <span className="font-semibold">{opp.patent_id}</span>
                        <Badge className={getStatusBadgeColor(opp.status)}>{opp.status}</Badge>
                        {opp.viability_score && (
                          <Badge className="bg-purple-100 text-purple-800">
                            Viability: {(opp.viability_score * 100).toFixed(1)}%
                          </Badge>
                        )}
                      </div>
                      <h3 className="font-medium text-gray-900 mb-1">{opp.title}</h3>
                      <div className="flex items-center gap-4 text-sm text-gray-600 mb-2">
                        <span className="flex items-center gap-1">
                          <Building2 className="h-3 w-3" />
                          {opp.assignee}
                        </span>
                        <span className="flex items-center gap-1">
                          <Globe className="h-3 w-3" />
                          {opp.country}
                        </span>
                        {opp.sequence_data && (
                          <span className="flex items-center gap-1">
                            <Dna className="h-3 w-3" />
                            {opp.sequence_data.length} AA
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-700 mb-2">{opp.repurpose_notes}</p>
                      <div className="flex gap-2">
                        <Badge className={getScoreBadge(opp.commercial_score)}>
                          Commercial: {(opp.commercial_score * 100).toFixed(0)}%
                        </Badge>
                        <Badge className={getScoreBadge(opp.synthesis_score, true)}>
                          Ease: {((1 - opp.synthesis_score) * 100).toFixed(0)}%
                        </Badge>
                        <Badge className={getScoreBadge(opp.fto_risk, true)}>
                          FTO: {((1 - opp.fto_risk) * 100).toFixed(0)}%
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Patents List */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Patent Database</CardTitle>
                <CardDescription>Browse and filter tracked patterns</CardDescription>
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="Expired">Expired</SelectItem>
                  <SelectItem value="Lapsed">Lapsed</SelectItem>
                  <SelectItem value="Expiring">Expiring</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {patents.map((patent) => (
                <div key={patent._id} className="border rounded-lg p-3 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-blue-600">{patent.patent_id}</span>
                        <Badge className={getStatusBadgeColor(patent.status)}>{patent.status}</Badge>
                      </div>
                      <h4 className="font-medium text-sm">{patent.title}</h4>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-600 mb-2">
                    <span>{patent.assignee}</span>
                    <span>•</span>
                    <span>{patent.country}</span>
                    <span>•</span>
                    <span>Expires: {new Date(patent.expiry_date).toLocaleDateString()}</span>
                  </div>
                  <div className="flex gap-2">
                    <Badge variant="outline" className="text-xs">
                      Commercial: {(patent.commercial_score * 100).toFixed(0)}%
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      Synthesis: {(patent.synthesis_score * 100).toFixed(0)}%
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      FTO Risk: {(patent.fto_risk * 100).toFixed(0)}%
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        </div>
      </div>
    </div>
  );
}
