from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import asyncio
import re
from emergentintegrations.llm.chat import LlmChat, UserMessage
import hashlib
from fpdf import FPDF
import json
from io import BytesIO
import tempfile
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import admin routes
from .routes_admin import admin_router
from .services.settings import get_settings, is_feature_enabled

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Thread pool for concurrent operations
thread_pool = ThreadPoolExecutor(max_workers=10)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Peptimancer - AI Peptide Architect", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Peptide Models
class PeptideAnalogue(BaseModel):
    analogue_name: str
    modified_sequence: str
    modifications_applied: List[str]
    modification_positions: List[str]
    
    # Enhanced Vault-grade fields
    patent_similarity_risk: str = Field(..., description="Low/Medium/High patent risk")
    novelty_score: float = Field(..., ge=0, le=100, description="Novelty percentage 0-100")
    ip_notes: str = Field(..., description="IP analysis notes")
    
    binding_affinity: float = Field(..., description="GLP-1R binding affinity (ΔG kcal/mol)")
    predicted_half_life: float = Field(..., description="Predicted half-life in days")
    synthesis_complexity: int = Field(..., ge=1, le=5, description="Synthesis complexity 1-5")
    synthesis_cost: Optional[float] = Field(None, description="Cost estimate CAD/mg")
    bioactivity_notes: str = Field(..., description="Bioactivity analysis notes")
    
    vault_id: str = Field(..., description="Unique Vault identifier")
    
    # Legacy compatibility fields (deprecated but maintained)
    ip_risk_score: float = Field(default=0.0, ge=0, le=10, description="Legacy IP risk score")
    novelty_score_legacy: float = Field(default=0.0, ge=0, le=10, description="Legacy novelty score") 
    affinity_estimate: str = Field(default="", description="Legacy affinity estimate")
    pk_estimate: str = Field(default="", description="Legacy PK estimate")

class PeptideGenerationRequest(BaseModel):
    generation_id: str = Field(..., description="Unique generation identifier")
    base_molecule: str = Field(..., description="1-letter amino acid sequence")
    allowed_mods: str = Field(..., description="Comma-separated list of allowed modifications")
    exclusions: str = Field(..., description="Exclusion clauses for modifications")
    target_use: str = Field(..., description="Target therapeutic use or application")
    num_analogues: int = Field(..., ge=1, le=10, description="Number of analogues to generate (1-10)")
    include_cost: bool = Field(default=False, description="Include synthesis cost estimates")

class PeptideGenerationResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    base_molecule: str
    analogues: List[PeptideAnalogue]

# Phase III Models
class VaultLedgerEntry(BaseModel):
    vault_id: str
    generation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    base_molecule: str
    analogue_data: Dict[str, Any]
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    export_count: int = Field(default=0)
    synthesis_requests: List[Dict[str, Any]] = Field(default_factory=list)

class SynthesisRequest(BaseModel):
    vault_id: str
    partner_name: str = Field(..., description="CRO/synthesis partner name")
    quantity_mg: float = Field(..., description="Requested quantity in mg")
    purity_requirement: float = Field(default=95.0, description="Required purity %")
    timeline_days: int = Field(..., description="Requested timeline in days")
    contact_email: str = Field(..., description="Contact email for quote")
    additional_notes: Optional[str] = None

class ExportRequest(BaseModel):
    generation_id: str
    format: str = Field(default="pdf", description="Export format: pdf, csv, json")
    include_cost: bool = Field(default=True)
    include_ip_analysis: bool = Field(default=True)
    watermark: bool = Field(default=True)

class ProVaultToken(BaseModel):
    token_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    credits: int = Field(default=0)
    tier: str = Field(default="basic", description="basic, pro, enterprise")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None


