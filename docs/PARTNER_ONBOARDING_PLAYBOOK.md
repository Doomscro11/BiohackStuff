# Partner Onboarding Playbook

## Overview

This playbook guides administrators through the complete process of onboarding a new partner to PatentPulse's Reclaim Pack preview program using the Partner Portal.

## Prerequisites

- [ ] Admin account with 2FA enabled
- [ ] At least one Reclaim Pack generated (PDF or JSON)
- [ ] Partner contact information (email, name, company)
- [ ] Feature flag enabled: `FEATURE_PATENTPULSE_PARTNER=true`

## Onboarding Flow

### Phase 1: Pre-Onboarding (Before Share Creation)

#### Step 1: Partner Qualification

**Action Items:**
- [ ] Verify partner is a legitimate pharma/biotech company
- [ ] Confirm partner's interest in peptide opportunities
- [ ] Collect required information:
  - Primary contact email
  - Primary contact first name
  - Company or project name
  - Intended use case (licensing, development, research)
  - Any IP restrictions or requirements

**Checklist:**
- [ ] Partner signed NDA (if required)
- [ ] Partner acknowledged data is for evaluation only
- [ ] Partner agreed to terms (no redistribution, watermarking, etc.)

#### Step 2: Generate Reclaim Pack

**Action:**
1. Navigate to PatentPulse Admin > Reclaim Packs
2. Click "Generate Reclaim Pack"
3. Configure pack settings:
   - Top N patents (e.g., 25)
   - Include sections: commercial score, synthesis, claims, family
   - Format: PDF (recommended) or JSON
4. Click "Generate"
5. Wait for generation to complete
6. Note the `file_id` for next steps

**Verification:**
- [ ] Reclaim Pack generated successfully
- [ ] File available in exports list
- [ ] File preview looks correct (no formatting issues)

### Phase 2: Share Creation

#### Step 3: Create Partner Share

**Action:**
1. Navigate to Admin > Partner Shares
2. Click "Create Share" button
3. Fill out share creation form:

**Form Fields:**

| Field | Value | Notes |
|-------|-------|-------|
| Export File | Select from dropdown | Use Reclaim Pack from Step 2 |
| Recipient Email | partner@company.com | Primary contact email |
| Recipient First Name | John | Used in landing page greeting |
| Company / Project | ACME Pharma R&D | Displayed on share page |
| Expires In (days) | 14 | Default: 14 days |
| Max Downloads | 10 | Default: 10 downloads |
| IP Allowlist | (optional) | Comma-separated IPs or CIDR |
| Enable Watermarking | ✓ Checked | Highly recommended |
| Internal Notes | "Q4 2024 partner outreach" | For your tracking |

4. Click "Create Share"
5. **Copy the generated share URL immediately**

**Share URL Format:**
```
https://peptimancer.com/share/{token}
```

Where `{token}` is the signed, base64-encoded share token.

**Verification:**
- [ ] Share created successfully
- [ ] Share URL copied to clipboard
- [ ] Share appears in shares list with "active" state

### Phase 3: Partner Communication

#### Step 4: Send Onboarding Email

**Action:**

Use the email template: `backend/emails/partner_onboarding_invite.md`

**Customize:**
- Replace `{{recipient_first_name}}` with partner's first name
- Replace `{{max_downloads}}` with configured value (e.g., 10)
- Replace `{{days_valid}}` with configured expiry (e.g., 14)
- Replace `{{support_email}}` with your support email

**Email Subject:**
```
Welcome to PatentPulse Partner Preview
```

**Email Body:**
(See template for full content)

**Key Points to Emphasize:**
- Preview is confidential and watermarked
- Access is time-limited and non-transferable
- Data is for internal evaluation only
- Not legal advice or FTO clearance
- Support contact for questions

**Verification:**
- [ ] Email sent to partner
- [ ] Email includes clear expectations
- [ ] Support email provided

#### Step 5: Send Access Granted Email

**Action:**

Use the email template: `backend/emails/partner_access_granted.md`

**Customize:**
- Replace `{{recipient_first_name}}` with partner's first name
- Replace `{{secure_share_url}}` with the share URL from Step 3
- Replace `{{expiry_date}}` with calculated expiry date
- Replace `{{max_downloads}}` with configured value
- Replace `{{days_valid}}` with configured expiry
- Replace `{{support_email}}` with your support email

**Email Subject:**
```
Your PatentPulse Reclaim Pack is Ready
```

**Email Body:**
(See template for full content)

**Security Note:**
- Consider sending this email separately (not in same thread as onboarding)
- Use encrypted email if possible
- Remind partner to keep link confidential

**Verification:**
- [ ] Access email sent
- [ ] Share URL included and correct
- [ ] Expiry date and download limits clearly stated

### Phase 4: Partner Access & Monitoring

