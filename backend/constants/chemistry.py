# Chemistry Constants - Pharmacokinetics-aware options for Peptimancer

# Tier hierarchy for access control
TIER_ORDER = {
    "basic": 0,
    "pro": 1,
    "enterprise": 2
}

# Allowed Modification Options with PK intent and tier gating
ALLOWED_MOD_OPTIONS = {
    # === PK Extension ===
    "pegylation": {
        "label": "PEGylation",
        "tier": "pro",
        "pk_intent": ["half_life_extension", "clearance_modulation"],
        "notes": "Polyethylene glycol conjugation for extended circulation time",
        "typical_targets": ["N-terminus", "Lys side chains"]
    },
    "lipidation": {
        "label": "Lipidation (C16-C20)",
        "tier": "pro",
        "pk_intent": ["half_life_extension", "albumin_binding"],
        "notes": "Fatty acid conjugation for albumin binding and half-life extension",
        "typical_targets": ["Lys", "N-terminus"]
    },
    "glycosylation": {
        "label": "Glycosylation (O/N)",
        "tier": "enterprise",
        "pk_intent": ["half_life_extension", "solubility", "protease_resistance"],
        "notes": "Sugar moiety attachment for stability and circulation",
        "typical_targets": ["Ser", "Thr", "Asn"]
    },
    
    # === Protease Resistance ===
    "d_isomers": {
        "label": "D-amino acids",
        "tier": "basic",
        "pk_intent": ["protease_resistance"],
        "notes": "Enantiomeric substitution for protease stability",
        "typical_targets": ["any position"]
    },
    "n_methylation": {
        "label": "N-methylation",
        "tier": "pro",
        "pk_intent": ["protease_resistance", "conformational_stability"],
        "notes": "Backbone N-methyl for protease resistance",
        "typical_targets": ["backbone amides"]
    },
    "peptoid": {
        "label": "Peptoid residues",
        "tier": "enterprise",
        "pk_intent": ["protease_resistance", "conformational_stability"],
        "notes": "N-substituted glycine for extreme protease resistance",
        "typical_targets": ["flexible regions"]
    },
    
    # === Conformational Stability ===
    "cyclization": {
        "label": "Cyclization (lactam bridge)",
        "tier": "basic",
        "pk_intent": ["conformational_stability", "protease_resistance"],
        "notes": "Intramolecular bridge for structural rigidity",
        "typical_targets": ["Glu-Lys", "Asp-Lys", "Cys-Cys"]
    },
    "stapling": {
        "label": "Hydrocarbon stapling",
        "tier": "enterprise",
        "pk_intent": ["conformational_stability", "affinity_tuning"],
        "notes": "All-hydrocarbon crosslink for α-helix stabilization",
        "typical_targets": ["i, i+4 or i+7 positions"]
    },
    
    # === Exopeptidase Protection ===
    "acetylation": {
        "label": "N-acetylation",
        "tier": "basic",
        "pk_intent": ["exopeptidase_resistance"],
        "notes": "N-terminal acetyl cap for exopeptidase protection",
        "typical_targets": ["N-terminus"]
    },
    "amidation": {
        "label": "C-amidation",
        "tier": "basic",
        "pk_intent": ["exopeptidase_resistance"],
        "notes": "C-terminal amide for exopeptidase protection",
        "typical_targets": ["C-terminus"]
    },
    
    # === Solubility/Clearance ===
    "charge_modification": {
        "label": "Charge modification (phosphorylation/sulfonation)",
        "tier": "pro",
        "pk_intent": ["solubility", "clearance_modulation"],
        "notes": "Addition of charged groups for solubility tuning",
        "typical_targets": ["Ser", "Thr", "Tyr"]
    },
    
    # === Affinity Tuning ===
    "substitution": {
        "label": "Conservative substitution",
        "tier": "basic",
        "pk_intent": ["affinity_tuning"],
        "notes": "Amino acid replacement with similar properties",
        "typical_targets": ["non-critical positions"]
    },
    "unnatural_aa": {
        "label": "Unnatural amino acids",
        "tier": "enterprise",
        "pk_intent": ["affinity_tuning", "protease_resistance"],
        "notes": "Non-canonical residues for enhanced properties",
        "typical_targets": ["binding interface"]
    }
}

# Exclusion Options with tier gating
EXCLUSION_OPTIONS = {
    "no_extra_cys": {
        "label": "No extra Cys residues",
        "tier": "basic"
    },
    "no_aib": {
        "label": "No α-aminoisobutyric acid (Aib)",
        "tier": "basic"
    },
    "no_gamma_glu": {
        "label": "No γ-Glu residues",
        "tier": "basic"
    },
    "no_beta_ala": {
        "label": "No β-Ala residues",
        "tier": "basic"
    },
    "no_linker_conflicts": {
        "label": "No PEG + Lipidation combo",
        "tier": "pro"
    },
    "no_n_methyl_pro": {
        "label": "No N-methyl-Pro",
        "tier": "pro"
    },
    "preserve_disulfides": {
        "label": "Preserve existing disulfide bridges",
        "tier": "basic"
    },
    "avoid_aggregation_motifs": {
        "label": "Avoid aggregation-prone sequences",
        "tier": "pro"
    },
    "maintain_charge_balance": {
        "label": "Maintain overall charge balance",
        "tier": "basic"
    },
    "no_reactive_handles": {
        "label": "No highly reactive functional groups",
        "tier": "enterprise"
    }
}

# Server-side conflict rules (authoritative)
CONFLICT_RULES = [
    {
        "mods": ["pegylation", "lipidation"],
        "exclusion": "no_linker_conflicts",
        "message": "PEG + Lipidation combo blocked by exclusion clause"
    },
    {
        "mods": ["acetylation", "lipidation"],
        "message": "N-acetylation and lipidation may conflict on same residue"
    },
    {
        "mods": ["cyclization"],
        "exclusion": "no_extra_cys",
        "message": "Cyclization may require extra Cys residues"
    }
]

# Validation caps
MAX_MOD_CLASSES = 3
MAX_EXCLUSIONS = 6