# Advanced Peptide Chemistry Logic
class PeptideProcessor:
    def __init__(self):
        self.amino_acids = {
            'A': 'Alanine', 'R': 'Arginine', 'N': 'Asparagine', 'D': 'Aspartic acid',
            'C': 'Cysteine', 'Q': 'Glutamine', 'E': 'Glutamic acid', 'G': 'Glycine',
            'H': 'Histidine', 'I': 'Isoleucine', 'L': 'Leucine', 'K': 'Lysine',
            'M': 'Methionine', 'F': 'Phenylalanine', 'P': 'Proline', 'S': 'Serine',
            'T': 'Threonine', 'W': 'Tryptophan', 'Y': 'Tyrosine', 'V': 'Valine'
        }
        
        self.d_isomers = {
            'A': 'D-Ala', 'F': 'D-Phe', 'L': 'D-Leu', 'V': 'D-Val',
            'I': 'D-Ile', 'P': 'D-Pro', 'W': 'D-Trp', 'Y': 'D-Tyr'
        }
        
        self.lipidation_sites = ['K', 'N', 'C']  # Lysine, N-terminus, Cysteine
        self.lipid_chains = ['C16', 'C18', 'PEG3']
        
        self.cyclization_pairs = {
            ('C', 'C'): 'disulfide',
            ('K', 'E'): 'lactam',
            ('D', 'K'): 'lactam'
        }

    def validate_sequence(self, sequence: str) -> dict:
        """Enhanced validation with detailed error information"""
        if not sequence or len(sequence.strip()) == 0:
            return {
                "is_valid": False,
                "error": "Empty sequence provided",
                "error_code": "EMPTY_SEQUENCE"
            }
        
        # Clean sequence and convert to uppercase
        clean_sequence = sequence.strip().upper()
        
        # Check for non-alphabetic characters (except spaces which are removed)
        non_alpha_chars = [char for char in clean_sequence if not char.isalpha()]
        if non_alpha_chars:
            return {
                "is_valid": False,
                "error": f"Invalid characters found: {', '.join(set(non_alpha_chars))}",
                "error_code": "INVALID_CHARACTERS"
            }
        
        # Check for invalid amino acids
        invalid_aas = [aa for aa in clean_sequence if aa not in self.amino_acids]
        if invalid_aas:
            return {
                "is_valid": False,
                "error": f"Invalid amino acids: {', '.join(set(invalid_aas))}. Valid amino acids: {', '.join(sorted(self.amino_acids.keys()))}",
                "error_code": "INVALID_AMINO_ACIDS"
            }
        
        # Check sequence length (reasonable bounds)
        if len(clean_sequence) > 1000:
            return {
                "is_valid": False,
                "error": f"Sequence too long ({len(clean_sequence)} amino acids). Maximum allowed: 1000",
                "error_code": "SEQUENCE_TOO_LONG"
            }
        
        return {
            "is_valid": True,
            "clean_sequence": clean_sequence,
            "length": len(clean_sequence),
            "composition": {aa: clean_sequence.count(aa) for aa in set(clean_sequence)}
        }

    def get_modification_suggestions(self, sequence: str, allowed_mods: str, exclusions: str) -> List[dict]:
        """Generate intelligent modification suggestions based on sequence analysis"""
        modifications = []
        
        # Parse allowed modifications
        allowed = [mod.strip().lower() for mod in allowed_mods.split(',')]
        excluded = [ex.strip().lower() for ex in exclusions.split(',')]
        
        for i, aa in enumerate(sequence):
            pos = i + 1
            
            # Amino acid substitutions
            if 'substitution' in allowed and 'substitution' not in excluded:
                for target_aa, d_form in self.d_isomers.items():
                    if aa != target_aa:
                        modifications.append({
                            'type': 'substitution',
                            'position': pos,
                            'original': aa,
                            'target': target_aa,
                            'description': f"Position {pos}: {aa} → {target_aa}"
                        })
                        
                        # Add D-isomer variant
                        modifications.append({
                            'type': 'd_isomer',
                            'position': pos,
                            'original': aa,
                            'target': d_form,
                            'description': f"Position {pos}: {aa} → {d_form}"
                        })
            
            # Lipidation
            if 'lipidation' in allowed and 'lipidation' not in excluded:
                if aa in self.lipidation_sites:
                    for lipid in self.lipid_chains:
                        modifications.append({
                            'type': 'lipidation',
                            'position': pos,
                            'site': aa,
                            'lipid': lipid,
                            'description': f"Position {pos}: {aa} lipidated with {lipid}"
                        })
        
        # Cyclization opportunities
        if 'cyclization' in allowed and 'cyclization' not in excluded:
            for i, aa1 in enumerate(sequence):
                for j, aa2 in enumerate(sequence[i+3:], i+4):  # Minimum 3 aa gap
                    if (aa1, aa2) in self.cyclization_pairs:
                        bridge_type = self.cyclization_pairs[(aa1, aa2)]
                        modifications.append({
                            'type': 'cyclization',
                            'position1': i + 1,
                            'position2': j + 1,
                            'aa1': aa1,
                            'aa2': aa2,
                            'bridge': bridge_type,
                            'description': f"Cyclization: {aa1}{i+1} - {aa2}{j+1} ({bridge_type} bridge)"
                        })
        
        return modifications