#### Step 6: Monitor Partner Access

**Action:**
1. Navigate to Admin > Partner Shares
2. Find partner's share in list
3. Click analytics button (📊) to view metrics

**Metrics to Monitor:**
- **Opens:** Number of times share page was viewed
- **Downloads:** Number of times file was downloaded
- **Blocked:** Number of blocked access attempts (expired, IP, rate limit)
- **Last Access:** Timestamp of last activity
- **Top IPs:** Most active IP addresses
- **Geo Breakdown:** Countries accessing the share

**Red Flags:**
- ⚠️ Multiple IPs from different countries (potential sharing)
- ⚠️ High blocked count (potential security issue)
- ⚠️ Rapid downloads (potential scraping)
- ⚠️ No access after 7 days (partner may need reminder)

**Actions:**
- If suspicious activity: Contact partner, consider revocation
- If no activity after 7 days: Send reminder email
- If normal activity: No action needed

**Verification:**
- [ ] Analytics reviewed
- [ ] No suspicious activity detected
- [ ] Partner engagement tracked

#### Step 7: Send Expiry Reminder (3 Days Before)

**Action:**

Use the email template: `backend/emails/partner_access_reminder.md`

**Trigger:**
- Automated: Cleanup job sends reminders 3 days before expiry
- Manual: Send if partner hasn't downloaded yet

**Customize:**
- Replace `{{recipient_first_name}}` with partner's first name
- Replace `{{days_remaining}}` with calculated days (e.g., 3)
- Replace `{{expiry_date}}` with expiry date
- Replace `{{secure_share_url}}` with share URL
- Replace `{{max_downloads}}` with remaining downloads
- Replace `{{support_email}}` with your support email

**Email Subject:**
```
Reminder: Your PatentPulse Reclaim Pack Expires Soon
```

**Verification:**
- [ ] Reminder sent 3 days before expiry
- [ ] Partner has opportunity to download before expiry

### Phase 5: Post-Access Follow-Up

#### Step 8: Collect Partner Feedback

**Action:**

After partner has accessed the Reclaim Pack (or after expiry), reach out for feedback.

**Questions to Ask:**

1. **Content Quality:**
   - Was the Reclaim Pack useful for your evaluation?
   - Did the commercial scores align with your assessment?
   - Were the patent details sufficient for initial due diligence?

2. **User Experience:**
   - Was the share link easy to access?
   - Did the landing page provide clear information?
   - Were the watermarking and limits acceptable?

3. **Next Steps:**
   - Are you interested in pursuing any of the opportunities?
   - Would you like access to additional Reclaim Packs?
   - Do you need deeper analysis on specific patents?

4. **Improvements:**
   - What additional data would be helpful?
   - How can we improve the preview experience?
   - Any technical issues or suggestions?

**Verification:**
- [ ] Feedback email sent
- [ ] Partner responses documented
- [ ] Insights captured for product improvement

#### Step 9: Determine Next Steps

**Based on Feedback:**

**If Partner is Interested:**
- [ ] Schedule follow-up call
- [ ] Provide access to additional Reclaim Packs
- [ ] Discuss licensing or partnership opportunities
- [ ] Create new share with extended access (if needed)

**If Partner is Not Interested:**
- [ ] Thank partner for their time
- [ ] Keep partner on mailing list for future opportunities
- [ ] Document reasons for no interest

**If Partner Needs More Information:**
- [ ] Provide deeper analysis on specific patents
- [ ] Connect with IP counsel (if available)
- [ ] Extend share expiry if needed

**Verification:**
- [ ] Next steps documented
- [ ] Partner relationship status updated
- [ ] Follow-up tasks scheduled

### Phase 6: Share Management

#### Step 10: Handle Special Scenarios

**Scenario A: Partner Needs More Time**

**Action:**
1. Navigate to Admin > Partner Shares
2. Find partner's share
3. Click rotate button (🔄)
4. New token generated with fresh expiry
5. Send new URL to partner
6. Old token immediately invalidated

**Scenario B: Accidental Share or Security Concern**

**Action:**
1. Navigate to Admin > Partner Shares
2. Find share to revoke
3. Click revoke button (🚫)
4. Enter revocation reason (e.g., "Security concern")
5. Confirm revocation
6. Share immediately revoked
7. Send revocation email to partner (optional)

**Scenario C: Partner Lost Access Link**

**Action:**
1. Navigate to Admin > Partner Shares
2. Find partner's share
3. If still active: Click copy button (📋) to get URL
4. If expired: Create new share with same details
5. Send URL to partner via secure channel

**Scenario D: Download Limit Reached Prematurely**

**Action:**
1. Contact partner to verify legitimate use
2. If legitimate: Create new share with higher limit
3. If suspicious: Investigate via analytics, consider revocation

