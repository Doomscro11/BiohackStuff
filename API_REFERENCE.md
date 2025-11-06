# 📊 Peptimancer Enterprise API Reference

## Authentication

All enterprise API endpoints require proper authentication tokens. Contact your administrator for Pro Vault tier access.

```bash
# Include token in headers for enterprise endpoints
curl -H "Authorization: Bearer YOUR_VAULT_TOKEN" \
     -H "Content-Type: application/json" \
     https://api.peptimancer.com/api/endpoint
```

---

## Core APIs

### 🧬 Peptide Generation

#### Generate Analogues
Generate novel peptide analogues with advanced chemistry and IP analysis.

**Endpoint:** `POST /api/generate-analogues`

**Request:**
```json
{
  "base_molecule": "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR",
  "allowed_mods": "Substitution, Lipidation, Cyclization, D-isomers",
  "exclusions": "No Aib or γ-Glu residues", 
  "target_use": "GLP-1 receptor agonist for diabetes treatment",
  "num_analogues": 3,
  "include_cost": true
}
```

**Response:**
```json
{
  "request_id": "uuid-string",
  "timestamp": "2025-11-06T17:38:58.440062+00:00",
  "base_molecule": "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR",
  "analogues": [
    {
      "analogue_name": "CycloStable-Pro-7",
      "modified_sequence": "HAE[D-Gly]GTFTSDVSSYLE[C18-K]GQAAKEFIAWLVKGR",
      "modifications_applied": [
        "D-isomerization at position 4 (Glycine)",
        "C18 Lipidation at position 17 (Lysine)",
        "Cyclization between positions 4 and 17"
      ],
      "modification_positions": [
        "Position 4: Gly → D-Gly",
        "Position 17: Lys lipidated with C18"
      ],
      "patent_similarity_risk": "Medium",
      "novelty_score": 75.0,
      "ip_notes": "Unique combination of D-isomer and lipidation reduces patent overlap",
      "binding_affinity": -9.1,
      "predicted_half_life": 6.5,
      "synthesis_complexity": 4,
      "synthesis_cost": 405.0,
      "bioactivity_notes": "Enhanced albumin binding and DPP-4 resistance",
      "vault_id": "PMNC-E36E32A"
    }
  ]
}
```

#### Validate Sequence
Validate amino acid sequences before generation.

**Endpoint:** `GET /api/validate-sequence/{sequence}`

**Response:**
```json
{
  "sequence": "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR",
  "is_valid": true,
  "length": 30,
  "composition": {
    "H": 1, "A": 4, "E": 4, "G": 4, "T": 2, "F": 2,
    "S": 2, "D": 1, "V": 2, "Y": 1, "L": 3, "Q": 1, "K": 3, "I": 1, "W": 1, "R": 1
  }
}
```

---

## 📄 Export & Documentation

#### Export Vault Report
Generate professional PDF reports for research submissions.

**Endpoint:** `POST /api/export-report`

**Request:**
```json
{
  "generation_id": "uuid-from-generation-response",
  "format": "pdf",
  "include_cost": true,
  "include_ip_analysis": true,
  "watermark": true
}
```

**Response:** PDF file download with proper content-type headers.

---

## 🔗 CRO Integration

#### Request Synthesis Quote
Submit synthesis requests to CRO partners.

**Endpoint:** `POST /api/request-synthesis`

**Request:**
```json
{
  "vault_id": "PMNC-E36E32A",
  "partner_name": "Synthesis Partners Inc",
  "quantity_mg": 500.0,
  "purity_requirement": 95.0,
  "timeline_days": 21,
  "contact_email": "research@institution.edu",
  "additional_notes": "Rush order for clinical trials"
}
```

**Response:**
```json
{
  "synthesis_request_id": "uuid-string",
  "vault_id": "PMNC-E36E32A", 
  "partner_response": {
    "status": "submitted",
    "partner_reference": "SYN-12EFB1A2",
    "estimated_quote_time": "2-3 business days",
    "message": "Synthesis request submitted to Synthesis Partners Inc"
  },
  "status": "submitted"
}
```

