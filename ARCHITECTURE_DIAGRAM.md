# PHI Detector - System Architecture with Example Flow

## System Overview

The PHI Detector is a privacy compliance chatbot that analyzes text for personal information (PII/PHI), answers policy questions, and provides technical compliance guidance to development teams. It uses RAG (Retrieval-Augmented Generation), Chain-of-Thought reasoning, and local LLM inference.

---

## High-Level Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Streamlit  │────▶│   ChatBot    │────▶│  RAG System  │────▶│  ChromaDB    │
│   Web UI     │     │  (Routing)   │     │  (Semantic   │     │  (Policy KB) │
│  (app.py)    │     │              │     │   Search)    │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                             │
                             │
                     ┌───────┴────────┐
                     ▼                ▼
              ┌──────────────┐  ┌──────────────┐
              │ PHI Detector │  │ Ollama LLM   │
              │  (spaCy NER) │  │  (gemma2:2b) │
              └──────────────┘  └──────────────┘
```

---

## Example Flow: Development Ticket Processing

### Example Input (from app.py:125-126)

```
"As a PM, I'm creating a ticket for storing chat messages between
users and healthcare providers. Does this data require encryption?
What technology measures are recommended for compliance?"
```

---

## Step-by-Step Flow

### **STEP 1: User Input** (app.py:160-166)
**Location**: Streamlit UI text area
**Input**: User types or clicks example button → text captured

```
user_input = "As a PM, I'm creating a ticket for storing chat messages..."
```

---

### **STEP 2: Analyze Button Click** (app.py:171-190)
**Location**: app.py main processing block

**Actions**:
1. First, classify the message type
   ```python
   msg_type = bot._classify_message(user_input)
   ```

2. Display detection result to user
   ```
   ✅ Detected as: Development Ticket
   ```

3. Process with full chain-of-thought
   ```python
   response, prompt, metadata, message_type = bot.chat(
       user_input,
       return_prompt=True,
       use_cot=True
   )
   ```

---

### **STEP 3: Message Classification** (chatbot.py:91-198)
**Location**: `ChatBot._classify_message()`

**Process**:

#### 3.1 Check for PII Patterns
```python
# Regex patterns for actual PII
has_email = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message)
has_phone = re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', message)
has_ssn = re.search(r'\b\d{3}-\d{2,3}-\d{3,4}\b', message)
```

**Result for our example**:
- Email: ❌ Not found
- Phone: ❌ Not found
- SSN: ❌ Not found
- **PII Count: 0** → Not a PII ticket

#### 3.2 Check for Development Indicators
```python
dev_keywords = [
    'pm ', 'product manager', 'developing', 'building',
    'feature', 'storing', 'encryption', 'chat message',
    'between user', 'requirement', 'compliance'
]
```

**Result for our example**:
- Found: 'pm', 'creating', 'storing', 'chat message', 'between user'
- **Dev indicators: 5** ✓

#### 3.3 Check for Question Words
```python
question_words = ['should', 'need', 'require', 'what', 'how', 'does']
```

**Result for our example**:
- Found: 'does', 'what'
- **Has questions: Yes** ✓

#### 3.4 Chain-of-Thought Classification (chain_of_thought.py:193-249)
```
Classification Reasoning Chain:
├─ Step 1: PII Pattern Analysis
│  ├─ ✗ Email pattern not found
│  ├─ ✗ Phone pattern not found
│  ├─ ✗ SSN pattern not found
│  └─ → Conclusion: No PII patterns → Not a PII ticket
│
├─ Step 2: Development Indicators
│  ├─ Found: 'pm'
│  ├─ Found: 'creating'
│  ├─ Found: 'storing'
│  ├─ Found: 'chat message'
│  ├─ Found: 'between user'
│  └─ → Conclusion: 5 development indicators present
│
├─ Step 3: Question Patterns
│  ├─ ✓ Contains question words (does, what)
│  └─ → Conclusion: Message is asking questions
│
└─ Final Conclusion: Development/Requirements Ticket (Confidence: HIGH)
```

**Classification Result**: `'dev_ticket'`

---

### **STEP 4: Route to Handler** (chatbot.py:648-733)
**Location**: `ChatBot.chat()` main router

```python
if msg_type == 'dev_ticket':
    response, prompt, context_chunks, rag_reasoning = self.answer_dev_ticket(
        message,
        return_prompt=True,
        use_cot=True
    )
