# 🏥 Peptimancer CRO Integration Guide

## Overview

This guide enables Contract Research Organizations (CROs) to integrate with Peptimancer's synthesis quotation system, providing automated workflows for peptide synthesis requests and quote management.

---

## 🔧 Integration Architecture

### Workflow Overview
1. **Research Institution** generates peptide analogues via Peptimancer
2. **Synthesis Request** submitted with Vault ID and requirements  
3. **CRO Partner** receives webhook notification with analogue data
4. **Quote Generation** processed by CRO internal systems
5. **Status Updates** sent back to Peptimancer via callbacks
6. **Client Notification** delivered to requesting research team

### Data Flow
```
Peptimancer → CRO Webhook → CRO Systems → Quote Response → Peptimancer → Client
```

---

## 📡 Webhook Integration

### Endpoint Registration
CRO partners must provide a secure HTTPS endpoint for receiving synthesis requests.

**Required Endpoint Format:**
```
https://your-cro-domain.com/api/peptimancer/synthesis-request
```

### Authentication
All webhook calls include signature verification for security.

**Headers:**
```
X-Peptimancer-Signature: sha256=signature_hash
X-Peptimancer-Timestamp: unix_timestamp
Content-Type: application/json
```

### Webhook Payload
```json
{
  "request_id": "uuid-string",
  "vault_id": "PMNC-E36E32A",
  "timestamp": "2025-11-06T17:38:58.440062+00:00",
  "client_info": {
    "organization": "University Research Institute",
    "contact_email": "research@institution.edu",
    "contact_name": "Dr. Jane Smith"
  },
  "analogue_data": {
    "analogue_name": "CycloStable-Pro-7",
    "modified_sequence": "HAE[D-Gly]GTFTSDVSSYLE[C18-K]GQAAKEFIAWLVKGR",
    "modifications_applied": [
      "D-isomerization at position 4 (Glycine)",
      "C18 Lipidation at position 17 (Lysine)", 
      "Cyclization between positions 4 and 17"
    ],
    "synthesis_complexity": 4,
    "estimated_cost": 405.0,
    "molecular_weight": 3247.8,
    "special_requirements": [
      "Requires D-amino acid synthesis capability",
      "Lipidation chemistry required",
      "Cyclization step needed"
    ]
  },
  "synthesis_requirements": {
    "quantity_mg": 500.0,
    "purity_requirement": 95.0,
    "timeline_days": 21,
    "additional_notes": "Rush order for clinical trials",
    "delivery_location": "Boston, MA, USA"
  }
}
```

---

## 📤 Response Format

### Initial Acknowledgment
CRO must respond within 30 seconds to confirm receipt.

**Response (HTTP 200):**
```json
{
  "status": "received",
  "cro_reference": "SYN-CRO-001234",
  "estimated_quote_time": "2-3 business days",
  "account_manager": "john.doe@cro-partner.com"
}
```

### Quote Submission
Submit detailed quotes via Peptimancer callback endpoint.

**Callback Endpoint:** `POST https://api.peptimancer.com/api/cro-callback`

**Quote Payload:**
```json
{
  "peptimancer_request_id": "uuid-from-original-request",
  "cro_reference": "SYN-CRO-001234",
  "status": "quote_ready",
  "quote": {
    "base_price": 2450.00,
    "currency": "USD",
    "quantity_mg": 500.0,
    "purity_guaranteed": 97.5,
    "timeline_days": 18,
    "express_timeline_days": 12,
    "express_surcharge": 500.00,
    "valid_until": "2025-12-06T17:38:58.440062+00:00"
  },
  "synthesis_notes": {
    "technical_notes": "Complex cyclization requires specialized conditions",
    "delivery_method": "Overnight shipping included",
    "quality_control": "HPLC and MS analysis provided",
    "storage_conditions": "-20°C storage recommended"
  },
  "contact_info": {
    "project_manager": "john.doe@cro-partner.com",
    "phone": "+1-555-123-4567",
    "alternative_contact": "support@cro-partner.com"
  }
}
```

---

## 📊 Status Updates

### Status Lifecycle
1. `received` - Initial acknowledgment
2. `under_review` - Technical feasibility assessment
3. `quote_ready` - Quote prepared and submitted
4. `quote_accepted` - Client approved synthesis
5. `in_synthesis` - Synthesis in progress
6. `qc_testing` - Quality control phase
7. `completed` - Ready for shipment
8. `shipped` - Package dispatched
9. `delivered` - Confirmed delivery

