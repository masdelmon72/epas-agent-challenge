# 🛩️ EPAS Assistant - AI Agent for Aviation Safety

> **UiPath Specialist Coded Agent Challenge 2025**
> An AI-powered assistant specialized in European Plan for Aviation Safety (EPAS)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![UiPath SDK](https://img.shields.io/badge/UiPath-SDK-orange.svg)](https://docs.uipath.com)
[![LangChain](https://img.shields.io/badge/LangChain-RAG-green.svg)](https://langchain.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 📖 Overview

EPAS Assistant is a specialized AI agent that helps aviation safety professionals quickly find and understand information from the European Plan for Aviation Safety (EPAS 2024-2028) published by EASA.

### What It Does

- 🔍 **Semantic Search** across 3 comprehensive EPAS volumes
- 📚 **Precise Citations** with Volume, Section, and Page numbers
- 🔗 **Cross-References** related information across documents
- ✅ **Validates** safety compliance requirements
- 📊 **Confidence Scoring** for every answer

### Why It Matters

Aviation safety professionals need to:
- Navigate 1000+ pages of regulations, actions, and risks
- Find specific requirements quickly during audits
- Understand relationships between regulations and actions
- Ensure compliance with EASA standards

**EPAS Assistant reduces search time from hours to seconds.**

---

## 🎯 Key Features

### 1. Multi-Document RAG System
Search across three correlated EPAS volumes simultaneously:
- **Volume I**: Easy Access Rules for Standardisation
- **Volume II**: Safety Actions and Implementation
- **Volume III**: Safety Risk Portfolio

### 2. Domain-Specific Tools
Three specialized tools built for aviation safety:

```python
# Tool 1: Semantic Search
semantic_search_epas( 
query="What are maintenance requirements?", 
volume="I" # Optional filter
)

# Tool 2: Cross-Reference Finder
find_cross_references( 
section_id="CAT.GEN.MPA.210"
)

# Tool 3: Volume Information
get_volume_info(volume="II")
```

### 3. Intelligent Citation System
Every answer includes verifiable sources:

```
Answer: "Operators must implement a safety management system..."

Sources:
- Volume I, Section CAT.GEN.MPA.200, Page 118 (Score: 0.92)
- Volume II, Action SP-02.1, Page 45 (Score: 0.87)
```

---

## 🚀 Quick Start

### Prerequisites

```bash
- Ubuntu 22.04 (or similar Linux)
- Python 3.10+
- 8GB RAM minimum
- OpenAI API key
```

### Installation

```bash
#1. Clone repository
git clone https://github.com/your-repo/epas-agent-challenge.git
cd epas-agent-challenge

# 2. Create virtual environments
python3 -m venv venv
source venv/bin/activate

#3. Install dependencies
pip install -r requirements.txt

#4. Configure environment
cp .env.template .env
dwarf .env # Add your OPENAI_API_KEY
```

### Setup Knowledge Base

```bash
# Place EPAS PDF files in data/raw/:
# - volume_1_regulations.pdf
# - volume_2_actions.pdf
# - volume_3_safety_risk.pdf

# Process PDFs and create vector store (one-time, ~10 minutes)
python scripts/setup_knowledge_base.py
```

### Run the Agent

```bash
# Interactive mode
python scripts/run_agent.py

# Test mode
python scripts/test_rag.py
```

---

## 💻 Usage Examples

### Example 1: Basic Query

```python
User: "What are the strategic priorities in EPAS?"

Agent: The European Plan for Aviation Safety identifies five 
strategic priorities: 

1. Safety Risk Management 
2. Emerging Risks and Innovation 
3. Industry Maturity and Resilience 
4. Standardization and Oversight 
5. International Cooperation 

[Volume II, Section 2.1, Pages 12-15]

Confidence: 92%
Sources: 4
```

### Example 2: Filtered Search

```python
User: "vol:I What are crew training requirements?"

Agent: According to Volume I regulations: 

Operators must ensure flight crew members complete: 
- Initial training before operating duties 
- Recurrent training at intervals not exceeding 12 months 
- Conversion training for new aircraft types 

[Volume I, Section ORO.FC.220, Page 234] 
[Volume I, AMC1 ORO.FC.220, Page 235]

Confidence: 95%
Sources: 3 (all from Volume I)
```

### Example 3: Cross-Reference

```python
User: "Find cross-references for CAT.GEN.MPA.210"

Agent: Cross-references for CAT.GEN.MPA.210 (Carriage of weapons): 

Related regulations: 
- Volume I, Section CAT.GEN.MPA.200, Page 118 

Implementing actions: 
- Volume II, Action SEC-01.3, Page 67 

Associated risks: 
- Volume III, SRP SEC.2, Page 89

Confidence: 88%
```

---

## 🏗️ Architecture

```
┌──────────────────── ─────────────────────┐
│ User Interface │
│ (CLI / API / EPASApp) │
└────────────┬────────────────────────────┘
│ 
↓
┌──────────────────── ─────────────────────┐
│ UiPath SDK Agent Layer │
│ - Tool Selection │
│ - Query U