```

**Routes to**: `answer_dev_ticket()` method

---

### **STEP 5: Initial RAG Query** (chatbot.py:200-218)
**Location**: `ChatBot.answer_dev_ticket()`

**Action**: Query ChromaDB for relevant policy documents
```python
context_chunks = self.rag.query(ticket_text, top_k=3)
```

**What happens inside RAG**:
1. Text → Sentence Transformer embedding (768-dim vector)
2. Semantic search in ChromaDB collection
3. Returns top 3 most similar chunks with scores

**Example Result**:
```
Context Chunk 1 (score: 0.843):
Source: PHIPA.txt
"Personal health information must be encrypted both at rest and
in transit using industry-standard encryption methods..."

Context Chunk 2 (score: 0.821):
Source: PIPEDA.txt
"Organizations must implement appropriate security safeguards,
including technical measures such as encryption..."

Context Chunk 3 (score: 0.798):
Source: BC_PIPA.txt
"When collecting personal information electronically,
organizations must ensure secure transmission protocols..."
```

---

### **STEP 6: Multi-Step RAG Analysis** (chain_of_thought.py:373-471)
**Location**: `ComplianceReasoning.multi_step_analysis()`

**CoT-Enhanced RAG Process**:

#### 6.1 Initial Broad Search
```
Step 1: Initial broad policy search
├─ Retrieved 3 relevant policy chunks
├─ Sources: PHIPA.txt, PIPEDA.txt, BC_PIPA.txt
└─ → Conclusion: Found 3 relevant passages
```

#### 6.2 Identify Gaps and Follow-up Queries
```python
# Analyze ticket for specific topics
if 'encryption' in ticket_lower:
    keywords_to_explore.append('encryption standards')
if 'consent' in ticket_lower:
    keywords_to_explore.append('consent requirements')
```

**For our example**:
- Detected keyword: 'encryption' ✓
- Follow-up query 1: "encryption standards"
- Follow-up query 2: "data retention requirements"

```
Step 2: Identifying gaps and performing follow-up queries
├─ Identified topics: encryption standards, data retention requirements
├─ ✓ Follow-up query 'encryption standards': 2 results
├─ ✓ Follow-up query 'data retention requirements': 2 results
└─ → Conclusion: Total context expanded to 7 passages
```

#### 6.3 Deduplication
```python
# Remove duplicate chunks based on text similarity
for text, metadata, score in all_context:
    text_normalized = text.strip().lower()[:200]
    if text_normalized not in seen_texts:
        unique_context.append((text, metadata, score))
```

```
Step 3: Deduplicating context
├─ Total passages retrieved: 7
├─ Duplicates removed: 2
├─ Unique passages: 5
└─ → Conclusion: Final context: 5 unique passages
```

**Multi-Step RAG Result**: 5 unique policy chunks + reasoning chain

---

### **STEP 7: Prompt Building** (prompt_templates.py:457-475)
**Location**: `build_cot_dev_ticket_prompt()`

**Constructs**:

```
[SYSTEM PROMPT - COT_SYSTEM_PROMPT]
You are a Canadian Privacy Compliance Assistant...
IMPORTANT - Chain of Thought Reasoning:
You MUST think step-by-step through problems:
1. Break down complex questions into smaller parts
2. Analyze each piece of information systematically
...

---

[USER PROMPT - COT_DEV_TICKET_PROMPT]
Development Ticket:
As a PM, I'm creating a ticket for storing chat messages between
users and healthcare providers. Does this data require encryption?
What technology measures are recommended for compliance?

Relevant Privacy Regulations:
[Context 1] Source: PHIPA.txt
Personal health information must be encrypted both at rest and in transit...

[Context 2] Source: PIPEDA.txt
Organizations must implement appropriate security safeguards...

[Context 3] Source: BC_PIPA.txt
When collecting personal information electronically...

[Context 4] Source: PHIPA.txt
Encryption standards should meet or exceed AES-256...

[Context 5] Source: PIPEDA.txt
Retention requirements for health information...

Your Task: Provide STEP-BY-STEP compliance guidance:

STEP 1: Understanding the Technical Requirement
- What system/feature is being built?
- What type of data will be processed?
- What is the user context?

STEP 2: Classification and Applicability
- Is this personal information? Personal health information?
- Which regulations apply?

