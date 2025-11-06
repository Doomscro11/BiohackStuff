from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import asyncio
import re
from emergentintegrations.llm.chat import LlmChat, UserMessage


import hashlib

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

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
    
    # Prepare AI prompt using clean sequence
    prompt = f"""Design {request.num_analogues} novel peptide analogues based on:

Base Molecule: {clean_sequence}
Allowed Modifications: {request.allowed_mods}
Exclusion Clauses: {request.exclusions}  
Target Use: {request.target_use}

Available modification options: {len(modifications)} possibilities including substitutions, D-isomers, lipidation, and cyclization.

For each analogue, apply up to 3 modifications that:
- Preserve or enhance function for {request.target_use}
- Avoid excluded residues/modifications  
- Result in biologically plausible and patent-differentiated peptides

Return EXACTLY this format for each analogue:

**Analogue Name**: [unique short name]
**Modified Sequence**: [1-letter amino acid chain with modifications noted inline]
**Modifications Applied**:
- [Brief description of change #1]
- [Brief description of change #2]  
- [Brief description of change #3]
**Modification Positions**: [e.g., Position 8: Aib → D-Ser, Position 26: Lys lipidated, etc.]
**IP Risk Score**: [0-10]
**Novelty Score**: [0-10]
**Affinity Estimate**: [High/Medium/Low maintained/enhanced]
**PK Estimate**: [Improved/Similar/Reduced half-life, stability]

---"""
    
    # Get AI response
    chat = await get_llm_chat()
    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    # Parse AI response into structured analogues
    analogues = parse_analogue_response(response, request.base_molecule)
    
    return analogues

def parse_analogue_response(ai_response: str, base_molecule: str) -> List[PeptideAnalogue]:
    """Parse AI response into structured PeptideAnalogue objects"""
    analogues = []
    
    # Split response into individual analogues
    analogue_sections = re.split(r'---+', ai_response)
    
    for section in analogue_sections:
        if '**Analogue Name**:' not in section:
            continue
            
        try:
            # Extract fields using regex
            name_match = re.search(r'\*\*Analogue Name\*\*:\s*(.+)', section)
            sequence_match = re.search(r'\*\*Modified Sequence\*\*:\s*(.+)', section)
            mods_match = re.findall(r'- (.+)', section)
            positions_match = re.search(r'\*\*Modification Positions\*\*:\s*(.+)', section)
            ip_match = re.search(r'\*\*IP Risk Score\*\*:\s*(\d+(?:\.\d+)?)', section)
            novelty_match = re.search(r'\*\*Novelty Score\*\*:\s*(\d+(?:\.\d+)?)', section)
            affinity_match = re.search(r'\*\*Affinity Estimate\*\*:\s*(.+)', section)
            pk_match = re.search(r'\*\*PK Estimate\*\*:\s*(.+)', section)
            
            if name_match and sequence_match:
                analogue = PeptideAnalogue(
                    analogue_name=name_match.group(1).strip(),
                    modified_sequence=sequence_match.group(1).strip(),
                    modifications_applied=mods_match[:3],  # Max 3 modifications
                    modification_positions=[positions_match.group(1).strip()] if positions_match else [],
                    ip_risk_score=float(ip_match.group(1)) if ip_match else 5.0,
                    novelty_score=float(novelty_match.group(1)) if novelty_match else 5.0,
                    affinity_estimate=affinity_match.group(1).strip() if affinity_match else "Medium maintained",
                    pk_estimate=pk_match.group(1).strip() if pk_match else "Similar stability"
                )
                analogues.append(analogue)
                
        except Exception as e:
            logging.warning(f"Failed to parse analogue section: {e}")
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
        
        # Store in MongoDB for history
        doc = response.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.peptide_generations.insert_one(doc)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error generating peptide analogues: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate analogues: {str(e)}")

@api_router.get("/generation-history", response_model=List[PeptideGenerationResponse])
async def get_generation_history():
    """Get history of peptide generation requests"""
    try:
        history = await db.peptide_generations.find({}, {"_id": 0}).sort("timestamp", -1).limit(50).to_list(50)
        
        # Convert ISO string timestamps back to datetime objects
        for record in history:
            if isinstance(record['timestamp'], str):
                record['timestamp'] = datetime.fromisoformat(record['timestamp'])
        
        return history
    except Exception as e:
        logging.error(f"Error fetching generation history: {e}")
        return []

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

# Include the router in the main app
app.include_router(api_router)

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