def generate_vault_id(sequence: str, modifications: List[str]) -> str:
    """Generate unique Vault ID from sequence and modifications"""
    # Create hash from sequence + modifications
    content = f"{sequence}{''.join(modifications)}"
    hash_obj = hashlib.sha256(content.encode())
    hash_hex = hash_obj.hexdigest()
    
    # Take first 7 characters and make uppercase
    hash7 = hash_hex[:7].upper()
    return f"PMNC-{hash7}"

# Phase III: PDF Export System
class VaultPDFGenerator:
    """Generate Vault-grade PDF reports for peptide analogues"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "vault_exports"
        self.temp_dir.mkdir(exist_ok=True)
    
    def generate_report(self, generation_response: PeptideGenerationResponse, 
                       include_cost: bool = True, watermark: bool = True) -> str:
        """Generate PDF report and return file path"""
        
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font('Arial', 'B', 20)
        pdf.cell(0, 15, 'Peptimancer Vault Report', ln=True, align='C')
        
        if watermark:
            pdf.set_font('Arial', 'I', 8)
            pdf.cell(0, 5, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M UTC")} | vault.peptologic.ai', ln=True, align='C')
        
        pdf.ln(10)
        
        # Base Information
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Base Molecule Analysis', ln=True)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, f'Sequence: {generation_response.base_molecule}', ln=True)
        pdf.cell(0, 8, f'Length: {len(generation_response.base_molecule)} amino acids', ln=True)
        pdf.cell(0, 8, f'Generation ID: {generation_response.request_id}', ln=True)
        pdf.ln(5)
        
        # Analogues
        for i, analogue in enumerate(generation_response.analogues, 1):
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, f'Analogue {i}: {analogue.analogue_name}', ln=True)
            
            pdf.set_font('Arial', '', 9)
            pdf.cell(0, 6, f'Vault ID: {analogue.vault_id}', ln=True)
            
            # Sequence
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(0, 6, 'Modified Sequence:', ln=True)
            pdf.set_font('Courier', '', 8)
            pdf.multi_cell(0, 5, analogue.modified_sequence)
            pdf.ln(2)
            
            # Modifications
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(0, 6, 'Modifications Applied:', ln=True)
            pdf.set_font('Arial', '', 8)
            for mod in analogue.modifications_applied:
                pdf.cell(0, 5, f'- {mod}', ln=True)
            pdf.ln(2)
            
            # IP Risk Profile
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(0, 6, 'IP Risk Profile:', ln=True)
            pdf.set_font('Arial', '', 8)
            pdf.cell(0, 5, f'Patent Risk: {analogue.patent_similarity_risk}', ln=True)
            pdf.cell(0, 5, f'Novelty Score: {analogue.novelty_score}%', ln=True)
            pdf.multi_cell(0, 4, f'Notes: {analogue.ip_notes}')
            pdf.ln(2)
            
            # Bioactivity Profile
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(0, 6, 'Bioactivity Profile:', ln=True)
            pdf.set_font('Arial', '', 8)
            pdf.cell(0, 5, f'Binding Affinity: {analogue.binding_affinity} kcal/mol', ln=True)
            pdf.cell(0, 5, f'Predicted Half-Life: {analogue.predicted_half_life} days', ln=True)
            pdf.cell(0, 5, f'Synthesis Complexity: {analogue.synthesis_complexity}/5', ln=True)
            
            if include_cost and analogue.synthesis_cost:
                pdf.cell(0, 5, f'Estimated Cost: ${analogue.synthesis_cost} CAD/mg', ln=True)
            
            pdf.multi_cell(0, 4, f'Notes: {analogue.bioactivity_notes}')
            pdf.ln(8)
        
        # Footer
        pdf.ln(10)
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 5, 'This report contains proprietary peptide designs. Handle confidentially.', ln=True, align='C')
        pdf.cell(0, 5, 'Generated by Peptimancer AI - vault.peptologic.ai', ln=True, align='C')
        
        # Save PDF
        filename = f"vault_report_{generation_response.request_id[:8]}.pdf"
        filepath = self.temp_dir / filename
        pdf.output(str(filepath))
        
        return str(filepath)

# Initialize LLM Chat
async def get_llm_chat():
    return LlmChat(
        api_key=os.environ.get('EMERGENT_LLM_KEY'),
        session_id=str(uuid.uuid4()),
        system_message="""You are Peptimancer, an expert AI peptide architect specializing in generating novel peptide analogues. 

