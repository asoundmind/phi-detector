# PHI Detector - Data Flow by Message Type

This document shows separate data flows for each message type (pii_ticket, dev_ticket, question) and demonstrates how the original input transforms through each processing stage.

---

## Flow 1: PII Support Ticket

### Original Input
```
User test@test.com (SIN: 123-456-789) reports issue with login.
Contact them at 555-1234.
```

### Stage 1: Classification (chatbot.py:91-198)
**Process:** Message classification with pattern detection

**Input Analysis:**
- Scan for PII patterns (email, phone, SSN)
- Check for dev keywords
- Check for question words

**Findings:**
- ✓ Email pattern: `test@test.com`
- ✓ SSN pattern: `123-456-789`
- ✓ Phone pattern: `555-1234`
- **PII Count: 3** (≥2 triggers pii_ticket classification)

**Output:** `message_type = 'pii_ticket'`

**Classification Reasoning:**
```
Step 1: Scanning for actual PII patterns
  - ✓ Email pattern detected
  - ✓ Phone pattern detected
  - ✓ SSN pattern detected
  - Total PII patterns found: 3
  → Conclusion: Contains 3 PII patterns → Likely PII Support Ticket

Final Conclusion: PII Support Ticket
Confidence: HIGH
```

---

### Stage 2: PHI Detection (chatbot.py:447-558)
**Process:** Extract and categorize personal information

**Input:** Original ticket text

**PHI Detector Analysis:**
```python
detections = [
    {'type': 'EMAIL', 'value': 'test@test.com', 'start': 5, 'end': 19},
    {'type': 'SSN', 'value': '123-456-789', 'start': 26, 'end': 37},
    {'type': 'PHONE_NUMBER', 'value': '555-1234', 'start': 76, 'end': 84}
]
```

**Output:** List of structured PII detections

---

### Stage 3: Risk Assessment (chatbot.py:323-384)
**Process:** Determine overall privacy risk level

**Input:** List of detections from Stage 2

**Risk Analysis:**
- SSN detected → **CRITICAL** category
- Email detected → MEDIUM category
- Phone detected → MEDIUM category

**Risk Reasoning Chain:**
```
Step 1: Cataloging detected PII types
  - SSN: 1 instance(s) [CRITICAL category]
  - EMAIL: 1 instance(s) [MEDIUM category]
  - PHONE_NUMBER: 1 instance(s) [MEDIUM category]
  → Conclusion: Found 3 PII items across 3 types

Step 2: Identifying highest risk elements
  - ⚠️ CRITICAL types found: SSN
  - Triggers automatic CRITICAL classification
  → Conclusion: Risk level determined: CRITICAL

Step 3: Considering context and linkability
  - Multiple identifier types (3) increase linkability risk
  → Conclusion: Context analysis complete

Final Conclusion: CRITICAL
Primary Factor: Presence of SSN
Secondary Factors: High linkability (multiple identifier types)
Confidence: HIGH
```

**Output:** `risk_level = "CRITICAL"`

---

### Stage 4: RAG Query Formation (chatbot.py:476-478)
**Process:** Transform original question into policy search query

**Input:**
- Detected types: `['SSN', 'EMAIL', 'PHONE_NUMBER']`
- Risk level: `CRITICAL`

**Query Transformation:**
```
ORIGINAL:
"User test@test.com (SIN: 123-456-789) reports issue with login.
Contact them at 555-1234."

↓ TRANSFORMED TO ↓

"How should we handle and protect SSN, EMAIL, PHONE_NUMBER information?
What are the security requirements and privacy obligations for CRITICAL
risk personal information?"
```

**Output:** Semantic search query optimized for policy retrieval

---

### Stage 5: RAG Context Retrieval (chatbot.py:482-487)
**Process:** Semantic search in ChromaDB

**Input:** Query from Stage 4

**Vector Search:**
- Query → Sentence Transformer embedding (768-dim vector)
- Cosine similarity search in ChromaDB
- Retrieve top_k=3 most relevant chunks

**Retrieved Context:**
```
[Context 1] Source: PHIPA.txt (score: 0.8521)
"Personal health information must be encrypted both at rest and in
transit using industry-standard encryption methods. Organizations
must implement appropriate security safeguards..."

[Context 2] Source: PIPEDA.txt (score: 0.8243)
"Organizations must protect personal information with security
safeguards appropriate to the sensitivity of the information.
For highly sensitive data, enhanced security measures are required..."

[Context 3] Source: BC_PIPA.txt (score: 0.8012)
"When handling personal information that could cause significant
harm if disclosed, organizations must ensure maximum protection
through encryption, access controls, and audit logging..."
```

**Output:** List of (text, metadata, score) tuples

---

### Stage 6: Prompt Building (prompt_templates.py:412-433)
**Process:** Construct Chain-of-Thought prompt for LLM

**Input:**
- Original ticket text
- Detections list
- Risk level
- Context chunks