[... continues with STEP 3-6 ...]
```

**Prompt Stats**:
- Length: ~2,500 characters
- Contains: System instructions + Context chunks + Step-by-step framework
- Temperature: 0.4, Max tokens: 800

---

### **STEP 8: LLM Generation** (ollama_client.py)
**Location**: `OllamaClient.generate()`

**Request to Ollama**:
```python
response = requests.post(
    'http://localhost:11434/api/generate',
    json={
        'model': 'gemma2:2b',
        'prompt': full_prompt,
        'stream': False,
        'options': {
            'temperature': 0.4,
            'max_tokens': 800
        }
    }
)
```

**LLM Processing**:
- Model: gemma2:2b (local inference)
- Reads prompt with system instructions + context + reasoning framework
- Generates step-by-step response following CoT template
- Returns structured compliance guidance

**Example LLM Response** (summarized):
```
STEP 1: Understanding the Technical Requirement
This system involves storing chat messages between users and healthcare
providers, which constitutes personal health information (PHI) under
Canadian privacy law...

STEP 2: Classification and Applicability
- Type: Personal Health Information (PHI)
- Regulations: PHIPA (Ontario), PIPEDA (federal), BC PIPA
- Sensitivity: HIGH

STEP 3: Analyzing Regulatory Requirements
PHIPA requires encryption of PHI both at rest and in transit.
PIPEDA mandates appropriate security safeguards proportionate to
sensitivity...

STEP 4: Technical Security Measures
Required encryption:
- At Rest: AES-256 encryption for database storage
- In Transit: TLS 1.3 for data transmission
- Access Controls: Role-based access (RBAC), MFA for admin access
- Logging: Audit logs for all access to PHI

STEP 5: Implementation Guidance
Recommended technologies:
- Database: PostgreSQL with pgcrypto extension or AWS RDS with encryption
- Transport: HTTPS with TLS 1.3, reject older protocols
- Key Management: AWS KMS or HashiCorp Vault
- Testing: Penetration testing, encryption verification

STEP 6: Risk Assessment and Best Practices
Privacy risks: Unauthorized access, data breach, improper retention
Best practices:
- Implement end-to-end encryption where feasible
- Regular security audits
- Data minimization - only store necessary information
- Clear retention policies with automated deletion
```

---

### **STEP 9: Response Assembly** (chatbot.py:700-709)
**Location**: `ChatBot.answer_dev_ticket()` return

**Returns Tuple**:
```python
return (
    response,          # LLM-generated text
    full_prompt,       # Complete prompt sent to LLM
    metadata,          # All context chunks + reasoning chains
    'dev_ticket'       # Message type
)
```

**Metadata Structure**:
```python
metadata = {
    'context_chunks': [
        ("Personal health information must be...", {'source': 'PHIPA.txt'}, 0.843),
        ("Organizations must implement...", {'source': 'PIPEDA.txt'}, 0.821),
        # ... 5 total chunks
    ],
    'ticket_type': 'development',
    'classification_reasoning': <ReasoningChain object>,  # Why it's a dev ticket
    'rag_reasoning': <ReasoningChain object>              # Multi-step RAG analysis
}
```

---

### **STEP 10: Display Results** (app.py:201-267)
**Location**: Streamlit UI result rendering

**Displays**:

#### Main Response
```
### Analysis Result
[LLM response text displayed in info box]
STEP 1: Understanding the Technical Requirement...
STEP 2: Classification and Applicability...
[... full 6-step response ...]
```

#### Expandable Sections

**🧠 Classification Reasoning** (Collapsed by default)
```
Complete Message Classification
Step 1: Scanning for actual PII patterns
  - ✗ Email pattern not found
  - ✗ Phone pattern not found
  ...
Final Conclusion: Development/Requirements Ticket
Confidence: HIGH
```

**🔍 Multi-Step RAG Analysis** (Collapsed by default)
```
Multi-Step Compliance Analysis
Step 1: Initial broad policy search
  - Retrieved 3 relevant policy chunks
  - Sources: PHIPA.txt, PIPEDA.txt, BC_PIPA.txt
Step 2: Identifying gaps and performing follow-up queries
  - Identified topics: encryption standards
  - ✓ Follow-up query 'encryption standards': 2 results
Step 3: Deduplicating context
  - Unique passages: 5
Final Conclusion: Multi-step analysis complete with 5 unique policy references
```

**🔧 View Prompt Used** (Collapsed by default)
```
[Full prompt text - 2,500 characters]
Prompt length: 2500 characters
```

**📚 Policy References** (Collapsed by default)
```
Compliance documents referenced (5 sources):