### Status Update Format
```json
{
  "peptimancer_request_id": "uuid-string",
  "cro_reference": "SYN-CRO-001234", 
  "status": "in_synthesis",
  "progress_notes": "Synthesis 60% complete, on schedule",
  "estimated_completion": "2025-11-20T17:38:58.440062+00:00",
  "quality_metrics": {
    "current_purity": 96.2,
    "yield_percentage": 78.5
  }
}
```

---

## 🔐 Security & Authentication

### Signature Verification
Verify webhook authenticity using HMAC-SHA256.

**Python Example:**
```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    computed_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    expected_signature = f"sha256={computed_signature}"
    return hmac.compare_digest(expected_signature, signature)
```

### IP Whitelisting
Configure firewalls to allow Peptimancer webhook origins:
- `52.91.43.120` (Primary)
- `34.203.255.89` (Secondary)
- `54.164.12.201` (Backup)

---

## 🧪 Testing & Validation

### Test Webhook
Use test endpoint for integration validation.

**Test Endpoint:** `https://api.peptimancer.com/api/cro-test-webhook`

**Test Payload:**
```json
{
  "test": true,
  "request_id": "test-123",
  "vault_id": "PMNC-TEST01",
  "analogue_data": {
    "analogue_name": "Test-Peptide-1",
    "modified_sequence": "TESTSEQUENCE",
    "synthesis_complexity": 2
  },
  "synthesis_requirements": {
    "quantity_mg": 100.0,
    "purity_requirement": 95.0,
    "timeline_days": 14
  }
}
```

### Integration Checklist
- [ ] Webhook endpoint configured and accessible
- [ ] Authentication/signature verification implemented
- [ ] Initial acknowledgment response (<30s)
- [ ] Quote submission callback working
- [ ] Status update callbacks functional
- [ ] Error handling and retry logic
- [ ] Test webhook validation complete

---

## 📈 Performance Requirements

### Response Time SLAs
- **Initial Acknowledgment**: <30 seconds
- **Quote Generation**: <72 hours (standard), <24 hours (express)
- **Status Updates**: Real-time (within 1 hour of changes)
- **Technical Support**: <4 hours response time

### Volume Expectations
- **Request Volume**: 50-200 synthesis requests/month per CRO
- **Peak Processing**: Up to 20 concurrent requests
- **Quote Validity**: Minimum 30 days recommended
- **Data Retention**: 2 years for audit compliance

---

## 🚨 Error Handling

### Common Error Scenarios
1. **Webhook Timeout**: Retry after 5 minutes
2. **Invalid Signature**: Check secret key configuration
3. **Malformed Payload**: Validate JSON structure
4. **Quote Rejection**: Provide alternative options

### Error Response Format
```json
{
  "error": true,
  "error_code": "SYNTHESIS_NOT_FEASIBLE",
  "message": "Peptide requires specialized equipment not available",
  "alternative_suggestions": [
    "Consider simpler modification pattern",
    "Alternative CRO partner recommendation available"
  ],
  "contact_for_discussion": "technical-support@cro-partner.com"
}
```

---

## 📋 Data Specifications

### Peptide Sequence Format
- **Standard**: Single-letter amino acid codes (A, C, D, E, F, G, H, I, K, L, M, N, P, Q, R, S, T, V, W, Y)
- **Modifications**: Inline notation [D-Ala], [C16], [PEG3]
- **Cyclization**: Indicated in modifications_applied array
- **Special Residues**: Non-natural amino acids clearly specified

### Purity Standards
- **Crude**: 60-75% purity
- **Standard**: 85-95% purity  
- **High Purity**: 95-98% purity
- **Research Grade**: >98% purity
- **GMP**: Pharmaceutical manufacturing standards

---

## 📞 CRO Partner Support

### Technical Integration
**Email**: cro-integration@peptimancer.ai  
**Phone**: +1-555-PEPTIDE (735-8433)  
**Hours**: Monday-Friday, 9 AM - 6 PM EST

### Business Development
**Email**: partnerships@peptimancer.ai  
**Contact**: Sarah Johnson, VP Partnerships  
**Direct**: +1-555-123-7890

### Documentation & Resources
**Developer Portal**: https://dev.peptimancer.ai/cro  
**API Status**: https://status.peptimancer.ai  
**Integration Examples**: https://github.com/peptimancer/cro-examples

---

## 📜 Legal & Compliance

### Data Handling
- **GDPR Compliance**: EU data protection standards
- **HIPAA Awareness**: Healthcare information protection
- **Export Controls**: International peptide research regulations
- **IP Protection**: Confidentiality of proprietary sequences

### Service Level Agreements
- **Availability**: 99.9% uptime guarantee
- **Data Security**: SOC 2 Type II compliance
- **Backup & Recovery**: 24-hour maximum data recovery
- **Audit Support**: Complete request/response logging

---

*CRO Integration Guide current as of Phase VI Production Release*