Your expertise includes:
- Advanced peptide chemistry (substitutions, D-isomers, lipidation, cyclization)
- Structure-activity relationships (SAR)
- Pharmacokinetic optimization
- Intellectual property considerations
- Biological plausibility assessment

For each analogue, provide:
1. A unique descriptive name
2. Modified sequence with clear notation
3. 1-3 specific modifications applied
4. Precise modification positions
5. IP risk assessment (0-10 scale)
6. Novelty score (0-10 scale) 
7. Affinity estimate (qualitative)
8. PK estimate (qualitative)

Focus on creating patent-differentiated analogues that preserve or enhance biological function."""
    ).with_model("openai", "gpt-4")

async def generate_peptide_analogues(request: PeptideGenerationRequest) -> List[PeptideAnalogue]:
    """Generate peptide analogues using AI-powered design"""
    processor = PeptideProcessor()
    
    # Enhanced validation with detailed error reporting
    validation_result = processor.validate_sequence(request.base_molecule)
    if not validation_result["is_valid"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid base molecule sequence: {validation_result['error']}"
        )
    
    # Use clean sequence for processing
    clean_sequence = validation_result["clean_sequence"]
    
    # Validate other required fields
    if not request.allowed_mods.strip():
        raise HTTPException(status_code=400, detail="Allowed modifications cannot be empty")
    
    if not request.target_use.strip():
        raise HTTPException(status_code=400, detail="Target therapeutic use cannot be empty")
    
    # Get modification suggestions using clean sequence
    modifications = processor.get_modification_suggestions(
        clean_sequence, request.allowed_mods, request.exclusions
    )
    
    # Prepare AI prompt using clean sequence with enhanced Vault-grade format
    prompt = f"""You are Peptimancer, an AI-powered peptide architect. Generate {request.num_analogues} scientifically valid, patent-aware peptide analogues.

BASE PARAMETERS:
Base Molecule: {clean_sequence}
Allowed Modifications: {request.allowed_mods}
Exclusions: {request.exclusions}  
Target Use: {request.target_use}
Include Cost: {request.include_cost}

INSTRUCTIONS:
For each analogue, apply up to 3 scientific modifications that:
- Preserve or enhance function for {request.target_use}
- Avoid excluded residues/modifications  
- Result in biologically plausible peptides similar to GLP-1 therapeutics
- Are patent-differentiated from existing compounds

RETURN FORMAT (for each analogue):

### Analogue: [unique descriptive name]

**Sequence:**  
`[modified sequence with inline notation, e.g., D-Ser, [PEG3-C18]]`
**Modifications Applied:**  
- [modification 1 with position]
- [modification 2 with position]  
- [modification 3 with position]

---

**IP Risk Profile**  
- Patent Similarity Risk: [Low/Medium/High]
- Novelty Score: [0-100]%  
- Notes: [analysis of potential patent overlaps, uniqueness factors]

---

**Bioactivity Profile**  
- Binding Affinity: [ΔG value] kcal/mol  
- Predicted Half-Life: [days] days  
- Synthesis Complexity: [1-5] / 5  
{f"- Estimated Cost: $[amount] CAD/mg" if request.include_cost else ""}
- Notes: [DPP-4 resistance, albumin binding, synthetic challenges]

---

