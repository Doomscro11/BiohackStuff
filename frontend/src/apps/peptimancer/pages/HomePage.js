import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { AlertCircle, Dna, Zap, TrendingUp, Clock, DollarSign, Shield, Beaker, Download, Send, CreditCard, Copy, ExternalLink } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
// import AnalogueForm from '@/components/AnalogueForm.js';
import { fetchChemistryOptions, hasClientConflicts } from '@/lib/chemistry';
import { fetchSession } from '@/lib/session';
import { normalizeError, getAxiosErrorMessage } from '@/lib/errorUtils';
import DACTabPanel from '@/components/DACTabPanel';
import MultiSelect from '@/components/ui/MultiSelect';
import TierAwareModPanel from '@/components/modifications/TierAwareModPanel';
import '@/App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [formData, setFormData] = useState({
    base_molecule: 'HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR',
    allowed_mods: [],  // Changed to array for MultiSelect
    exclusions: [],    // Changed to array for MultiSelect
    target_use: 'Metabolic Research / GLP-1R',
    num_analogues: 3,
    include_cost: true
  });
  
  // Chemistry options state
  const [chemOptions, setChemOptions] = useState(null);
  const [conflictMsg, setConflictMsg] = useState(null);
  
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sequenceValidation, setSequenceValidation] = useState(null);
  const [exportLoading, setExportLoading] = useState(false);
  const [synthesisLoading, setSynthesisLoading] = useState(null);
  const [currentMode, setCurrentMode] = useState(null);
  const [featureLevel, setFeatureLevel] = useState(0);
  const [user, setUser] = useState(null);
  const [selectedModifications, setSelectedModifications] = useState({});
  const [copySuccess, setCopySuccess] = useState(null);
  
  const navigate = useNavigate();

  // Handler for copying sequence to clipboard
  const handleCopyForPatentPulse = async (sequence, analogueName) => {
    try {
      await navigator.clipboard.writeText(sequence);
      setCopySuccess(analogueName);
      setTimeout(() => setCopySuccess(null), 3000);
    } catch (error) {
      console.error('Failed to copy:', error);
      alert('Failed to copy sequence. Please copy manually.');
    }
  };

  // Handler for navigating to PatentPulse
  const handleOpenPatentPulse = () => {
    navigate('/admin/patentpulse');
  };

  // Load user session
  useEffect(() => {
    const loadUser = async () => {
      try {
        const session = await fetchSession();
        if (session) {
          setUser(session);
        }
      } catch (error) {
        console.debug('User session not available:', error);
      }
    };
    loadUser();
  }, []);

  // Load current mode and feature level on component mount
  useEffect(() => {
    const loadCurrentMode = async () => {
      try {
        const response = await axios.get(`${API}/mode`);
        setCurrentMode(response.data);
      } catch (error) {
        console.error('Failed to load current mode:', error);
      }
    };
    
    const loadFeatureLevel = async () => {
      try {
        const session = await fetchSession();
        if (session && session.feature_level !== undefined) {
          setFeatureLevel(session.feature_level);
        }
      } catch (error) {
        console.debug('Feature level not available:', error);
      }
    };
    
    loadCurrentMode();
    loadFeatureLevel();
  }, []);

  // Load chemistry options on mount
  useEffect(() => {
    fetchChemistryOptions()
      .then(setChemOptions)
      .catch(() => setChemOptions({ tier: 'basic', mods: [], exclusions: [] }));
  }, []);

  // Check for conflicts when mods or exclusions change
  useEffect(() => {
    if (chemOptions) {
      setConflictMsg(hasClientConflicts(formData.allowed_mods, formData.exclusions));
    }
  }, [formData.allowed_mods, formData.exclusions, chemOptions]);

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
      // Flatten selectedModifications from category structure to array
      const allSelectedMods = Object.values(selectedModifications || {}).flat();
      
      // Convert arrays to comma-separated strings for backend
      const requestData = {
        ...formData,
        allowed_mods: allSelectedMods.join(', '),
        exclusions: formData.exclusions.join(', ')
      };
      
      const response = await axios.post(`${API}/generate-analogues`, requestData);
      setResults(response.data);
    } catch (error) {
      // Use error normalizer to safely handle all error types including Pydantic validation errors
      setError(getAxiosErrorMessage(error, 'Failed to generate analogues'));
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // Phase III: Export Functions
  const handleExportPDF = async (generationId) => {
    setExportLoading(true);
    try {
      const response = await axios.post(`${API}/export-report`, {
        generation_id: generationId,
        format: 'pdf',
        include_cost: formData.include_cost,
        include_ip_analysis: true,
        watermark: true
      }, {
        responseType: 'blob'
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `peptimancer_vault_report_${generationId.slice(0,8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error('Export failed:', error);
      setError('PDF export failed. Please try again.');
    } finally {
      setExportLoading(false);
    }
  };

  // Phase III: Synthesis Request
  const handleSynthesisRequest = async (vaultId, analogueName) => {
    setSynthesisLoading(vaultId);
    try {
      const response = await axios.post(`${API}/request-synthesis`, {
        vault_id: vaultId,
        partner_name: 'CRO Partners Inc.',
        quantity_mg: 100.0,
        purity_requirement: 95.0,
        timeline_days: 14,
        contact_email: 'research@example.com',
        additional_notes: `Synthesis request for ${analogueName}`
      });

      alert(`Synthesis request submitted!\nPartner Reference: ${response.data.partner_response.partner_reference}\nStatus: ${response.data.status}`);
      
    } catch (error) {
      console.error('Synthesis request failed:', error);
      setError('Synthesis request failed. Please try again.');
    } finally {
      setSynthesisLoading(null);
    }
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

  const getModeColor = (color) => {
    switch (color) {
      case 'green': return 'bg-green-100 border-green-500 text-green-800';
      case 'yellow': return 'bg-yellow-100 border-yellow-500 text-yellow-800'; 
      case 'red': return 'bg-red-100 border-red-500 text-red-800';
      default: return 'bg-gray-100 border-gray-500 text-gray-800';
    }
  };

  const getComplexityColor = (complexity) => {
    if (complexity <= 2) return 'bg-green-500';
    if (complexity <= 3) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  // Group modifications by PK intent for better UX
  const groupedMods = useMemo(() => {
    if (!chemOptions) return {};
    
    const groupFor = (m) =>
      (m.pk_intent?.includes('half_life_extension') || m.pk_intent?.includes('albumin_binding')) ? 'PK Extension' :
      (m.pk_intent?.includes('protease_resistance')) ? 'Protease Resistance' :
      (m.pk_intent?.includes('conformational_stability')) ? 'Conformational Stability' :
      (m.pk_intent?.includes('exopeptidase_resistance')) ? 'Exopeptidase Protection' :
      (m.pk_intent?.includes('solubility') || m.pk_intent?.includes('clearance_modulation')) ? 'Solubility/Clearance' :
      (m.pk_intent?.includes('affinity_tuning')) ? 'Affinity Tuning' : 'Other';
    
    const groups = {};
    chemOptions.mods.forEach((m) => {
      const g = groupFor(m);
      groups[g] = groups[g] || [];
      groups[g].push(m);
    });
    
    return groups;
  }, [chemOptions]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="w-full max-w-screen-2xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Dna className="h-8 w-8 text-blue-600" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Peptimancer
            </h1>
            <Badge className="bg-gradient-to-r from-purple-600 to-pink-600 text-white">
              <CreditCard className="h-3 w-3 mr-1" />
              Vault Pro
            </Badge>
          </div>
          
          {/* Mode Indicator */}
          {currentMode && (
            <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full border-2 mb-4 ${getModeColor(currentMode.mode_info?.color)}`}>
              <div className={`w-2 h-2 rounded-full ${
                currentMode.mode_info?.color === 'green' ? 'bg-green-500' :
                currentMode.mode_info?.color === 'yellow' ? 'bg-yellow-500' :
                currentMode.mode_info?.color === 'red' ? 'bg-red-500' : 'bg-gray-500'
              }`} />
              <span className="text-sm font-medium">
                {currentMode.mode_info?.name || 'Unknown Mode'} 
                {currentMode.demo_mode && ' (Demo)'}
              </span>
            </div>
          )}
          
          <p className="text-lg text-gray-600 dark:text-gray-300">
            AI-Powered Peptide Architect • Generate Novel Analogues with Advanced Chemistry
          </p>
          <p className="text-sm text-gray-500 mt-2">
            🔐 Phase III: Export • Synthesis Partners • Pro Vault Access
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
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Base Peptide Sequence */}
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Base Peptide Sequence
                  </label>
                  <textarea
                    className="w-full px-3 py-2 border rounded-md font-mono text-sm"
                    rows="3"
                    value={formData.base_molecule}
                    onChange={(e) => handleInputChange('base_molecule', e.target.value)}
                    placeholder="Enter peptide sequence (e.g., HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR)"
                  />
                  {sequenceValidation && (
                    <p className={`text-xs mt-1 ${sequenceValidation.is_valid ? 'text-green-600' : 'text-red-600'}`}>
                      {sequenceValidation.is_valid ? '✓ Valid sequence' : sequenceValidation.error}
                    </p>
                  )}
                </div>

                {/* Number of Analogues */}
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Number of Analogues
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    className="w-full px-3 py-2 border rounded-md"
                    value={formData.num_analogues}
                    onChange={(e) => handleInputChange('num_analogues', parseInt(e.target.value))}
                  />
                </div>

                {/* Target Use */}
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Target Use
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border rounded-md"
                    value={formData.target_use}
                    onChange={(e) => handleInputChange('target_use', e.target.value)}
                    placeholder="e.g., Metabolic Research / GLP-1R"
                  />
                </div>

                {/* New Accordion-Based Modification UI */}
                <div className="my-6">
                  <TierAwareModPanel
                    user={user}
                    selectedModifications={selectedModifications}
                    onChange={setSelectedModifications}
                  />
                </div>

                {/* Submit Button */}
                <Button 
                  type="submit" 
                  className="w-full"
                  disabled={loading || !sequenceValidation?.is_valid || !formData.base_molecule.trim() || sequenceValidation?.error}
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

                      {/* Export Ready Footer with Phase III Actions */}
                      <div className="flex items-center justify-between pt-4 border-t bg-gray-50 dark:bg-gray-800 -m-6 mt-4 p-4 rounded-b-lg">
                        <div className="text-xs text-gray-500">
                          🔗 Export-ready • Vault-grade format
                        </div>
                        <div className="flex gap-2">
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => handleSynthesisRequest(analogue.vault_id, analogue.analogue_name)}
                            disabled={synthesisLoading === analogue.vault_id}
                            data-testid={`synthesis-request-${index}`}
                          >
                            {synthesisLoading === analogue.vault_id ? (
                              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600 mr-1" />
                            ) : (
                              <Send className="h-3 w-3 mr-1" />
                            )}
                            Synthesis Quote
                          </Button>
                          <Button 
                            size="sm"
                            onClick={() => handleExportPDF(results.request_id)}
                            disabled={exportLoading}
                            data-testid={`export-pdf-${index}`}
                          >
                            {exportLoading ? (
                              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1" />
                            ) : (
                              <Download className="h-3 w-3 mr-1" />
                            )}
                            Export PDF
                          </Button>
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

            {/* DAC Advanced Features Panel (UI Scaffolding Only) */}
            {featureLevel > 0 && (
              <div className="mt-8">
                <DACTabPanel featureLevel={featureLevel} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;