**Prompt Structure:**
```
[SYSTEM PROMPT]
You are a Canadian Privacy Compliance Assistant...
IMPORTANT - Chain of Thought Reasoning:
You MUST think step-by-step through problems:
1. Break down complex questions into smaller parts
2. Analyze each piece of information systematically
...

---

[USER PROMPT]
You are analyzing a support ticket for personal information and
privacy risks.

**Ticket Content:**
User test@test.com (SIN: 123-456-789) reports issue with login.
Contact them at 555-1234.

**Detected Personal Information:**
- **EMAIL** (1 occurrence)
  - test@test.com
- **SSN** (1 occurrence)
  - 123-456-789
- **PHONE_NUMBER** (1 occurrence)
  - 555-1234

**Overall Risk Level:** 🔴 CRITICAL RISK

**Your Task:**
Provide a professional analysis using STEP-BY-STEP REASONING:

**STEP 1: Understanding the Data**
- What types of personal information are present?
- What is the context of this information?
- Are there any patterns or combinations of concern?

**STEP 2: Regulatory Analysis**
- Which Canadian privacy regulations apply (PIPEDA, provincial laws)?
- What specific requirements are triggered by this data?
- Are there any special categories (health data, financial, etc.)?

[... STEPS 3-5 ...]

**Relevant Privacy Regulations:**
[Context 1] Source: PHIPA.txt
Personal health information must be encrypted both at rest and in
transit using industry-standard encryption methods...

[Context 2] Source: PIPEDA.txt
Organizations must protect personal information with security
safeguards appropriate to the sensitivity of the information...

[Context 3] Source: BC_PIPA.txt
When handling personal information that could cause significant
harm if disclosed, organizations must ensure maximum protection...
```

**Output:** Complete structured prompt (~2,200 characters)

---

### Stage 7: LLM Generation (ollama_client.py)
**Process:** Generate compliance analysis using local LLM

**Input:** Prompt from Stage 6

**LLM Request:**
```python
{
    'model': 'gemma2:2b',
    'prompt': full_prompt,
    'temperature': 0.3,
    'max_tokens': 800
}
```

**LLM Processing:**
- Reads system instructions + context + CoT framework
- Generates step-by-step analysis following template
- Includes citations to policy sources

**Generated Response:**
```
STEP 1: Understanding the Data
The ticket contains three types of personal information:
- Email address (test@test.com) - a direct identifier
- Social Insurance Number (123-456-789) - a critical identifier
- Phone number (555-1234) - a contact identifier

This combination creates a high linkability risk where the individual
can be uniquely identified and contacted. The presence of a SIN makes
this particularly sensitive as it's used for government benefits and
can enable identity theft.

STEP 2: Regulatory Analysis
This information falls under multiple Canadian privacy laws:
- PIPEDA (federal): Applies as this is personal information in
  commercial context
- Provincial acts (PHIPA if healthcare-related): The SIN suggests
  this may involve health or government services

The SIN triggers special handling requirements under federal privacy
guidelines. Collection and use must be strictly limited to legally
authorized purposes.

STEP 3: Risk Evaluation
This is classified as CRITICAL risk because:
- SINs are government identifiers with severe consequences if
  compromised
- The combination enables identity theft and fraud
- Unauthorized disclosure could cause significant harm to the
  individual
- Multiple identifiers increase linkability and re-identification risk

STEP 4: Compliance Requirements
Under PIPEDA and provincial laws:
- Encryption: Must encrypt at rest (AES-256) and in transit (TLS 1.3)
- Access Controls: Implement strict role-based access, need-to-know
- Audit Logging: Log all access to this information
- Retention: Retain only as long as legally required
- Breach Notification: Must report any breach to Privacy Commissioner
  and affected individual

STEP 5: Recommended Actions
Immediate:
1. Redact the SIN from the ticket unless absolutely necessary
2. Encrypt the ticket data in storage
3. Restrict access to authorized personnel only
4. Create audit log entry for this access

Ongoing:
1. Implement data minimization - question if SIN is needed
2. Use tokenization or pseudonymization where possible
3. Establish retention policy and auto-deletion
4. Train staff on handling sensitive identifiers
5. Regular privacy impact assessments

🔴 CRITICAL: The presence of SIN requires maximum protection measures
and careful justification for collection and use.
```

**Output:** Structured compliance analysis with actionable guidance

---

### Stage 8: Response Assembly (chatbot.py:682-692)
**Process:** Package response with metadata

**Output to User:**
```python
{
    'response': <LLM generated analysis>,
    'prompt': <Full prompt sent to LLM>,
    'metadata': {
        'detections': [
            {'type': 'EMAIL', 'value': 'test@test.com', ...},
            {'type': 'SSN', 'value': '123-456-789', ...},
            {'type': 'PHONE_NUMBER', 'value': '555-1234', ...}
        ],
        'risk_level': 'CRITICAL',
        'context_chunks': [...],
        'classification_reasoning': <ReasoningChain object>,
        'risk_reasoning': <ReasoningChain object>
    },
    'message_type': 'pii_ticket'
}
```

---

### Stage 9: UI Display (app.py:201-267)
**What the User Sees:**

