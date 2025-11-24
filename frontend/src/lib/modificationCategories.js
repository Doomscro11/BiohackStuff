/**
 * Modification Categories Data Model
 * Defines all modification categories and their options
 * 
 * CRITICAL: This is 100% mock data for UI purposes only.
 * NO real chemistry, NO real predictions, NO real modeling.
 */

export const MODIFICATION_CATEGORIES = [
  {
    id: "pk_ext",
    title: "PK Extension",
    description: "Modifications that extend pharmacokinetic half-life (mock)",
    proOnly: true,
    options: [
      {
        id: "PEGylation",
        label: "PEGylation",
        notes: "Attach polyethylene glycol chains to increase half-life (mock placeholder)",
        default: false,
        tier: "pro"
      },
      {
        id: "Lipidation",
        label: "Lipidation",
        notes: "Add lipid chains for albumin binding and extended circulation (mock)",
        default: false,
        tier: "pro"
      },
      {
        id: "Albumin-binding Tag",
        label: "Albumin-binding Tag",
        notes: "Peptide sequences that bind to serum albumin (mock)",
        default: false,
        tier: "pro"
      },
      {
        id: "Cyclization",
        label: "Cyclization",
        notes: "Form cyclic structure for improved stability (mock)",
        default: false,
        tier: "pro"
      }
    ]
  },
  {
    id: "protease_resistance",
    title: "Protease Resistance",
    description: "Modifications that protect against protease degradation (mock)",
    proOnly: false,
    options: [
      {
        id: "D-amino acids (Multiple Positions)",
        label: "D-amino acids (Multiple Positions)",
        notes: "Replace multiple L-amino acids with D-forms for protease resistance (mock)",
        default: false,
        tier: "basic"
      },
      {
        id: "D-amino acids (C-terminus)",
        label: "D-amino acids (C-terminus)",
        notes: "D-amino acid substitution at C-terminus (mock)",
        default: false,
        tier: "basic"
      },
      {
        id: "N-methylation",
        label: "N-methylation",
        notes: "Methylate backbone nitrogen to block protease recognition (mock)",
        default: false,
        tier: "pro"
      },
      {
        id: "Backbone modification",
        label: "Backbone modification",
        notes: "Alter peptide backbone structure (mock placeholder)",
        default: false,
        tier: "pro"
      }
    ]
  },
  {
    id: "exopeptidase_protection",
    title: "Exopeptidase Protection",
    description: "Modifications that protect terminal amino acids (mock)",
    proOnly: false,
    options: [
      {
        id: "Acetylation (N-cap)",
        label: "Acetylation (N-cap)",
        notes: "Cap N-terminus with acetyl group (mock)",
        default: true,
        tier: "basic"
      },
      {
        id: "Amidation (C-cap)",
        label: "Amidation (C-cap)",
        notes: "Cap C-terminus with amide group (mock)",
        default: true,
        tier: "basic"
      },
      {
        id: "Pyroglutamate formation",
        label: "Pyroglutamate formation",
        notes: "Cyclize N-terminal glutamine to pyroglutamate (mock)",
        default: false,
        tier: "basic"
      }
    ]
  },
  {
    id: "solubility_clearance",
    title: "Solubility & Clearance",
    description: "Modifications affecting solubility and clearance rates (mock)",
    proOnly: false,
    options: [
      {
        id: "Charged residue addition",
        label: "Charged residue addition",
        notes: "Add charged amino acids to improve solubility (mock)",
        default: false,
        tier: "basic"
      },
      {
        id: "Hydrophobic patch reduction",
        label: "Hydrophobic patch reduction",
        notes: "Reduce aggregation-prone hydrophobic regions (mock)",
        default: false,
        tier: "basic"
      },
      {
        id: "Glycosylation",
        label: "Glycosylation",
        notes: "Attach sugar moieties for improved properties (mock)",
        default: false,
        tier: "pro"
      }
    ]
  },
  {
    id: "affinity_tuning",
    title: "Affinity Tuning (Mock/Placeholder)",
    description: "Modifications for target binding affinity (mock - no real predictions)",
    proOnly: true,
    options: [
      {
        id: "Unnatural amino acids",
        label: "Unnatural amino acids",
        notes: "Incorporate non-standard amino acids for enhanced binding (mock)",
        default: false,
        tier: "pro"
      },
      {
        id: "Conformational constraint",
        label: "Conformational constraint",
        notes: "Constrain peptide structure for optimal binding (mock)",
        default: false,
        tier: "pro"
      },
      {
        id: "Side-chain modification",
        label: "Side-chain modification",
        notes: "Modify amino acid side chains for better interactions (mock)",
        default: false,
        tier: "pro"
      }
    ]
  },
  {
    id: "exclusion_clauses",
    title: "Exclusion Clauses",
    description: "Specify modifications to avoid (mock)",
    proOnly: false,
    options: [
      {
        id: "No_oxidizable_residues",
        label: "Avoid oxidizable residues (Met, Cys)",
        notes: "Prevent oxidation-prone amino acids (mock)",
        default: false,
        tier: "basic"
      },
      {
        id: "No_aggregation_prone",
        label: "Minimize aggregation risk",
        notes: "Avoid sequences prone to aggregation (mock)",
        default: false,
        tier: "basic"
      },
      {
        id: "No_immunogenic_motifs",
        label: "Exclude potential immunogenic motifs",
        notes: "Avoid sequences that may trigger immune response (mock)",
        default: false,
        tier: "basic"
      },
      {
        id: "No_multiple_charges",
        label: "Limit consecutive charged residues",
        notes: "Avoid runs of charged amino acids (mock)",
        default: false,
        tier: "basic"
      },
      {
        id: "No_disulfide_formation",
        label: "Prevent disulfide bond formation",
        notes: "Avoid cysteine pairs that could form unwanted bonds (mock)",
        default: false,
        tier: "basic"
      },
      {
        id: "No_protease_sites",
        label: "Remove known protease cleavage sites",
        notes: "Identify and modify protease recognition sequences (mock)",
        default: false,
        tier: "pro"
      }
    ]
  }
];

