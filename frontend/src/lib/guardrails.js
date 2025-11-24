/**
 * Guardrails System (UI-Only Mock Data)
 * 
 * IMPORTANT: This is 100% mock data for UI purposes only.
 * NO real chemistry, NO real predictions, NO real modeling.
 * All content is fictional placeholder text.
 */

export const GUARDRAILS = [
  {
    id: "bulk_conflict",
    title: "High Steric Burden Conflict",
    description: "These modifications both add significant molecular bulk that may cause steric interference (mock placeholder explanation)",
    applicableWhen: ["PEGylation", "Albumin-binding Tag"],
    severity: "high",
    rationale: "Steric and conformational interference placeholder rationale. This is mock data only, not real structural analysis.",
    category: "pk_ext"
  },
  {
    id: "protease_redundancy",
    title: "Redundant Protease Protection",
    description: "Combining multiple D-amino acid substitutions may not provide additional benefit (mock placeholder)",
    applicableWhen: ["D-amino acids (Multiple Positions)", "D-amino acids (C-terminus)"],
    severity: "medium",
    rationale: "Diminishing returns from redundant modifications. Mock explanation only.",
    category: "protease_resistance"
  },
  {
    id: "cyclization_bulk",
    title: "Cyclization + Bulk Modification Conflict",
    description: "Large modifications may interfere with cyclization ring closure (mock placeholder)",
    applicableWhen: ["Cyclization", "PEGylation"],
    severity: "high",
    rationale: "Structural constraints on ring formation. Placeholder explanation, not real chemistry.",
    category: "pk_ext"
  },
  {
    id: "lipid_albumin_conflict",
    title: "Lipidation + Albumin Binding Redundancy",
    description: "Both modifications target albumin binding via different mechanisms (mock)",
    applicableWhen: ["Lipidation", "Albumin-binding Tag"],
    severity: "medium",
    rationale: "Redundant albumin-targeting strategies. Mock reasoning only.",
    category: "pk_ext"
  },
  {
    id: "multiple_termini_mods",
    title: "Over-modification of Termini",
    description: "Too many modifications at N- and C-termini may affect peptide stability (mock)",
    applicableWhen: ["Acetylation (N-cap)", "Amidation (C-cap)", "D-amino acids (C-terminus)"],
    severity: "low",
    rationale: "Cumulative structural effects placeholder. Not real analysis.",
    category: "exopeptidase_protection"
  },
  {
    id: "peg_lipid_solubility",
    title: "Conflicting Solubility Strategies",
    description: "PEGylation increases solubility while lipidation decreases it (mock)",
    applicableWhen: ["PEGylation", "Lipidation"],
    severity: "medium",
    rationale: "Opposing physicochemical effects. Placeholder explanation only.",
    category: "solubility_clearance"
  },
  {
    id: "n_methyl_backbone",
    title: "N-methylation Backbone Flexibility Warning",
    description: "N-methylation may alter backbone conformation in unpredictable ways (mock)",
    applicableWhen: ["N-methylation"],
    severity: "low",
    rationale: "Conformational uncertainty placeholder. Mock warning only.",
    category: "protease_resistance"
  },
  {
    id: "unnatural_aa_stability",
    title: "Multiple Unnatural Amino Acids",
    description: "Combining many unnatural amino acids may affect overall peptide stability (mock)",
    applicableWhen: ["Unnatural amino acids", "D-amino acids (Multiple Positions)"],
    severity: "low",
    rationale: "Cumulative structural changes. Not real stability prediction.",
    category: "affinity_tuning"
  },
  {
    id: "max_modifications_warning",
    title: "Maximum Modification Threshold",
    description: "Selecting more than 5 modifications may lead to complex interactions (mock)",
    applicableWhen: [], // Special rule - checks total count
    severity: "medium",
    rationale: "Complexity threshold placeholder. This is not a real chemical constraint.",
    category: "general"
  }
];

/**
 * Get guardrails that apply to selected modifications
 * @param {Array} selectedModifications - Array of selected modification IDs
 * @returns {Array} Array of applicable guardrails with severity
 */
export function getApplicableGuardrails(selectedModifications) {
  if (!selectedModifications || selectedModifications.length === 0) {
    return [];
  }

  const applicableRules = [];

  // Check each guardrail rule
  GUARDRAILS.forEach(rule => {
    // Special handling for max modifications rule
    if (rule.id === "max_modifications_warning") {
      if (selectedModifications.length > 5) {
        applicableRules.push({
          ...rule,
          triggered: true,
          matchedMods: selectedModifications
        });
      }
      return;
    }

    // Check if all conditions in applicableWhen are present in selection
    const matchedMods = rule.applicableWhen.filter(mod => 
      selectedModifications.includes(mod)
    );

    // Rule triggers if at least 2 of its conditions are met (for conflict rules)
    if (matchedMods.length >= 2) {
      applicableRules.push({
        ...rule,
        triggered: true,
        matchedMods
      });
    }
  });

  // Sort by severity (high -> medium -> low)
  const severityOrder = { high: 0, medium: 1, low: 2 };
  applicableRules.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);

  return applicableRules;
}

/**
 * Get severity color class for UI
 * @param {string} severity - "low", "medium", or "high"
 * @returns {string} Tailwind color classes
 */
export function getSeverityColor(severity) {
  const colors = {
    low: 'bg-yellow-100 text-yellow-800 border-yellow-300 dark:bg-yellow-900/20 dark:text-yellow-200 dark:border-yellow-800',
    medium: 'bg-orange-100 text-orange-800 border-orange-300 dark:bg-orange-900/20 dark:text-orange-200 dark:border-orange-800',
    high: 'bg-red-100 text-red-800 border-red-300 dark:bg-red-900/20 dark:text-red-200 dark:border-red-800'
  };
  return colors[severity] || colors.low;
}

/**
 * Get severity icon
 * @param {string} severity - "low", "medium", or "high"
 * @returns {string} Icon emoji
 */
export function getSeverityIcon(severity) {
  const icons = {
    low: '⚠️',
    medium: '⚠️',
    high: '🚫'
  };
  return icons[severity] || '⚠️';
}
