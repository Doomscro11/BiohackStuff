/**
 * PatentPulse Standalone Page
 * Manual candidate review with mock IP insights
 * 
 * IMPORTANT: This is a manual handoff page.
 * No automatic data transfer or real patent search is performed.
 * All analysis results are mock/placeholder data.
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Shield, AlertTriangle, Clipboard, FileText, Globe, TrendingUp, Users, Calendar } from 'lucide-react';

function PatentPulseStandalonePage() {
  const [formData, setFormData] = useState({
    candidate_sequence: '',
    intended_use: '',
    target_jurisdictions: '',
    notes: ''
  });

  const [submitted, setSubmitted] = useState(false);
  const [mockResults, setMockResults] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Generate mock results
    const mock = {
      sequence: formData.candidate_sequence,
      timestamp: new Date().toISOString(),
      crowdedness: {
        level: 'Unknown',
        description: 'Crowdedness analysis requires full PatentPulse (coming soon)',
        badge: 'gray'
      },
      riskBucket: {
        level: 'To be determined',
        description: 'Risk assessment will be available in full PatentPulse release',
        badge: 'yellow'
      },
      mockAssignees: [
        { name: 'ExamplePharm Inc.', patents: 'Mock data', jurisdiction: 'US' },
        { name: 'DemoBio Corp.', patents: 'Mock data', jurisdiction: 'EU' },
        { name: 'SamplePeptides LLC', patents: 'Mock data', jurisdiction: 'JP' }
      ],
      insights: [
        'This is mock placeholder data for demonstration purposes',
        'No real patent search or prior-art analysis is being performed',
        'Full PatentPulse will include comprehensive patent landscape analysis'
      ]
    };

    setMockResults(mock);
    setSubmitted(true);
  };

  const handleReset = () => {
    setFormData({
      candidate_sequence: '',
      intended_use: '',
      target_jurisdictions: '',
      notes: ''
    });
    setSubmitted(false);
    setMockResults(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Page Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
            <Shield className="h-8 w-8 text-blue-600" />
            PatentPulse – Manual Candidate Review
          </h1>
          <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-300">
            Beta – Mock Data Only
          </Badge>
        </div>

        {/* Main Layout: Two Columns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column: Instructions & Disclaimer */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-blue-600" />
                  How to Use This Beta
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 flex items-center justify-center text-sm font-semibold">
                      1
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      <strong>Generate analogues</strong> in Peptimancer using the AI-powered design tool.
                    </p>
                  </div>
                  
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 flex items-center justify-center text-sm font-semibold">
                      2
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      <strong>Copy an analogue</strong> using the "Copy for PatentPulse" button in the results section.
                    </p>
                  </div>
                  
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 flex items-center justify-center text-sm font-semibold">
                      3
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      <strong>Paste the sequence</strong> into the form on the right and submit for mock IP analysis.
                    </p>
                  </div>
                </div>

                <Separator />

                <Alert className="bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700">
                  <AlertTriangle className="h-4 w-4 text-yellow-600" />
                  <AlertDescription className="text-sm text-yellow-800 dark:text-yellow-200">
                    <strong>Important Disclaimer:</strong> This beta view shows placeholder insights only. 
                    No live patent search, prior-art mining, or biochemical IP inference is being performed. 
                    All displayed results are mock data for demonstration purposes.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>

            {/* Future Features Preview */}
            <Card className="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Coming in Full PatentPulse
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="text-xs space-y-2 text-gray-700 dark:text-gray-300">
                  <li className="flex items-center gap-2">
                    <Globe className="h-3 w-3 text-blue-600" />
                    Real-time patent landscape analysis
                  </li>
                  <li className="flex items-center gap-2">
                    <Users className="h-3 w-3 text-purple-600" />
                    Competitor and assignee mapping
                  </li>
                  <li className="flex items-center gap-2">
                    <Calendar className="h-3 w-3 text-green-600" />
                    Prior-art timeline visualization
                  </li>
                  <li className="flex items-center gap-2">
                    <Shield className="h-3 w-3 text-red-600" />
                    Freedom-to-operate analysis
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Input Form & Results */}
          <div className="space-y-6">
            {!submitted ? (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clipboard className="h-5 w-5 text-blue-600" />
                    Candidate Input
                  </CardTitle>
                  <CardDescription>
                    Paste your peptide sequence and provide context for mock IP review
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Candidate Sequence */}
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Candidate Sequence <span className="text-red-500">*</span>
                      </label>
                      <textarea
                        className="w-full px-3 py-2 border rounded-md font-mono text-sm"
                        rows="4"
                        value={formData.candidate_sequence}
                        onChange={(e) => setFormData({ ...formData, candidate_sequence: e.target.value })}
                        placeholder="Paste peptide sequence here (e.g., HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR)"
                        required
                      />
                    </div>

                    {/* Intended Use */}
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Intended Use
                      </label>
                      <textarea
                        className="w-full px-3 py-2 border rounded-md text-sm"
                        rows="2"
                        value={formData.intended_use}
                        onChange={(e) => setFormData({ ...formData, intended_use: e.target.value })}
                        placeholder="e.g., GLP-1 receptor agonist for metabolic disorders"
                      />
                    </div>

                    {/* Target Jurisdictions */}
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Target Jurisdictions
                      </label>
                      <input
                        type="text"
                        className="w-full px-3 py-2 border rounded-md text-sm"
                        value={formData.target_jurisdictions}
                        onChange={(e) => setFormData({ ...formData, target_jurisdictions: e.target.value })}
                        placeholder="e.g., US, EU, JP"
                      />
                    </div>

                    {/* Notes */}
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Additional Notes
                      </label>
                      <textarea
                        className="w-full px-3 py-2 border rounded-md text-sm"
                        rows="2"
                        value={formData.notes}
                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                        placeholder="Any additional context or concerns"
                      />
                    </div>

                    {/* Submit Button */}
                    <Button type="submit" className="w-full">
                      <Shield className="h-4 w-4 mr-2" />
                      Generate Mock IP Insights
                    </Button>
                  </form>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-6">
                {/* Mock Results Display */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Shield className="h-5 w-5 text-blue-600" />
                      Mock IP Analysis Results
                    </CardTitle>
                    <CardDescription>
                      Beta placeholder insights – Not real patent data
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Sequence Display */}
                    <div>
                      <div className="text-sm font-semibold mb-2">Analyzed Sequence:</div>
                      <div className="bg-gray-100 dark:bg-gray-800 p-3 rounded font-mono text-xs break-all">
                        {mockResults.sequence}
                      </div>
                    </div>

                    <Separator />

                    {/* Crowdedness Card */}
                    <Card className="bg-gray-50 dark:bg-gray-800">
                      <CardContent className="pt-6">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm font-semibold">Patent Crowdedness</div>
                          <Badge variant="outline" className="bg-gray-100">
                            {mockResults.crowdedness.level}
                          </Badge>
                        </div>
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          {mockResults.crowdedness.description}
                        </p>
                      </CardContent>
                    </Card>

                    {/* Risk Bucket Card */}
                    <Card className="bg-yellow-50 dark:bg-yellow-900/20">
                      <CardContent className="pt-6">
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm font-semibold">Risk Bucket</div>
                          <Badge variant="outline" className="bg-yellow-100 text-yellow-700">
                            {mockResults.riskBucket.level}
                          </Badge>
                        </div>
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          {mockResults.riskBucket.description}
                        </p>
                      </CardContent>
                    </Card>

                    {/* Mock Assignees */}
                    <div>
                      <div className="text-sm font-semibold mb-3">Top Mock Assignees</div>
                      <div className="space-y-2">
                        {mockResults.mockAssignees.map((assignee, idx) => (
                          <Card key={idx} className="bg-blue-50 dark:bg-blue-900/20">
                            <CardContent className="py-3">
                              <div className="flex items-center justify-between">
                                <div className="text-sm font-medium">{assignee.name}</div>
                                <Badge variant="outline" className="text-xs">
                                  {assignee.jurisdiction}
                                </Badge>
                              </div>
                              <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                                {assignee.patents}
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>

                    {/* Key Insights */}
                    <div>
                      <div className="text-sm font-semibold mb-2">Key Insights (Mock)</div>
                      <ul className="text-xs space-y-2 text-gray-700 dark:text-gray-300">
                        {mockResults.insights.map((insight, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-blue-600 mt-1">•</span>
                            <span>{insight}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Reset Button */}
                    <Button onClick={handleReset} variant="outline" className="w-full mt-4">
                      Analyze Another Sequence
                    </Button>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default PatentPulseStandalonePage;