[1] PHIPA.txt (relevance: 0.8430)
  View excerpt 1 ▼
    Personal health information must be encrypted both at rest
    and in transit using industry-standard encryption methods...

[2] PIPEDA.txt (relevance: 0.8210)
  View excerpt 2 ▼
    Organizations must implement appropriate security safeguards,
    including technical measures such as encryption...

[... 3 more sources ...]
```

---

## Component Details

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Streamlit UI** | `app.py` | Web interface, user interaction |
| **ChatBot** | `src/chatbot.py` | Main orchestrator, routing logic |
| **PHI Detector** | `src/phi_detector.py` | Regex + NER for PII detection |
| **RAG System** | `src/rag_system.py` | Document loading, semantic search |
| **ChromaDB** | `./chroma_db/` | Vector database (100+ chunks) |
| **Ollama Client** | `src/ollama_client.py` | LLM inference client |
| **Chain of Thought** | `src/chain_of_thought.py` | Reasoning utilities |
| **Prompt Templates** | `src/prompt_templates.py` | System & user prompts |

### Message Types

| Type | Trigger Conditions | Handler | Example |
|------|-------------------|---------|---------|
| **pii_ticket** | 2+ PII patterns detected | `analyze_ticket()` | "User john@test.com (SSN: 123-45-6789) reports issue" |
| **dev_ticket** | 2+ dev keywords + question words | `answer_dev_ticket()` | "As a PM, building feature to store chat messages..." |
| **question** | Everything else | `answer_question()` | "What is PII under Canadian law?" |

### CoT Reasoning Components

| Reasoning Type | Purpose | Output |
|----------------|---------|--------|
| **Classification** | Explain why message classified as pii_ticket/dev_ticket/question | Step-by-step pattern analysis |
| **Risk Assessment** | Justify risk level (LOW/MEDIUM/HIGH/CRITICAL) | Multi-step risk evaluation |
| **Multi-Step RAG** | Document retrieval strategy and deduplication | Reasoning for context expansion |

---

## Data Flow Summary

```
User Input (Text)
    ↓
[1] Classification (Regex + Keywords + CoT)
    ↓
[2] Route to Handler (pii_ticket / dev_ticket / question)
    ↓
[3] RAG Query (Semantic search in ChromaDB)
    ↓
[4] Multi-Step Analysis (Follow-up queries + Dedup + CoT)
    ↓
[5] Prompt Building (System + Context + CoT Framework)
    ↓
[6] LLM Generation (Ollama gemma2:2b, local inference)
    ↓
[7] Response Assembly (Text + Metadata + Reasoning Chains)
    ↓
[8] Display (Streamlit UI with expandable sections)
```

---

## Technology Stack

- **Frontend**: Streamlit (Python web framework)
- **Backend**: Python 3.x
- **NLP**: spaCy (en_core_web_sm model)
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Vector DB**: ChromaDB (persistent storage)
- **LLM**: Ollama (gemma2:2b, local inference)
- **Reasoning**: Custom Chain-of-Thought implementation

---

## Key Features

1. **Automatic Classification**: Distinguishes between PII tickets, dev tickets, and questions
2. **Chain-of-Thought Reasoning**: Transparent step-by-step analysis
3. **Multi-Step RAG**: Iterative context expansion with follow-up queries
4. **Local LLM**: Privacy-preserving inference (no data sent to external APIs)
5. **Policy Grounding**: All responses backed by actual Canadian privacy regulations
6. **Explainability**: Full reasoning chains and prompt visibility

---

## Performance Characteristics

- **Classification**: ~50ms (regex + keyword matching)
- **RAG Query**: ~200ms per query (semantic search)
- **Multi-Step RAG**: ~600ms (initial + 2 follow-ups + dedup)
- **LLM Generation**: ~3-5s (local gemma2:2b inference)
- **Total Response Time**: ~4-6s end-to-end

---

## Example Outputs

For the development ticket example, the system:
- ✅ Correctly classifies as dev ticket (not PII ticket)
- ✅ Retrieves 5 unique policy references from 3 regulations
- ✅ Provides specific technical recommendations (AES-256, TLS 1.3, etc.)
- ✅ Shows complete reasoning chain for classification
- ✅ Documents multi-step RAG analysis process
- ✅ Enables full transparency with prompt visibility