Generate all {request.num_analogues} analogues in this exact format."""
    
    # Get AI response
    chat = await get_llm_chat()
    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    # Parse AI response into structured analogues
    analogues = parse_analogue_response(response, clean_sequence, request.include_cost)
    
    return analogues

def parse_analogue_response(ai_response: str, base_molecule: str, include_cost: bool = False) -> List[PeptideAnalogue]:
    """Parse AI response into structured PeptideAnalogue objects with Vault-grade format"""
    analogues = []
    
    # Split response into individual analogues using the ### marker
    analogue_sections = re.split(r'### Analogue:', ai_response)
    
    for i, section in enumerate(analogue_sections):
        if i == 0 or not section.strip():  # Skip empty first section
            continue
            
        try:
            # Extract analogue name
            name_match = re.search(r'^([^\n]+)', section.strip())
            analogue_name = name_match.group(1).strip() if name_match else f"Analogue-{i}"
            
            # Extract sequence
            sequence_match = re.search(r'\*\*Sequence:\*\*\s*\n`([^`]+)`', section)
            modified_sequence = sequence_match.group(1).strip() if sequence_match else ""
            
            # Extract modifications
            mods_section = re.search(r'\*\*Modifications Applied:\*\*\s*\n((?:- .+\n?)+)', section)
            modifications = []
            if mods_section:
                mod_lines = mods_section.group(1).strip().split('\n')
                modifications = [line.strip('- ').strip() for line in mod_lines if line.strip().startswith('-')]
            
            # Extract IP Risk Profile
            ip_risk_match = re.search(r'- Patent Similarity Risk: ([^\n]+)', section)
            novelty_match = re.search(r'- Novelty Score: (\d+(?:\.\d+)?)%', section)
            ip_notes_match = re.search(r'IP Risk Profile.*?- Notes: ([^\n]+)', section, re.DOTALL)
            
            patent_risk = ip_risk_match.group(1).strip() if ip_risk_match else "Medium"
            novelty_score = float(novelty_match.group(1)) if novelty_match else 50.0
            ip_notes = ip_notes_match.group(1).strip() if ip_notes_match else "Patent analysis pending"
            
            # Extract Bioactivity Profile
            binding_match = re.search(r'- Binding Affinity: ([+-]?\d+(?:\.\d+)?) kcal/mol', section)
            half_life_match = re.search(r'- Predicted Half-Life: (\d+(?:\.\d+)?) days', section)
            complexity_match = re.search(r'- Synthesis Complexity: (\d+) / 5', section)
            cost_match = re.search(r'- Estimated Cost: \$(\d+(?:\.\d+)?) CAD/mg', section) if include_cost else None
            bioactivity_notes_match = re.search(r'Bioactivity Profile.*?- Notes: ([^\n]+)', section, re.DOTALL)
            
            binding_affinity = float(binding_match.group(1)) if binding_match else -8.5
            predicted_half_life = float(half_life_match.group(1)) if half_life_match else 2.1
            synthesis_complexity = int(complexity_match.group(1)) if complexity_match else 3
            synthesis_cost = float(cost_match.group(1)) if cost_match else None
            bioactivity_notes = bioactivity_notes_match.group(1).strip() if bioactivity_notes_match else "Standard GLP-1R profile expected"
            
            # Generate Vault ID
            vault_id = generate_vault_id(modified_sequence, modifications)
            
            # Create analogue with both new and legacy fields
            analogue = PeptideAnalogue(
                analogue_name=analogue_name,
                modified_sequence=modified_sequence,
                modifications_applied=modifications,
                modification_positions=modifications,  # Using same for now
                
                # New Vault-grade fields
                patent_similarity_risk=patent_risk,
                novelty_score=novelty_score,
                ip_notes=ip_notes,
                binding_affinity=binding_affinity,
                predicted_half_life=predicted_half_life,
                synthesis_complexity=synthesis_complexity,
                synthesis_cost=synthesis_cost,
                bioactivity_notes=bioactivity_notes,
                vault_id=vault_id,
                
                # Legacy compatibility fields
                ip_risk_score=max(0, min(10, 10 - (novelty_score / 10))),  # Convert novelty to legacy scale
                novelty_score_legacy=novelty_score / 10,  # Convert to 0-10 scale
                affinity_estimate=f"ΔG = {binding_affinity} kcal/mol",
                pk_estimate=f"t½ = {predicted_half_life} days"
            )
            analogues.append(analogue)
            
        except Exception as e:
            logging.warning(f"Failed to parse analogue section {i}: {e}")
            continue
    
    return analogues


# API Routes
@api_router.get("/")
async def root():
    return {"message": "Peptimancer - AI-Powered Peptide Architect", "version": "1.0.0"}

@api_router.post("/generate-analogues", response_model=PeptideGenerationResponse)
async def create_peptide_analogues(request: PeptideGenerationRequest):
    """Generate novel peptide analogues using AI-powered design"""
    try:
        # Generate analogues (validation happens inside this function)
        analogues = await generate_peptide_analogues(request)
        
        # Get clean sequence for response
        processor = PeptideProcessor()
        validation_result = processor.validate_sequence(request.base_molecule)
        clean_sequence = validation_result["clean_sequence"]
        
        # Create response using clean sequence
        response = PeptideGenerationResponse(
            base_molecule=clean_sequence,
            analogues=analogues
        )
        
        # Store in MongoDB for history and create vault ledger entries
        doc = response.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.peptide_generations.insert_one(doc)
        
        # Create vault ledger entries for each analogue
        for analogue in response.analogues:
            ledger_entry = VaultLedgerEntry(
                vault_id=analogue.vault_id,
                generation_id=response.request_id,
                base_molecule=response.base_molecule,
                analogue_data=analogue.model_dump()
            )
            
            ledger_doc = ledger_entry.model_dump()
            ledger_doc['timestamp'] = ledger_doc['timestamp'].isoformat()
            await db.vault_ledger.insert_one(ledger_doc)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error generating peptide analogues: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate analogues: {str(e)}")

@api_router.get("/generation-history")
async def get_generation_history(limit: int = 50):
    """Get history of peptide generation requests with enhanced serialization"""
    try:
        # Use aggregation pipeline for better control
        pipeline = [
            {"$sort": {"timestamp": -1}},
            {"$limit": limit},
            {"$project": {"_id": 0}}  # Explicitly exclude _id field
        ]
        
        history_entries = []
        async for record in db.peptide_generations.aggregate(pipeline):
            try:
                # Clean the record for JSON serialization
                clean_record = {}
                
                for key, value in record.items():
                    if key == "_id":  # Skip any _id that might slip through
                        continue
                    elif hasattr(value, 'isoformat'):  # datetime objects
                        clean_record[key] = value.isoformat()
                    elif isinstance(value, dict):
                        # Clean nested dictionaries
                        clean_dict = {}
                        for nested_key, nested_value in value.items():
                            if hasattr(nested_value, 'isoformat'):
                                clean_dict[nested_key] = nested_value.isoformat()
                            else:
                                clean_dict[nested_key] = nested_value
                        clean_record[key] = clean_dict
                    elif isinstance(value, list):
                        # Clean list items (analogues)
                        clean_list = []
                        for item in value:
                            if isinstance(item, dict):
                                clean_item = {}
                                for item_key, item_value in item.items():
                                    if hasattr(item_value, 'isoformat'):
                                        clean_item[item_key] = item_value.isoformat()
                                    else:
                                        clean_item[item_key] = item_value
                                clean_list.append(clean_item)
                            else:
                                clean_list.append(item)
                        clean_record[key] = clean_list
                    elif isinstance(value, str) and key == 'timestamp':
                        # Handle timestamp strings
                        try:
                            dt = datetime.fromisoformat(value)
                            clean_record[key] = dt.isoformat()
                        except:
                            clean_record[key] = value
                    else:
                        clean_record[key] = value
                
                history_entries.append(clean_record)
                
            except Exception as e:
                logging.warning(f"Skipping problematic history entry: {e}")
                continue
        
        return {
            "history": history_entries,
            "total_entries": len(history_entries),
            "status": "active"
        }
        
    except Exception as e:
        logging.error(f"Error fetching generation history: {e}")
        # Return empty but valid response instead of error
        return {
            "history": [],
            "total_entries": 0,
            "status": "error", 
            "error_message": str(e)
        }

@api_router.get("/validate-sequence/{sequence}")
async def validate_peptide_sequence(sequence: str):
    """Validate amino acid sequence format with enhanced error handling"""
    processor = PeptideProcessor()
    
    # Handle empty sequence case
    if not sequence or sequence.strip() == "":
        return {
            "sequence": "",
            "is_valid": False,
            "error": "Empty sequence provided",
            "length": 0,
            "composition": {}
        }
    
    validation_result = processor.validate_sequence(sequence)
    
    if validation_result["is_valid"]:
        return {
            "sequence": validation_result["clean_sequence"],
            "is_valid": True,
            "length": validation_result["length"],
            "composition": validation_result["composition"]
        }
    else:
        return {
            "sequence": sequence,
            "is_valid": False,
            "error": validation_result["error"],
            "error_code": validation_result["error_code"],
            "length": len(sequence.strip()) if sequence else 0,
            "composition": {}
        }

@api_router.get("/validate-sequence/")
async def validate_empty_sequence():
    """Handle empty sequence validation endpoint"""
    return {
        "sequence": "",
        "is_valid": False,
        "error": "No sequence provided for validation",
        "error_code": "NO_SEQUENCE",
        "length": 0,
        "composition": {}
    }

# Phase III: Vault Export System
@api_router.post("/export-report")
async def export_vault_report(export_request: ExportRequest):
    """Export Vault-grade report in PDF format"""
    try:
        # Validate request
        if not export_request.generation_id or not export_request.generation_id.strip():
            raise HTTPException(status_code=400, detail="Generation ID is required")
        
        # Retrieve generation from database
        generation_doc = await db.peptide_generations.find_one(
            {"request_id": export_request.generation_id.strip()}, {"_id": 0}
        )
        
        if not generation_doc:
            raise HTTPException(status_code=404, detail="Generation not found")
        
        # Convert back to response model
        if isinstance(generation_doc.get('timestamp'), str):
            generation_doc['timestamp'] = datetime.fromisoformat(generation_doc['timestamp'])
        
        generation_response = PeptideGenerationResponse(**generation_doc)
        
        # Generate PDF report
        pdf_generator = VaultPDFGenerator()
        pdf_path = pdf_generator.generate_report(
            generation_response, 
            include_cost=export_request.include_cost,
            watermark=export_request.watermark
        )
        
        # Update export count in vault ledger
        if generation_response.analogues:
            vault_ids = [analogue.vault_id for analogue in generation_response.analogues if analogue.vault_id]
            if vault_ids:
                await db.vault_ledger.update_many(
                    {"vault_id": {"$in": vault_ids}},
                    {"$inc": {"export_count": 1}}
                )
        
        return FileResponse(
            path=pdf_path,
            filename=f"peptimancer_vault_report_{export_request.generation_id[:8]}.pdf",
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# Phase III: Synthesis Partner Integration
@api_router.post("/request-synthesis")
async def request_synthesis_quote(synthesis_request: SynthesisRequest):
    """Send analogue to synthesis partner for quotation"""
    try:
        # Retrieve analogue from vault ledger
        ledger_entry = await db.vault_ledger.find_one(
            {"vault_id": synthesis_request.vault_id}, {"_id": 0}
        )
        
        if not ledger_entry:
            raise HTTPException(status_code=404, detail="Vault ID not found")
        
        # Prepare synthesis request data
        synthesis_data = {
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "vault_id": synthesis_request.vault_id,
            "partner_name": synthesis_request.partner_name,
            "analogue_data": ledger_entry["analogue_data"],
            "requirements": {
                "quantity_mg": synthesis_request.quantity_mg,
                "purity_requirement": synthesis_request.purity_requirement,
                "timeline_days": synthesis_request.timeline_days,
                "additional_notes": synthesis_request.additional_notes
            },
            "contact_email": synthesis_request.contact_email
        }
        
        # Store synthesis request
        await db.synthesis_requests.insert_one(synthesis_data)
        
        # Update vault ledger with synthesis request
        await db.vault_ledger.update_one(
            {"vault_id": synthesis_request.vault_id},
            {"$push": {"synthesis_requests": synthesis_data}}
        )
        
        # In a real implementation, this would send to partner webhook
        # For now, we'll simulate the webhook call
        webhook_response = {
            "status": "submitted",
            "partner_reference": f"SYN-{synthesis_data['request_id'][:8]}",
            "estimated_quote_time": "2-3 business days",
            "message": f"Synthesis request submitted to {synthesis_request.partner_name}"
        }
        
        return {
            "synthesis_request_id": synthesis_data["request_id"],
            "vault_id": synthesis_request.vault_id,
            "partner_response": webhook_response,
            "status": "submitted"
        }
        
    except Exception as e:
        logging.error(f"Synthesis request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Synthesis request failed: {str(e)}")

# Phase III: Pro Vault Tier - Token Management
@api_router.post("/vault-tokens/create")
async def create_vault_token(user_id: str, tier: str = "pro", credits: int = 100):
    """Create Pro Vault access token"""
    try:
        if not user_id or not user_id.strip():
            raise HTTPException(status_code=400, detail="User ID is required")
        
        token = ProVaultToken(
            user_id=user_id.strip(),
            tier=tier,
            credits=credits,
            expires_at=datetime.now(timezone.utc).replace(year=datetime.now().year + 1)
        )
        
        token_doc = token.model_dump()
        token_doc['created_at'] = token_doc['created_at'].isoformat()
        if token_doc['expires_at']:
            token_doc['expires_at'] = token_doc['expires_at'].isoformat()
        
        await db.vault_tokens.insert_one(token_doc)
        
        return {
            "token_id": token.token_id,
            "tier": token.tier,
            "credits": token.credits,
            "status": "active"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Token creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Token creation failed: {str(e)}")

@api_router.get("/vault-tokens/{token_id}")
async def get_vault_token_status(token_id: str):
    """Check Pro Vault token status and credits"""
    try:
        if not token_id or not token_id.strip():
            raise HTTPException(status_code=400, detail="Token ID is required")
        
        token_doc = await db.vault_tokens.find_one({"token_id": token_id.strip()}, {"_id": 0})
        
        if not token_doc:
            raise HTTPException(status_code=404, detail="Token not found")
        
        return {
            "token_id": token_id,
            "tier": token_doc["tier"],
            "credits": token_doc["credits"],
            "expires_at": token_doc["expires_at"],
            "status": "active" if token_doc["credits"] > 0 else "depleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Token check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Token check failed: {str(e)}")

# Phase III: Vault Ledger / IP Registry
@api_router.get("/vault-ledger")
async def get_vault_ledger(limit: int = 50):
    """Get vault ledger entries for IP tracking with enhanced error handling"""
    try:
        # Use aggregation pipeline to ensure proper data serialization
        pipeline = [
            {"$sort": {"timestamp": -1}},
            {"$limit": limit},
            {"$project": {"_id": 0}}  # Explicitly exclude _id field
        ]
        
        ledger_entries = []
        async for entry in db.vault_ledger.aggregate(pipeline):
            try:
                # Clean up the entry for JSON serialization
                clean_entry = {}
                
                for key, value in entry.items():
                    if key == "_id":  # Skip any _id that might slip through
                        continue
                    elif hasattr(value, 'isoformat'):  # datetime objects
                        clean_entry[key] = value.isoformat()
                    elif isinstance(value, dict):
                        # Recursively clean nested dictionaries
                        clean_dict = {}
                        for nested_key, nested_value in value.items():
                            if hasattr(nested_value, 'isoformat'):
                                clean_dict[nested_key] = nested_value.isoformat()
                            else:
                                clean_dict[nested_key] = nested_value
                        clean_entry[key] = clean_dict
                    elif isinstance(value, list):
                        # Clean list items
                        clean_list = []
                        for item in value:
                            if hasattr(item, 'isoformat'):
                                clean_list.append(item.isoformat())
                            elif isinstance(item, dict):
                                clean_item = {k: v.isoformat() if hasattr(v, 'isoformat') else v for k, v in item.items()}
                                clean_list.append(clean_item)
                            else:
                                clean_list.append(item)
                        clean_entry[key] = clean_list
                    else:
                        clean_entry[key] = value
                
                ledger_entries.append(clean_entry)
                
            except Exception as e:
                logging.warning(f"Skipping problematic ledger entry: {e}")
                continue
        
        return {
            "ledger_entries": ledger_entries,
            "total_entries": len(ledger_entries),
            "registry_status": "active"
        }
        
    except Exception as e:
        logging.error(f"Vault ledger retrieval failed: {e}")
        # Return empty but valid response instead of error
        return {
            "ledger_entries": [],
            "total_entries": 0,
            "registry_status": "error",
            "error_message": str(e)
        }

@api_router.get("/vault-ledger/{vault_id}")
async def get_vault_entry(vault_id: str):
    """Get specific vault entry for IP audit trail"""
    try:
        entry = await db.vault_ledger.find_one({"vault_id": vault_id}, {"_id": 0})
        
        if not entry:
            raise HTTPException(status_code=404, detail="Vault entry not found")
        
        # Convert timestamp if needed
        if isinstance(entry.get('timestamp'), str):
            entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
        
        return entry
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Vault entry retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Vault entry retrieval failed: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

# Include admin routes
app.include_router(admin_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()