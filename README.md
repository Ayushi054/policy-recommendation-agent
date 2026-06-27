# 🏛️ AI-Based Government Policy & Scheme Recommendation System

An intelligent multi-agent system that analyzes existing government schemes, identifies policy gaps, and generates data-driven policy recommendations for Indian policymakers.

## 🎯 Problem Statement

India has 1,000+ central and state government schemes, yet millions remain underserved due to:
- **Policy Gaps:** Many demographics lack adequate scheme coverage
- **Duplication:** Multiple ministries launch overlapping schemes
- **Poor Implementation:** Lack of data-driven monitoring and feedback loops

## 💡 Solution

An AI agent system built on **Google ADK 2.0** that:
1. Collects user context via Human-in-the-Loop interaction
2. Screens input for security threats and PII
3. Analyzes policy gaps using LLM
4. Generates structured policy proposals
5. Routes proposals for human review and approval

## 🏗️ Architecture

```
User Input
    ↓
[Node 1] collect_user_profile (HITL)
    → Collects: Role, State, Sector, Problem Statement
    ↓
[Node 2] security_check
    → PII Redaction (Aadhaar, PAN, Phone)
    → Prompt Injection Defense
    ↓
[Node 3] analyze_gaps (LLM - Groq/Gemini)
    → Gap Analysis Report
    → Identifies underserved populations
    ↓
[Node 4] generate_recommendation (LLM - Groq/Gemini)
    → Structured Policy Proposal
    → Budget, Implementation Plan, KPIs
    ↓
[Node 5] human_review (HITL)
    → Policymaker Approve/Reject
    ↓
[Node 6] finalize_output
    → Final Policy Document + Next Steps
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Agent Framework | Google ADK 2.0 |
| LLM | Groq (llama-3.3-70b-versatile) / Gemini |
| Development IDE | Google Antigravity |
| MCP Server | Custom MyScheme MCP |
| Agent Skills | 3 Custom Skills |
| Security | PII Redaction + Prompt Injection Defense |

## ✨ Key Features

### 🤖 Multi-Agent Graph Workflow (ADK 2.0)
- 6-node graph workflow using ADK 2.0 Workflow API
- Directed edges with state management via EventActions
- ResumabilityConfig for multi-turn conversations
- **Robust State Persistence:** Directly mutates `ctx.state` to ensure reliable recovery upon execution resume, resolving multi-turn interruption bugs.

### 🔒 Security Features
- **PII Redaction:** Aadhaar, PAN, Phone numbers automatically redacted
- **Prompt Injection Defense:** Detects and blocks adversarial inputs
- **LLM Bypass:** Malicious inputs routed directly to human review

### 👥 Human-in-the-Loop (HITL)
- **Node 1:** Collects user profile interactively
- **Node 5:** Policymaker reviews and approves/rejects proposals

### 🔌 MCP Server
Custom MCP server for Indian government scheme data:
- `search_schemes` — Search by sector/state/beneficiary
- `get_scheme_details` — Get scheme information
- `identify_gaps` — Identify policy gaps

### 📚 Agent Skills
Three custom Antigravity skills:
- `policy-gap-analyzer` — Gap analysis instructions
- `policy-recommendation-generator` — Proposal generation
- `scheme-data-fetcher` — Data retrieval guidelines

## 🚀 Setup Instructions

### Prerequisites
- Python 3.11+
- uv package manager
- Groq API key (free at console.groq.com)

### Installation

```bash
# Clone the repository
git clone https://github.com/Ayushi054/policy-recommendation-agent.git
cd policy-recommendation-agent

# Install dependencies
uv sync

# Setup environment
cp .env.example .env
# Add your GROQ_API_KEY to .env file
```

### Running the Agent

```bash
# Start the ADK playground
uv run adk web app --host 127.0.0.1 --port 8082

# Open in browser
# http://127.0.0.1:8082/dev-ui/?app=app
```

### Testing

```bash
# Run tests
uv run pytest

# Example query to try:
# "I want to analyze policy gaps in Maharashtra for the education sector"
```

## 📁 Project Structure

```
policy-recommendation-agent/
├── app/
│   └── agent.py              # Main ADK 2.0 workflow
├── mcp_server/
│   └── myscheme_mcp.py       # MCP Server for scheme data
├── .agents/
│   └── skills/
│       ├── policy-gap-analyzer/
│       │   └── SKILL.md
│       ├── policy-recommendation-generator/
│       │   └── SKILL.md
│       └── scheme-data-fetcher/
│           └── SKILL.md
├── tests/
│   └── integration/
├── .env.example              # Environment variables template
├── pyproject.toml
└── README.md
```

## 🎯 Example Output

**Input:** Policy gaps in Maharashtra, Education sector

**Output — "Shiksha Sampark" (शिक्षा संपर्क)**
- Ministry: Ministry of Education
- Budget: ₹500 Crore
- Beneficiaries: 2 million students
- 3-phase implementation plan
- KPIs and success metrics

## 🔄 Switching LLM Backend

```python
# In app/agent.py - switch between Groq and Gemini

# Groq (current - free)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Gemini (when quota available)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
```

## 📊 Competition Track

**Agents for Good** — Helping Indian policymakers design better schemes for citizens

## 🙏 Acknowledgements

- Google ADK 2.0
- Google Antigravity IDE
- Kaggle 5-Day AI Agents Course
- MyScheme Portal (myscheme.gov.in)
- data.gov.in