---

## 🔐 Vault Management

#### Create Vault Token
Create enterprise access tokens for team members.

**Endpoint:** `POST /api/vault-tokens/create`

**Parameters:**
- `user_id`: Unique identifier for user
- `tier`: Access tier (basic, pro, enterprise) 
- `credits`: Initial credit allocation

**Response:**
```json
{
  "token_id": "uuid-string",
  "tier": "pro",
  "credits": 1000,
  "status": "active"
}
```

#### Check Token Status
Monitor credit usage and token status.

**Endpoint:** `GET /api/vault-tokens/{token_id}`

**Response:**
```json
{
  "token_id": "uuid-string",
  "tier": "pro", 
  "credits": 750,
  "expires_at": "2026-11-06T17:38:58.440062+00:00",
  "status": "active"
}
```

---

## 📊 Audit & Registry

#### Vault Ledger
Access complete IP registry and audit trails.

**Endpoint:** `GET /api/vault-ledger?limit=50`

**Response:**
```json
{
  "ledger_entries": [
    {
      "vault_id": "PMNC-E36E32A",
      "generation_id": "uuid-string",
      "timestamp": "2025-11-06T17:38:58.440062+00:00",
      "base_molecule": "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR",
      "analogue_data": {
        "analogue_name": "CycloStable-Pro-7",
        "patent_similarity_risk": "Medium",
        "novelty_score": 75.0
      },
      "export_count": 3,
      "synthesis_requests": []
    }
  ],
  "total_entries": 1,
  "registry_status": "active"
}
```

#### Generation History
Retrieve historical generation data for compliance.

**Endpoint:** `GET /api/generation-history?limit=50`

**Response:**
```json
{
  "history": [
    {
      "request_id": "uuid-string",
      "timestamp": "2025-11-06T17:38:58.440062+00:00", 
      "base_molecule": "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR",
      "analogues": []
    }
  ],
  "total_entries": 1,
  "status": "active"
}
```

---

## 🚨 Error Handling

### HTTP Status Codes
- `200 OK`: Request successful
- `400 Bad Request`: Invalid input parameters
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error, contact support

### Error Response Format
```json
{
  "detail": "Invalid amino acid sequence: Invalid characters found",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2025-11-06T17:38:58.440062+00:00"
}
```

---

## 📈 Rate Limits & Performance

### Enterprise Rate Limits
- **Generation API**: 100 requests/hour per token
- **Export API**: 50 requests/hour per token  
- **Vault APIs**: 500 requests/hour per token
- **Validation API**: Unlimited

### Performance Guidelines
- **Generation Time**: 15-30 seconds for 3 analogues
- **Export Time**: 2-5 seconds for PDF generation
- **API Response**: <2 seconds for most endpoints

### Optimization Tips
- **Batch Processing**: Submit larger num_analogues for efficiency
- **Caching**: Reuse validation results within sessions
- **Concurrent Requests**: Limit to 5 simultaneous generations

---

## 🔄 Webhooks (Enterprise Only)

### Synthesis Status Updates
CRO partners can send status updates to your webhook endpoints.

**Webhook Format:**
```json
{
  "synthesis_request_id": "uuid-string",
  "vault_id": "PMNC-E36E32A",
  "status": "quote_ready",
  "partner_reference": "SYN-12EFB1A2",
  "quote": {
    "price": 1250.00,
    "currency": "USD",
    "timeline_days": 14,
    "purity_achieved": 97.5
  },
  "timestamp": "2025-11-06T17:38:58.440062+00:00"
}
```

---

## 📞 Support

**API Documentation**: https://docs.peptimancer.ai  
**Technical Support**: api-support@peptimancer.ai  
**Enterprise Sales**: enterprise@peptimancer.ai  

---

*API Reference current as of Phase VI Production Release*