```
✅ Detected as: PII Support Ticket (will analyze for personal information)

### Analysis Result
[Full LLM response with STEP 1 through STEP 5]

[Expandable Sections:]
🧠 Classification Reasoning
  [Shows why it was classified as PII ticket]

⚠️ Risk Assessment Reasoning
  [Shows step-by-step risk analysis]

🔧 View Prompt Used
  [Full prompt sent to LLM]

📋 PII Detection Details (3 items found)
  Risk Level: CRITICAL
  - EMAIL: test@test.com
  - SSN: 123-456-789
  - PHONE_NUMBER: 555-1234

📚 Policy References (3 sources)
  [1] PHIPA.txt (relevance: 0.8521)
  [2] PIPEDA.txt (relevance: 0.8243)
  [3] BC_PIPA.txt (relevance: 0.8012)
```

---

## Question Transformation Summary (PII Ticket)

```
STAGE 1 - Original Input:
"User test@test.com (SIN: 123-456-789) reports issue with login.
Contact them at 555-1234."

↓

STAGE 4 - RAG Query:
"How should we handle and protect SSN, EMAIL, PHONE_NUMBER information?
What are the security requirements and privacy obligations for CRITICAL
risk personal information?"

↓

STAGE 6 - LLM Prompt:
"You are analyzing a support ticket for personal information and
privacy risks.

**Ticket Content:** [original text]
**Detected Personal Information:** [structured list]
**Overall Risk Level:** CRITICAL

Provide STEP-BY-STEP analysis:
STEP 1: Understanding the Data
STEP 2: Regulatory Analysis
STEP 3: Risk Evaluation
STEP 4: Compliance Requirements
STEP 5: Recommended Actions

**Relevant Privacy Regulations:** [3 policy excerpts]"

↓

STAGE 9 - Final Response to User:
"STEP 1: Understanding the Data
The ticket contains three types of personal information...
[Complete 5-step analysis with specific compliance guidance]"
```

---
---

## Flow 2: Development Ticket

### Original Input
```
As a PM, I'm creating a ticket for storing chat messages between users
and healthcare providers. Does this data require encryption? What
technology measures are recommended for compliance?
```

### Stage 1: Classification (chatbot.py:91-198)
**Process:** Message classification with keyword detection

**Input Analysis:**
- Scan for PII patterns
- Check for development keywords
- Check for question words

**Findings:**
- ✗ Email pattern: Not found
- ✗ Phone pattern: Not found
- ✗ SSN pattern: Not found
- **PII Count: 0**
- ✓ Dev keywords: 'pm', 'creating', 'storing', 'chat message', 'between user' (5 indicators)
- ✓ Question words: 'does', 'what' (has questions)
- **Dev indicators ≥2 AND has questions** → dev_ticket

**Output:** `message_type = 'dev_ticket'`

**Classification Reasoning:**
```
Step 1: Scanning for actual PII patterns
  - ✗ Email pattern not found
  - ✗ Phone pattern not found
  - ✗ SSN pattern not found
  - Total PII patterns found: 0
  → Conclusion: No PII patterns → Not a PII ticket

Step 2: Checking for development/PM indicators
  - Found: 'pm'
  - Found: 'creating'
  - Found: 'storing'
  - Found: 'chat message'
  - Found: 'between user'
  - Total: 5 development indicators
  → Conclusion: 5 indicators present

Step 3: Analyzing question patterns
  - ✓ Contains question words (does, what)
  → Conclusion: Message is asking questions

Final Conclusion: Development/Requirements Ticket
Confidence: HIGH
```

---

### Stage 2: Initial RAG Query (chatbot.py:214-229)
**Process:** Semantic search for compliance guidance

**Input:** Original ticket text (unchanged)

**Query:**
```
"As a PM, I'm creating a ticket for storing chat messages between users
and healthcare providers. Does this data require encryption? What
technology measures are recommended for compliance?"
```

**Vector Search:**
- Original question → Embedding
- Semantic search with top_k=3

**Retrieved Context (Initial):**
```
[Context 1] Source: PHIPA.txt (score: 0.8430)
"Personal health information must be encrypted both at rest and in
transit using industry-standard encryption methods. Healthcare
communications require TLS 1.3 or higher for transmission..."

[Context 2] Source: PIPEDA.txt (score: 0.8210)
"Organizations must implement appropriate security safeguards,
including technical measures such as encryption, when storing personal
information. For communications containing personal information, secure
transmission protocols are required..."

[Context 3] Source: BC_PIPA.txt (score: 0.7980)
"When collecting personal information electronically, organizations
must ensure secure transmission protocols and encrypted storage for
sensitive communications..."
```

**Output:** 3 initial context chunks

---

### Stage 3: Multi-Step RAG Analysis (chain_of_thought.py:373-471)
**Process:** Identify gaps and expand context with follow-up queries

**Input:**
- Original ticket text
- Initial 3 context chunks

**Gap Analysis:**
```python
# Analyze ticket for specific topics
ticket_lower = ticket_text.lower()

if 'encryption' in ticket_lower:
    keywords_to_explore.append('encryption standards')
if 'consent' in ticket_lower:
    keywords_to_explore.append('consent requirements')
if 'retention' in ticket_lower:
    keywords_to_explore.append('data retention requirements')
```

**Findings:**
- Detected keyword: 'encryption' ✓
- Detected keyword: 'chat' → implies retention considerations

**Follow-up Queries:**
```
Query 1: "encryption standards"
Query 2: "data retention requirements"
```

