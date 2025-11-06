import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { AlertCircle, Dna, Zap, TrendingUp, Clock, DollarSign, Shield, Beaker, Download, Send, CreditCard } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import '@/App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [formData, setFormData] = useState({
    base_molecule: 'HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR',
    allowed_mods: 'Substitution, Lipidation, Cyclization, D-isomers',
    exclusions: 'No Aib or γ-Glu residues', 
    target_use: 'Metabolic Research / GLP-1R',
    num_analogues: 3,
    include_cost: true
  });
  
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sequenceValidation, setSequenceValidation] = useState(null);
  const [exportLoading, setExportLoading] = useState(false);
  const [synthesisLoading, setSynthesisLoading] = useState(null);

  // Validate sequence on change
  useEffect(() => {
    if (formData.base_molecule && formData.base_molecule.trim().length > 0) {
      validateSequence(formData.base_molecule);
    } else {
      setSequenceValidation({ is_valid: false, error: "Empty sequence" });
    }
  }, [formData.base_molecule]);

  const validateSequence = async (sequence) => {
    try {
      const response = await axios.get(`${API}/validate-sequence/${sequence}`);
      setSequenceValidation(response.data);
    } catch (error) {
      console.error('Validation error:', error);
      setSequenceValidation(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResults(null);

    try {
      const response = await axios.post(`${API}/generate-analogues`, formData);
      setResults(response.data);
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to generate analogues');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const getRiskColor = (risk) => {
    if (typeof risk === 'string') {
      switch (risk.toLowerCase()) {
        case 'low': return 'bg-green-500';
        case 'medium': return 'bg-yellow-500';
        case 'high': return 'bg-red-500';
        default: return 'bg-gray-500';
      }
    }
    // Legacy numeric handling
    if (risk <= 3) return 'bg-green-500';
    if (risk <= 6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getNoveltyColor = (score) => {
    if (score >= 70) return 'bg-blue-500';
    if (score >= 40) return 'bg-purple-500';
    return 'bg-gray-500';
  };

  const getComplexityColor = (complexity) => {
    if (complexity <= 2) return 'bg-green-500';
    if (complexity <= 3) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Dna className="h-8 w-8 text-blue-600" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Peptimancer
            </h1>
          </div>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            AI-Powered Peptide Architect • Generate Novel Analogues with Advanced Chemistry
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Input Form */}
          <Card className="h-fit" data-testid="peptide-input-form">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-blue-600" />
                Analogue Generation
              </CardTitle>
              <CardDescription>
                Configure your peptide design parameters for AI-powered analogue generation
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Base Molecule */}
                <div className="space-y-2">
                  <Label htmlFor="base_molecule">Base Molecule Sequence</Label>
                  <Input
                    id="base_molecule"
                    data-testid="base-molecule-input"
                    value={formData.base_molecule}
                    onChange={(e) => handleInputChange('base_molecule', e.target.value.toUpperCase())}
                    placeholder="HAEGTFTSDVSSYLEG..."
                    className="font-mono text-sm"
                  />
                  {sequenceValidation && (
                    <div className="text-xs text-gray-500">
                      {sequenceValidation.is_valid ? (
                        <span className="text-green-600">✓ Valid sequence ({sequenceValidation.length} amino acids)</span>
                      ) : (
                        <span className="text-red-600">✗ {sequenceValidation.error || 'Invalid amino acid sequence'}</span>
                      )}
                    </div>
                  )}
                </div>

                {/* Allowed Modifications */}
                <div className="space-y-2">
                  <Label htmlFor="allowed_mods">Allowed Modifications</Label>
                  <Textarea
                    id="allowed_mods"
                    data-testid="allowed-mods-input"
                    value={formData.allowed_mods}
                    onChange={(e) => handleInputChange('allowed_mods', e.target.value)}
                    placeholder="substitution, D-isomers, lipidation, cyclization"
                    rows={2}
                  />
                </div>

                {/* Exclusions */}
                <div className="space-y-2">
                  <Label htmlFor="exclusions">Exclusion Clauses</Label>
                  <Textarea
                    id="exclusions"
                    data-testid="exclusions-input"
                    value={formData.exclusions}
                    onChange={(e) => handleInputChange('exclusions', e.target.value)}
                    placeholder="proline substitution, N-terminal modifications"
                    rows={2}
                  />
                </div>

                {/* Target Use */}
                <div className="space-y-2">
                  <Label htmlFor="target_use">Target Therapeutic Use</Label>
                  <Textarea
                    id="target_use"
                    data-testid="target-use-input"
                    value={formData.target_use}
                    onChange={(e) => handleInputChange('target_use', e.target.value)}
                    placeholder="GLP-1 receptor agonist for diabetes treatment"
                    rows={2}
                  />
                </div>

                {/* Number of Analogues */}
                <div className="space-y-2">
                  <Label htmlFor="num_analogues">Number of Analogues</Label>
                  <Select
                    value={formData.num_analogues.toString()}
                    onValueChange={(value) => handleInputChange('num_analogues', parseInt(value))}
                  >
                    <SelectTrigger data-testid="num-analogues-select">
                      <SelectValue placeholder="Select number" />
                    </SelectTrigger>
                    <SelectContent>
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                        <SelectItem key={num} value={num.toString()}>{num}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Include Cost Estimates */}
                <div className="flex items-center space-x-2">
                  <Switch
                    id="include_cost"
                    checked={formData.include_cost}
                    onCheckedChange={(checked) => handleInputChange('include_cost', checked)}
                    data-testid="include-cost-switch"
                  />
                  <Label htmlFor="include_cost" className="flex items-center gap-2">
                    <DollarSign className="h-4 w-4" />
                    Include Synthesis Cost Estimates
                  </Label>
                </div>

                {/* Submit Button */}
                <Button 
                  type="submit" 
                  className="w-full"
                  disabled={loading || !sequenceValidation?.is_valid || !formData.base_molecule.trim()}
                  data-testid="generate-analogues-button"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                      Generating Analogues...
                    </>
                  ) : (
                    <>
                      <Dna className="h-4 w-4 mr-2" />
                      Generate Analogues
                    </>
                  )}
                </Button>
              </form>

              {error && (
                <Alert className="mt-4" variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Results Display */}
          <div className="space-y-4">
            {results && (
              <Card data-testid="results-container">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-green-600" />
                    Generated Analogues
                  </CardTitle>
                  <CardDescription>
                    {results.analogues?.length || 0} novel peptide analogues generated for: {results.base_molecule}
                  </CardDescription>
                </CardHeader>
                
                <CardContent className="space-y-4">
                  {results.analogues?.map((analogue, index) => (
                    <div key={index} className="border rounded-lg p-6 space-y-4 bg-white dark:bg-gray-800" data-testid={`analogue-${index}`}>
                      {/* Analogue Header with Vault ID */}
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="text-xl font-bold text-blue-700 dark:text-blue-300 mb-1">
                            🧬 {analogue.analogue_name}
                          </h3>
                          <div className="text-sm text-gray-500 font-mono">
                            🔐 Vault ID: {analogue.vault_id}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Badge className={`${getRiskColor(analogue.patent_similarity_risk)} text-white text-xs`}>
                            {typeof analogue.patent_similarity_risk === 'string' ? 
                              `${analogue.patent_similarity_risk} Risk` : 
                              `Risk: ${analogue.patent_similarity_risk}/10`}
                          </Badge>
                          <Badge className={`${getNoveltyColor(analogue.novelty_score)} text-white text-xs`}>
                            {analogue.novelty_score >= 10 ? 
                              `${Math.round(analogue.novelty_score)}% Novel` : 
                              `Novel: ${analogue.novelty_score}/10`}
                          </Badge>
                        </div>
                      </div>

                      {/* Modified Sequence */}
                      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                        <div className="text-sm font-semibold mb-2 flex items-center gap-2">
                          <Dna className="h-4 w-4" />
                          Sequence:
                        </div>
                        <div className="font-mono text-sm break-all bg-white dark:bg-gray-800 p-2 rounded border">
                          {analogue.modified_sequence}
                        </div>
                      </div>

                      {/* Modifications Applied */}
                      <div>
                        <div className="text-sm font-semibold mb-2 flex items-center gap-2">
                          <Zap className="h-4 w-4" />
                          Modifications Applied:
                        </div>
                        <ul className="text-sm space-y-1 pl-4">
                          {analogue.modifications_applied?.map((mod, idx) => (
                            <li key={idx} className="flex items-start gap-2">
                              <span className="text-blue-600 mt-1">•</span>
                              <span>{mod}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <Separator />

                      {/* IP Risk Profile */}
                      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                        <div className="text-sm font-semibold mb-3 flex items-center gap-2">
                          <Shield className="h-4 w-4 text-blue-600" />
                          📜 IP Risk Profile
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                          <div><strong>Patent Risk:</strong> {analogue.patent_similarity_risk || 'Medium'}</div>
                          <div><strong>Novelty:</strong> {analogue.novelty_score >= 10 ? `${Math.round(analogue.novelty_score)}%` : `${analogue.novelty_score}/10`}</div>
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-300 mt-2">
                          <strong>Notes:</strong> {analogue.ip_notes || 'Patent analysis pending'}
                        </div>
                      </div>

                      {/* Bioactivity Profile */}
                      <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                        <div className="text-sm font-semibold mb-3 flex items-center gap-2">
                          <Beaker className="h-4 w-4 text-green-600" />
                          🧪 Bioactivity Profile
                        </div>
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
                          <div className="flex items-center gap-2">
                            <TrendingUp className="h-4 w-4 text-green-600" />
                            <span><strong>Binding:</strong> {analogue.binding_affinity || -8.5} kcal/mol</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4 text-purple-600" />
                            <span><strong>Half-Life:</strong> {analogue.predicted_half_life || 2.1} days</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge className={`${getComplexityColor(analogue.synthesis_complexity || 3)} text-white text-xs`}>
                              Complexity: {analogue.synthesis_complexity || 3}/5
                            </Badge>
                          </div>
                          {formData.include_cost && analogue.synthesis_cost && (
                            <div className="flex items-center gap-2">
                              <DollarSign className="h-4 w-4 text-yellow-600" />
                              <span><strong>Cost:</strong> ${analogue.synthesis_cost} CAD/mg</span>
                            </div>
                          )}
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-300 mt-3">
                          <strong>Notes:</strong> {analogue.bioactivity_notes || 'Standard GLP-1R profile expected'}
                        </div>
                      </div>

                      {/* Export Ready Footer */}
                      <div className="flex items-center justify-between pt-2 border-t">
                        <div className="text-xs text-gray-500">
                          🔗 Export-ready • Vault-grade format
                        </div>
                        <div className="text-xs text-gray-400">
                          Generated: {new Date().toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {loading && (
              <Card>
                <CardContent className="flex items-center justify-center py-12">
                  <div className="text-center space-y-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
                    <div>
                      <p className="font-medium">Generating Peptide Analogues...</p>
                      <p className="text-sm text-gray-500">AI is analyzing your parameters and designing novel variants</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;