/**
 * Get all modification options across all categories
 * @returns {Array} Flat array of all modification options
 */
export function getAllModificationOptions() {
  return MODIFICATION_CATEGORIES.flatMap(category => 
    category.options.map(option => ({
      ...option,
      categoryId: category.id,
      categoryTitle: category.title
    }))
  );
}

/**
 * Get categories accessible to a given user tier
 * @param {string} userTier - 'basic', 'pro', or 'enterprise'
 * @returns {Array} Filtered categories
 */
export function getCategoriesForTier(userTier = 'basic') {
  if (userTier === 'enterprise' || userTier === 'pro') {
    // Pro and enterprise see all categories
    return MODIFICATION_CATEGORIES;
  }
  
  // Basic users see only non-pro categories
  return MODIFICATION_CATEGORIES.filter(cat => !cat.proOnly);
}

/**
 * Get options for a specific category filtered by tier
 * @param {string} categoryId - Category ID
 * @param {string} userTier - User tier
 * @returns {Array} Filtered options
 */
export function getOptionsForCategory(categoryId, userTier = 'basic') {
  const category = MODIFICATION_CATEGORIES.find(cat => cat.id === categoryId);
  if (!category) return [];
  
  if (userTier === 'enterprise' || userTier === 'pro') {
    return category.options;
  }
  
  // Basic users see only basic-tier options
  return category.options.filter(opt => opt.tier === 'basic');
}

/**
 * Get default selected modifications
 * @returns {Object} Object with category IDs as keys and arrays of selected option IDs as values
 */
export function getDefaultSelections() {
  const defaults = {};
  
  MODIFICATION_CATEGORIES.forEach(category => {
    const defaultOptions = category.options
      .filter(opt => opt.default)
      .map(opt => opt.id);
    
    if (defaultOptions.length > 0) {
      defaults[category.id] = defaultOptions;
    }
  });
  
  return defaults;
}