**Follow-up RAG Results:**
```
[Query 1: "encryption standards"]
  - Retrieved 2 additional chunks about AES-256, key management

[Query 2: "data retention requirements"]
  - Retrieved 2 additional chunks about retention policies, deletion
```

**Multi-Step RAG Reasoning:**
```
Step 1: Initial broad policy search
  - Retrieved 3 relevant policy chunks
  - Sources: PHIPA.txt, PIPEDA.txt, BC_PIPA.txt
  → Conclusion: Found 3 relevant passages

Step 2: Identifying gaps and performing follow-up queries
  - Identified specific topics to explore: encryption standards,
    data retention requirements
  - ✓ Follow-up query 'encryption standards': 2 results
  - ✓ Follow-up query 'data retention requirements': 2 results
  → Conclusion: Total context expanded to 7 passages

Step 3: Deduplicating context
  - Total passages retrieved: 7
  - Duplicates removed: 2
  - Unique passages: 5
  → Conclusion: Final context: 5 unique passages

Final Conclusion: Multi-step analysis complete with 5 unique policy
references
Confidence: HIGH
```

**Output:** 5 unique context chunks + reasoning chain

---

### Stage 4: Prompt Building (prompt_templates.py:457-475)
**Process:** Construct CoT development guidance prompt

**Input:**
- Original ticket text
- 5 unique context chunks from multi-step RAG

**Prompt Structure:**
```
[SYSTEM PROMPT]
You are a Canadian Privacy Compliance Assistant...
IMPORTANT - Chain of Thought Reasoning:
You MUST think step-by-step through problems...

---

[USER PROMPT]
You are a privacy compliance advisor helping development teams
understand regulatory requirements.

**Development Ticket:**
As a PM, I'm creating a ticket for storing chat messages between users
and healthcare providers. Does this data require encryption? What
technology measures are recommended for compliance?

**Relevant Privacy Regulations:**
[Context 1] Source: PHIPA.txt
Personal health information must be encrypted both at rest and in
transit using industry-standard encryption methods. Healthcare
communications require TLS 1.3 or higher...

[Context 2] Source: PIPEDA.txt
Organizations must implement appropriate security safeguards,
including technical measures such as encryption...

[Context 3] Source: BC_PIPA.txt
When collecting personal information electronically, organizations
must ensure secure transmission protocols...

[Context 4] Source: PHIPA.txt
Encryption standards for PHI should meet or exceed AES-256 for data
at rest. Key management must follow industry best practices...

[Context 5] Source: PIPEDA.txt
Personal information retention should be limited to the minimum
necessary. Organizations must implement deletion policies...

**Your Task:**
Provide STEP-BY-STEP compliance guidance:

**STEP 1: Understanding the Technical Requirement**
- What system/feature is being built?
- What type of data will be processed?
- What is the user context (healthcare, general public, employees)?

**STEP 2: Classification and Applicability**
- Is this personal information? Personal health information?
- Which regulations apply (PIPEDA, PHIPA, BC PIPA)?
- What is the sensitivity level?

**STEP 3: Analyzing Regulatory Requirements**
- What do the applicable laws require?
- Are there specific technical safeguards mandated?
- What about consent, access rights, retention?

**STEP 4: Technical Security Measures**
- What encryption is required (at rest, in transit)?
- What access controls are needed?
- What logging and audit requirements exist?
- What backup and recovery measures?

**STEP 5: Implementation Guidance**
- Specific technologies recommended (e.g., AES-256, TLS 1.3)
- Architecture patterns for compliance
- Testing and validation approaches
- Documentation requirements

**STEP 6: Risk Assessment and Best Practices**
- Privacy risks to address
- Beyond minimum compliance - recommended practices
- Common pitfalls to avoid

Present your analysis following these steps. Be specific and actionable
with technology recommendations. Distinguish between legal requirements
and industry best practices.
```

**Output:** Complete structured prompt (~3,000 characters)

---

### Stage 5: LLM Generation (ollama_client.py)
**Process:** Generate technical compliance guidance

**Input:** Prompt from Stage 4

**LLM Request:**
```python
{
    'model': 'gemma2:2b',
    'prompt': full_prompt,
    'temperature': 0.4,
    'max_tokens': 800
}
```