**Verification:**
- [ ] Special scenarios handled promptly
- [ ] Partner communication maintained
- [ ] Security maintained throughout

## Best Practices

### Security

1. **Always Enable Watermarking:** Don't disable unless absolutely necessary
2. **Use IP Allowlist:** If partner's IP range is known, restrict access
3. **Monitor Analytics:** Check for suspicious patterns weekly
4. **Rotate Tokens:** If share is long-lived, rotate every 30 days
5. **Revoke Promptly:** Don't delay revocation if security concern arises

### Communication

1. **Set Clear Expectations:** Be explicit about limits, watermarking, and expiry
2. **Provide Support:** Make it easy for partners to reach you
3. **Send Reminders:** Don't let partners miss their expiry without warning
4. **Collect Feedback:** Learn from each partner engagement
5. **Document Everything:** Keep notes on all partner interactions

### Operational

1. **Generate Fresh Packs:** Don't share old Reclaim Packs (data may be stale)
2. **Test Before Sharing:** Preview the Reclaim Pack yourself first
3. **Use Internal Notes:** Track context for each share (campaign, referral, etc.)
4. **Review Analytics:** Check metrics at least weekly
5. **Clean Up Expired Shares:** Let cleanup job handle old shares automatically

## Troubleshooting

### Partner Can't Access Share

**Diagnosis:**
1. Check share state (active/expired/revoked)
2. Check if partner IP is in allowlist (if configured)
3. Check if download limit reached
4. Check if token is valid

**Resolution:**
- If expired: Create new share or rotate token
- If IP blocked: Update allowlist or remove it
- If limit reached: Create new share with higher limit
- If token invalid: Regenerate via rotate

### Partner Downloaded Wrong File

**Diagnosis:**
1. Check which export was selected when share was created
2. Verify export file still exists on disk

**Resolution:**
- Create new share with correct export file
- Revoke old share (optional)
- Send new URL to partner with apology

### Watermark Not Visible

**Diagnosis:**
1. Check `WATERMARK_ENABLED` setting
2. Check if PyPDF2/reportlab installed
3. Check logs for watermarking errors

**Resolution:**
- Install dependencies: `pip install PyPDF2 reportlab`
- Enable watermarking in config
- Regenerate share

## Metrics to Track

### Per-Partner Metrics

- **Time to First Access:** How quickly partner opens link
- **Download Rate:** Percentage of partners who download
- **Engagement Rate:** Opens per partner
- **Blocked Rate:** Blocked events per partner (should be low)

### Overall Program Metrics

- **Active Shares:** Number of currently active shares
- **Total Downloads:** Cumulative downloads across all shares
- **Average Time to Download:** Time from creation to first download
- **Partner Feedback Score:** Qualitative feedback ratings
- **Conversion Rate:** Partners interested in next steps

## Email Template Customization

All email templates support Jinja-style placeholders:

```markdown
{{recipient_first_name}}    # Partner's first name
{{secure_share_url}}        # Full share URL
{{expiry_date}}             # Expiry date (formatted)
{{max_downloads}}           # Max download count
{{days_valid}}              # Days from creation to expiry
{{days_remaining}}          # Days left before expiry
{{support_email}}           # Your support email
{{revoked_reason}}          # Reason for revocation
```

**How to Customize:**

1. Edit template files in `backend/emails/`
2. Keep placeholders intact (e.g., `{{...}}`)
3. Update branding, tone, and messaging as needed
4. Test templates before sending to partners

## Checklist Summary

### Before Creating Share
- [ ] Partner qualified and approved
- [ ] NDA signed (if required)
- [ ] Reclaim Pack generated and verified
- [ ] Contact information collected

### During Share Creation
- [ ] Correct export file selected
- [ ] Contact details entered correctly
- [ ] Policy configured appropriately
- [ ] Watermarking enabled
- [ ] Internal notes added

### After Share Creation
- [ ] Share URL copied
- [ ] Onboarding email sent
- [ ] Access granted email sent
- [ ] Analytics monitoring set up

### During Access Period
- [ ] Access analytics reviewed weekly
- [ ] No suspicious activity detected
- [ ] Reminder email sent (3 days before expiry)

### After Expiry/Download
- [ ] Feedback email sent
- [ ] Partner response documented
- [ ] Next steps determined
- [ ] Follow-up tasks scheduled

## Resources

- **Documentation:** `/app/docs/PARTNER_PORTAL.md`
- **Email Templates:** `/app/backend/emails/`
- **API Reference:** `/app/backend/routes/partner_shares.py`
- **Admin UI:** Admin > Partner Shares
- **Partner Landing Page:** `/share/{token}`

## Support

For questions or issues with the Partner Portal:
- **Email:** support@peptimancer.com
- **Docs:** /app/docs/PARTNER_PORTAL.md
- **Logs:** /var/log/supervisor/backend.*.log