**Generated Response:**
```
STEP 1: Understanding the Technical Requirement
The system being built is a messaging feature that enables
communication between users (likely patients) and healthcare providers.
This is a chat/messaging system that will:
- Store conversation history
- Handle communications containing health information
- Require authentication and access controls

The data processed will be personal health information (PHI) under
Canadian privacy law, as it involves healthcare providers discussing
patient matters.

STEP 2: Classification and Applicability
Type of Information: Personal Health Information (PHI)

Applicable Regulations:
- PHIPA (Personal Health Information Protection Act) - if in Ontario
- PIPEDA (federal law) - applies across Canada for private sector
- Provincial equivalents in other provinces (BC PIPA, Alberta HIA)

Sensitivity Level: HIGH - Healthcare communications are among the most
sensitive categories of personal information.

STEP 3: Analyzing Regulatory Requirements
Based on PHIPA and PIPEDA:

1. Encryption Requirements:
   - Data must be encrypted both at rest and in transit
   - Industry-standard encryption methods required

2. Access Controls:
   - Only authorized healthcare providers can access patient messages
   - Role-based access control (RBAC) required
   - Audit trails for all access

3. Consent:
   - Must obtain patient consent for collecting and storing messages
   - Clear disclosure of how messages will be used and who can access

4. Retention:
   - Healthcare records have specific retention periods
   - Must implement secure deletion after retention period

STEP 4: Technical Security Measures
Required Encryption:
- At Rest: AES-256 encryption for database storage
- In Transit: TLS 1.3 (minimum TLS 1.2) for all communications
- End-to-end encryption recommended for maximum privacy

Access Controls:
- Multi-factor authentication (MFA) for healthcare provider access
- Role-based access control (RBAC)
- Session management with automatic timeout
- IP whitelisting for additional security

Logging and Audit:
- Log all message access with timestamp, user ID, and action
- Immutable audit logs retained separately
- Real-time monitoring for unauthorized access attempts

Backup and Recovery:
- Encrypted backups stored separately
- Tested recovery procedures
- Geographic redundancy if possible

STEP 5: Implementation Guidance
Recommended Technologies:

Database:
- PostgreSQL with pgcrypto extension for encryption
- Or cloud solutions: AWS RDS with encryption enabled, Azure SQL with
  TDE (Transparent Data Encryption)

Transport Security:
- HTTPS everywhere with TLS 1.3
- Certificate pinning in mobile apps
- Reject older TLS versions and weak cipher suites

Messaging Architecture:
- Consider Signal Protocol for end-to-end encryption
- WebSocket over TLS for real-time messaging
- Message queuing with encryption (RabbitMQ with TLS, AWS SQS)

Key Management:
- Use HSM (Hardware Security Module) or cloud KMS
- AWS KMS, Azure Key Vault, or HashiCorp Vault
- Regular key rotation policies

Authentication:
- OAuth 2.0 / OpenID Connect
- MFA using TOTP or SMS (TOTP preferred)
- Healthcare-specific identity providers if available

Testing:
- Penetration testing for security vulnerabilities
- Encryption verification (data at rest and in transit)
- Access control testing
- Compliance audit

Documentation:
- Privacy Impact Assessment (PIA)
- Security architecture documentation
- Data flow diagrams
- Incident response plan

STEP 6: Risk Assessment and Best Practices
Privacy Risks to Address:
1. Unauthorized access by staff → Implement strict RBAC and audit
2. Data breach during transmission → Use TLS 1.3, end-to-end encryption
3. Improper retention → Automated deletion policies
4. Lack of patient control → Provide access and deletion rights
5. Third-party vendors → Ensure vendor contracts include privacy terms

Best Practices Beyond Compliance:
- Implement end-to-end encryption even if not legally required
- Data minimization: only store necessary message content
- Pseudonymization where possible
- Regular security audits and penetration testing
- Privacy by design: build privacy into architecture from the start
- User education: teach patients and providers about secure messaging

Common Pitfalls to Avoid:
- Don't store messages in plain text "temporarily"
- Don't use weak encryption (DES, MD5, SHA-1)
- Don't skip audit logging "for performance"
- Don't allow screenshot or copy/paste without logging
- Don't forget about metadata (timestamps, sender/recipient info)
- Don't neglect mobile security (app must also encrypt locally)

⚠️ Recommendation: Given the healthcare context, aim for security
standards above minimum compliance. Consider certification against
healthcare security standards (e.g., HITRUST) and conduct third-party
security audits.
```

**Output:** Comprehensive technical compliance guidance

---

### Stage 6: Response Assembly (chatbot.py:700-709)
**Process:** Package response with metadata

**Output to User:**
```python
{
    'response': <LLM generated guidance>,
    'prompt': <Full prompt sent to LLM>,
    'metadata': {
        'context_chunks': [5 unique policy chunks],
        'ticket_type': 'development',
        'classification_reasoning': <ReasoningChain object>,
        'rag_reasoning': <ReasoningChain object>
    },
    'message_type': 'dev_ticket'
}
```

---

### Stage 7: UI Display (app.py:201-267)
**What the User Sees:**

```
🛠️ Detected as: Development Ticket (will provide compliance guidance)

### Analysis Result
[Full LLM response with STEP 1 through STEP 6]

[Expandable Sections:]
🧠 Classification Reasoning
  [Shows why it was classified as development ticket]

🔍 Multi-Step RAG Analysis
  Multi-Step Compliance Analysis
  Step 1: Initial broad policy search
    - Retrieved 3 relevant policy chunks
    - Sources: PHIPA.txt, PIPEDA.txt, BC_PIPA.txt
  Step 2: Identifying gaps and performing follow-up queries
    - Identified topics: encryption standards, data retention
    - ✓ Follow-up query 'encryption standards': 2 results
    - ✓ Follow-up query 'data retention requirements': 2 results
  Step 3: Deduplicating context
    - Unique passages: 5
  Final Conclusion: Multi-step analysis complete with 5 unique
  policy references

🔧 View Prompt Used
  [Full prompt sent to LLM - 3,000 characters]

📚 Policy References (5 sources)
  [1] PHIPA.txt (relevance: 0.8430)
  [2] PIPEDA.txt (relevance: 0.8210)
  [3] BC_PIPA.txt (relevance: 0.7980)
  [4] PHIPA.txt (relevance: 0.7654)
  [5] PIPEDA.txt (relevance: 0.7432)
```

---

## Question Transformation Summary (Dev Ticket)

```
STAGE 1 - Original Input:
"As a PM, I'm creating a ticket for storing chat messages between users
and healthcare providers. Does this data require encryption? What
technology measures are recommended for compliance?"

↓

STAGE 2 - Initial RAG Query (unchanged):
"As a PM, I'm creating a ticket for storing chat messages between users
and healthcare providers. Does this data require encryption? What
technology measures are recommended for compliance?"

↓

STAGE 3 - Follow-up Queries (identified from original):
Query 1: "encryption standards"
Query 2: "data retention requirements"
[Retrieved 4 additional chunks, total 7, deduplicated to 5]

↓

STAGE 4 - LLM Prompt:
"You are a privacy compliance advisor helping development teams.

**Development Ticket:** [original text]

**Relevant Privacy Regulations:** [5 policy excerpts from multi-step RAG]

Provide STEP-BY-STEP compliance guidance:
STEP 1: Understanding the Technical Requirement
STEP 2: Classification and Applicability
STEP 3: Analyzing Regulatory Requirements
STEP 4: Technical Security Measures
STEP 5: Implementation Guidance
STEP 6: Risk Assessment and Best Practices"

↓

STAGE 7 - Final Response to User:
"STEP 1: Understanding the Technical Requirement
The system being built is a messaging feature...
[Complete 6-step technical compliance guidance with specific
technologies: AES-256, TLS 1.3, PostgreSQL, AWS KMS, OAuth 2.0, etc.]"
```

---
---

## Flow 3: Policy Question

### Original Input
```
What are the consent requirements for collecting personal information
under PIPEDA?
```

### Stage 1: Classification (chatbot.py:91-198)
**Process:** Message classification

**Input Analysis:**
- Scan for PII patterns
- Check for development keywords
- Check for question words

**Findings:**
- ✗ Email pattern: Not found
- ✗ Phone pattern: Not found
- ✗ SSN pattern: Not found
- **PII Count: 0**
- Dev keywords: None significant
- ✓ Question words: 'what', 'are' (has questions)
- **Not enough for PII ticket or dev ticket** → question

**Output:** `message_type = 'question'`

**Classification Reasoning:**
```
Step 1: Scanning for actual PII patterns
  - ✗ Email pattern not found
  - ✗ Phone pattern not found
  - ✗ SSN pattern not found
  - Total PII patterns found: 0
  → Conclusion: No PII patterns → Not a PII ticket

Step 2: Checking for development/PM indicators
  - No development keywords found
  → Conclusion: Not a development ticket

Step 3: Analyzing question patterns
  - ✓ Contains question words (what, are)
  → Conclusion: Message is asking questions

Final Conclusion: General Policy Question
Confidence: HIGH
```

---

### Stage 2: RAG Query (chatbot.py:584-599)
**Process:** Semantic search for policy information

**Input:** Original question (unchanged)

**Query:**
```
"What are the consent requirements for collecting personal information
under PIPEDA?"
```

**Vector Search:**
- Question → Embedding
- Semantic search with top_k=2 (questions use fewer chunks)

**Retrieved Context:**
```
[Context 1] Source: PIPEDA.txt (score: 0.8923)
"Organizations must obtain meaningful consent when collecting, using,
or disclosing personal information. Consent must be:
- Informed: Individuals understand what they're consenting to
- Specific: Related to identified purposes
- Voluntary: Not coerced or bundled with unrelated services
- Revocable: Individuals can withdraw consent

The form of consent may vary depending on circumstances and sensitivity.
Express consent is required for sensitive personal information."

[Context 2] Source: PIPEDA.txt (score: 0.8654)
"Principle 3 - Consent: The knowledge and consent of the individual are
required for the collection, use, or disclosure of personal information,
except where inappropriate.

Organizations shall make a reasonable effort to ensure the individual is
advised of the purposes for which the information will be used. Purposes
must be stated in a manner that can be reasonably understood."
```

**Output:** 2 context chunks directly about PIPEDA consent

---

### Stage 3: Prompt Building (prompt_templates.py:436-454)
**Process:** Construct CoT policy question prompt

**Input:**
- Original question
- 2 context chunks

**Prompt Structure:**
```
[SYSTEM PROMPT]
You are a Canadian Privacy Compliance Assistant...
IMPORTANT - Chain of Thought Reasoning:
You MUST think step-by-step through problems...

---

[USER PROMPT]
You are a Canadian Privacy Compliance Assistant answering a question
about privacy regulations.

**Question:**
What are the consent requirements for collecting personal information
under PIPEDA?

**Relevant Policy Context:**
[Context 1] Source: PIPEDA.txt
Organizations must obtain meaningful consent when collecting, using,
or disclosing personal information. Consent must be:
- Informed: Individuals understand what they're consenting to
- Specific: Related to identified purposes
- Voluntary: Not coerced or bundled with unrelated services
- Revocable: Individuals can withdraw consent

The form of consent may vary depending on circumstances and sensitivity.
Express consent is required for sensitive personal information.

[Context 2] Source: PIPEDA.txt
Principle 3 - Consent: The knowledge and consent of the individual are
required for the collection, use, or disclosure of personal information,
except where inappropriate.

Organizations shall make a reasonable effort to ensure the individual is
advised of the purposes for which the information will be used. Purposes
must be stated in a manner that can be reasonably understood.

**Your Task:**
Answer using STEP-BY-STEP REASONING:

**STEP 1: Understanding the Question**
- What is being asked?
- What is the core legal/compliance issue?
- What context is relevant?

**STEP 2: Analyzing the Policy Context**
- What does each policy document say about this issue?
- Which regulations are most relevant?
- Are there any conflicts or nuances between sources?

**STEP 3: Identifying Requirements**
- What are the specific legal requirements?
- What distinctions exist between federal (PIPEDA) and provincial laws?
- Are there any exceptions or special cases?

**STEP 4: Practical Application**
- How do these requirements apply in practice?
- What steps must organizations take?
- What are the consequences of non-compliance?

**STEP 5: Final Answer**
- Direct answer to the question
- Key citations and sources
- Any limitations or caveats

Present your answer following these analytical steps. Cite specific
regulations and policy sections. If the context doesn't fully answer
the question, explain what's missing and suggest consulting legal
counsel.
```

**Output:** Complete structured prompt (~2,100 characters)

---

### Stage 4: LLM Generation (ollama_client.py)
**Process:** Generate policy answer with citations

**Input:** Prompt from Stage 3

**LLM Request:**
```python
{
    'model': 'gemma2:2b',
    'prompt': full_prompt,
    'temperature': 0.4,
    'max_tokens': 600
}
```

**Generated Response:**
```
STEP 1: Understanding the Question
The question asks about the consent requirements under PIPEDA
(Personal Information Protection and Electronic Documents Act),
Canada's federal privacy law.

The core legal issue is: What constitutes valid consent when an
organization collects personal information from individuals?

This is fundamental to PIPEDA compliance as Principle 3 of PIPEDA's
Fair Information Principles specifically addresses consent.

STEP 2: Analyzing the Policy Context
Both policy excerpts are from PIPEDA and address the same principle
from different angles:

Context 1 defines the characteristics of "meaningful consent":
- Must be informed (individual understands what they're agreeing to)
- Must be specific (tied to particular purposes)
- Must be voluntary (not forced or bundled)
- Must be revocable (can be withdrawn)
- Form varies by sensitivity (express consent for sensitive data)

Context 2 provides the foundational principle:
- Consent is required for collection, use, OR disclosure
- There are exceptions ("except where inappropriate")
- Organizations must make reasonable efforts to inform individuals
  of purposes
- Purposes must be understandable to the average person

There are no conflicts between these sources - they complement each
other.

STEP 3: Identifying Requirements
Specific Legal Requirements under PIPEDA:

1. Obtain consent for collection, use, or disclosure of personal
   information

2. Consent must be "meaningful":
   - Informed: Provide clear information about purposes
   - Specific: Identify specific purposes, not blanket consent
   - Voluntary: Cannot be a condition of service for unrelated purposes
   - Revocable: Must allow withdrawal of consent

3. Form of consent depends on sensitivity:
   - Implied consent: May be acceptable for non-sensitive information
   - Express consent: Required for sensitive information (health,
     financial, biometric, etc.)

4. Timing: Consent should be obtained at or before collection

5. Communication: Purposes must be stated in understandable language

Exceptions:
PIPEDA allows collection without consent in limited circumstances:
- Legal requirement or court order
- Emergency threatening life/health
- Publicly available information (with restrictions)
- Investigation of breach of contract or law
- Journalistic, artistic, or literary purposes

STEP 4: Practical Application
Organizations must:

1. Before Collection:
   - Identify the purposes for collecting information
   - Determine appropriate form of consent (implied vs. express)
   - Prepare clear consent language in plain language

2. During Collection:
   - Inform individuals of purposes at time of collection
   - Obtain appropriate consent (express for sensitive data)
   - Document consent obtained
   - Provide option to decline (unless legally required)

3. After Collection:
   - Honor consent limitations (only use for stated purposes)
   - Provide mechanism for individuals to withdraw consent
   - Stop using information if consent is withdrawn (with reasonable
     exceptions)

Consequences of Non-Compliance:
- Privacy Commissioner investigation and findings
- Reputational damage
- Federal Court action for non-compliance
- Potential damages if individual harmed
- Business disruption from required remediation

STEP 5: Final Answer
Under PIPEDA, consent requirements for collecting personal information
are:

**Core Requirement:** Organizations must obtain meaningful consent from
individuals before collecting their personal information [PIPEDA
Principle 3].

**Meaningful Consent Must Be:**
1. **Informed** - Individuals understand what information is collected
   and why
2. **Specific** - Consent tied to identified purposes, not broad blanket
   permission
3. **Voluntary** - Freely given, not coerced or bundled with unrelated
   services
4. **Revocable** - Individuals can withdraw consent

**Form of Consent:**
- **Express consent** (explicit agreement) required for sensitive
  personal information
- **Implied consent** may be acceptable for non-sensitive information
  in appropriate circumstances

**Communication:** Purposes must be stated in language the average
person can reasonably understand.

**Sources:** PIPEDA Fair Information Principle 3 (Consent)

**Important Note:** This answer is based on general PIPEDA requirements.
Specific situations may involve complexities (e.g., minor's consent,
employee consent, research contexts). Organizations should consult
privacy legal counsel for specific compliance situations, especially
when dealing with sensitive personal information or novel collection
methods.
```

**Output:** Structured policy answer with citations

---

### Stage 5: Response Assembly (chatbot.py:717-724)
**Process:** Package response with metadata

**Output to User:**
```python
{
    'response': <LLM generated answer>,
    'prompt': <Full prompt sent to LLM>,
    'metadata': {
        'context_chunks': [2 policy chunks],
        'classification_reasoning': <ReasoningChain object>
    },
    'message_type': 'question'
}
```

---

### Stage 6: UI Display (app.py:201-267)
**What the User Sees:**

```
ℹ️ Detected as: Policy Question (will search knowledge base)

### Analysis Result
[Full LLM response with STEP 1 through STEP 5]

[Expandable Sections:]
🧠 Classification Reasoning
  Complete Message Classification
  Step 1: Scanning for actual PII patterns
    - No PII patterns → Not a PII ticket
  Step 2: Checking for development/PM indicators
    - Not a development ticket
  Step 3: Analyzing question patterns
    - Contains question words
  Final Conclusion: General Policy Question

🔧 View Prompt Used
  [Full prompt sent to LLM - 2,100 characters]

📚 Retrieved Context (2 chunks)
  Chunk 1 (from PIPEDA.txt, score: 0.8923)
  Organizations must obtain meaningful consent when collecting...

  Chunk 2 (from PIPEDA.txt, score: 0.8654)
  Principle 3 - Consent: The knowledge and consent of the individual...
```

---

## Question Transformation Summary (Policy Question)

```
STAGE 1 - Original Input:
"What are the consent requirements for collecting personal information
under PIPEDA?"

↓

STAGE 2 - RAG Query (unchanged):
"What are the consent requirements for collecting personal information
under PIPEDA?"

↓

STAGE 3 - LLM Prompt:
"You are a Canadian Privacy Compliance Assistant answering a question.

**Question:** What are the consent requirements for collecting personal
information under PIPEDA?

**Relevant Policy Context:**
[Context 1] Organizations must obtain meaningful consent when
collecting, using, or disclosing personal information. Consent must
be: Informed, Specific, Voluntary, Revocable...

[Context 2] Principle 3 - Consent: The knowledge and consent of the
individual are required for the collection, use, or disclosure...

Answer using STEP-BY-STEP REASONING:
STEP 1: Understanding the Question
STEP 2: Analyzing the Policy Context
STEP 3: Identifying Requirements
STEP 4: Practical Application
STEP 5: Final Answer"

↓

STAGE 6 - Final Response to User:
"STEP 1: Understanding the Question
The question asks about the consent requirements under PIPEDA...

[Complete 5-step analysis with specific requirements:]
- Meaningful consent must be: Informed, Specific, Voluntary, Revocable
- Express consent required for sensitive information
- Implied consent may be acceptable for non-sensitive
- Purposes must be understandable
[Sources: PIPEDA Principle 3]"
```

---

## Comparison: How Each Type Transforms the Question

### PII Ticket
**Original Question Focus:** User's support issue with personal data
**Transformation:** Extracts PII types → Creates policy search query about handling those specific types → Adds risk context
**Key Change:** "User test@test.com..." → "How to handle SSN, EMAIL, PHONE at CRITICAL risk level?"

### Dev Ticket
**Original Question Focus:** Technical requirements and compliance
**Transformation:** Keeps original question for broad search → Identifies gaps → Adds targeted follow-up queries
**Key Change:** Original preserved, but expanded with: "encryption standards", "data retention requirements"

### Policy Question
**Original Question Focus:** Direct policy/legal question
**Transformation:** Minimal - question used directly for semantic search
**Key Change:** Nearly unchanged - question is already optimized for policy retrieval

---

## Key Differences in Processing

| Stage | PII Ticket | Dev Ticket | Question |
|-------|-----------|------------|----------|
| **Query Transformation** | ✓ Significant (extracts types + risk) | ~ Moderate (adds follow-ups) | ✗ Minimal (direct use) |
| **Multi-Step RAG** | ✗ No | ✓ Yes | ✗ No |
| **Context Chunks** | 3 chunks | 5 chunks (after dedup) | 2 chunks |
| **LLM Steps** | 5 steps | 6 steps | 5 steps |
| **Risk Assessment** | ✓ Yes | ✗ No | ✗ No |
| **PHI Detection** | ✓ Yes | ✗ No | ✗ No |
| **Technical Guidance** | ~ Some | ✓ Extensive | ~ Some |

---

## Summary

This document demonstrates how each message type follows a distinct flow through the PHI Detector system:

1. **PII Ticket**: Focuses on detection → risk assessment → policy-based handling guidance
2. **Dev Ticket**: Focuses on technical requirements → gap analysis → implementation guidance
3. **Policy Question**: Focuses on direct answer → regulatory analysis → practical application

Each flow transforms the original input differently to optimize for its specific purpose, while maintaining transparency through Chain-of-Thought reasoning at every stage.
