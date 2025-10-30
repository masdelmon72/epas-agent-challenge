# 🏛️ Architettura EPAS Agent - UiPath Challenge

## 1. OVERVIEW SISTEMA

### Obiettivo
Creare un agente specializzato EPAS (European Plan for Aviation Safety) che:
- Risponde a domande su aviation safety usando 3 volumi EASA
- Fornisce citazioni precise (volume, sezione, pagina)
- Valida compliance con regolamenti
- Cross-referenzia informazioni tra volumi

### Stack Tecnologico
- **Agent Framework**: UiPath SDK (Python)
- **RAG Framework**: LangChain
- **Vector Store**: FAISS
- **Embeddings**: sentence-transformers
- **LLM**: GPT-4 (via UiPath)
- **API**: FastAPI (per interfaccia)

---

## 2. ARCHITETTURA LAYERED

```
┌─────────────────────────────────────────────────┐
│           USER INTERFACE LAYER                  │
│  (EPASApp - Existing UI / REST API)            │
└────────────────┬────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────┐
│           AGENT ORCHESTRATION LAYER             │
│  ┌──────────────────────────────────────┐      │
│  │   UiPath SDK Agent                   │      │
│  │  - Query Understanding               │      │
│  │  - Tool Selection                    │      │
│  │  - Response Generation               │      │
│  └──────────────┬───────────────────────┘      │
└─────────────────┼───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│              TOOLS LAYER                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Semantic │  │  Cross   │  │  Safety  │     │
│  │  Search  │  │Reference │  │Validator │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
└───────┼─────────────┼─────────────┼────────────┘
        │             │             │
        ↓             ↓             ↓
┌─────────────────────────────────────────────────┐
│              RAG LAYER                          │
│  ┌──────────────────────────────────────┐      │
│  │   LangChain RAG System               │      │
│  │  ┌────────────┐  ┌────────────┐     │      │
│  │  │ Retriever  │→ │  Reranker  │     │      │
│  │  └──────┬─────┘  └─────┬──────┘     │      │
│  │         │               │            │      │
│  │         ↓               ↓            │      │
│  │  ┌─────────────────────────────┐    │      │
│  │  │   Context Builder           │    │      │
│  │  └──────────┬──────────────────┘    │      │
│  └─────────────┼────────────────────────┘      │
└────────────────┼────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────┐
│           KNOWLEDGE BASE LAYER                  │
│  ┌──────────────────────────────────────┐      │
│  │   FAISS Vector Store                 │      │
│  │  - Embeddings (384 dim)              │      │
│  │  - Metadata (vol, section, page)     │      │
│  │  - ~3000-5000 chunks                 │      │
│  └──────────────────────────────────────┘      │
└─────────────────────────────────────────────────┘
                 ↑
                 │
┌─────────────────────────────────────────────────┐
│           DATA PROCESSING LAYER                 │
│  Volume I, II, III PDFs → Chunking → Embedding │
└─────────────────────────────────────────────────┘
```

---

## 3. COMPONENTI DETTAGLIATI

### 3.1 Data Processing Pipeline

```python
# Processo:
# 1. PDF Loading con metadata
# 2. Intelligent Chunking
# 3. Embedding Generation
# 4. Vector Store Creation

Pipeline:
PDF → Text Extraction → Section Detection → 
      Chunking (500 tokens, 50 overlap) → 
      Metadata Enrichment → Embedding → FAISS Index
```

**Metadata Structure**:
```json
{
  "volume": "I/II/III",
  "volume_title": "Easy Access Rules...",
  "section": "AMC1 CAT.GEN.MPA.210",
  "page": 125,
  "chunk_id": "vol1_s42_p125_c3",
  "priority_level": "strategic/operational/safety",
  "document_type": "regulation/action/risk"
}
```

### 3.2 RAG System

**Retrieval Strategy**:
1. **Semantic Search**: Query embedding → Top-k chunks (k=10)
2. **Reranking**: Cross-encoder per relevance
3. **Filtering**: Per volume/section se specificato
4. **Context Building**: Max 3000 tokens di contesto

**Retriever Configuration**:
```python
retriever = VectorStoreRetriever(
    vectorstore=faiss_store,
    search_type="similarity_score_threshold",
    search_kwargs={
        "k": 10,
        "score_threshold": 0.7
    }
)
```

### 3.3 Agent Tools

#### Tool 1: Semantic Search
```python
@tool
def semantic_search_epas(query: str, volume: Optional[str] = None) -> str:
    """
    Cerca semanticamente nei documenti EPAS.
    
    Args:
        query: Domanda dell'utente
        volume: Filtra per volume (I, II, III) - opzionale
    
    Returns:
        Contesto rilevante con citazioni
    """
```

#### Tool 2: Cross-Reference Finder
```python
@tool
def find_cross_references(section_id: str) -> str:
    """
    Trova riferimenti incrociati tra volumi.
    
    Args:
        section_id: ID sezione (es. "CAT.GEN.MPA.210")
    
    Returns:
        Sezioni correlate in altri volumi
    """
```

#### Tool 3: Safety Validator
```python
@tool
def validate_safety_compliance(
    action: str, 
    priority: str
) -> str:
    """
    Valida compliance con EPAS safety risk portfolio.
    
    Args:
        action: Azione proposta
        priority: Livello priorità (strategic/operational)
    
    Returns:
        Analisi compliance e raccomandazioni
    """
```

### 3.4 UiPath Agent Configuration

```python
from uipath import Agent, Tool

agent = Agent(
    name="EPASAssistant",
    description="""AI assistant specializzato in European Plan 
    for Aviation Safety (EPAS). Esperto in regolamenti aviation 
    safety EASA, azioni implementative e safety risk portfolio.""",
    
    tools=[
        semantic_search_tool,
        cross_reference_tool,
        safety_validator_tool
    ],
    
    llm_config={
        "model": "gpt-4",
        "temperature": 0.2,  # Bassa per precisione
        "max_tokens": 2000
    },
    
    system_prompt=EPAS_SYSTEM_PROMPT
)
```

### 3.5 Response Format

```json
{
  "answer": "HTML formatted response",
  "sources": [
    {
      "volume": "I",
      "section": "AMC1 CAT.GEN.MPA.210",
      "page": 125,
      "relevance_score": 0.92,
      "excerpt": "..."
    }
  ],
  "confidence": 0.87,
  "related_topics": ["topic1", "topic2"],
  "cross_references": ["Vol II - Section X", "..."]
}
```

---

## 4. SYSTEM PROMPTS

### Agent System Prompt
```
You are AgentAssistantEPAS, an AI assistant specialized in the 
European Plan for Aviation Safety (EPAS 2024-2028) published by EASA.

You have access to three key reference documents:
1. Volume I – Regulations and Implementing Rules (IMM, IMT, IST, IES)
2. Volume II – Actions and Implementation (Safety Actions)  
3. Volume III – Safety Risk Portfolio (SRPs)

YOUR MAIN TASKS:
- Answer user questions about strategic priorities, actions, and safety risks
- Provide structured answers with clear source citations (Vol, Section, Page)
- Cross-reference between volumes when applicable
- Validate safety compliance according to EASA terminology

RESPONSE STRUCTURE:
1. Direct answer to the question
2. Source citations in format [Vol X, Section Y, p. Z]
3. Cross-references if applicable
4. Related topics or actions

IMPORTANT:
- Always cite exact sources
- Use EASA terminology (IMM, IST, SRP, etc.)
- Be concise but comprehensive
- If uncertain, specify which volume might contain the information
```

---

## 5. PERFORMANCE OPTIMIZATION

### Embedding Strategy
- **Model**: all-MiniLM-L6-v2 (22MB, fast)
- **Dimension**: 384 (bilanciato)
- **Batch Processing**: 32 chunks per batch
- **Caching**: Embeddings salvati su disco

### Vector Search
- **Index Type**: FAISS IndexFlatIP (inner product)
- **Search**: Approximate nearest neighbor
- **Threshold**: 0.7 similarity score
- **Max Results**: Top 10, reranked to top 5

### Memory Management (8GB RAM)
- Lazy loading documenti
- Streaming per PDF grandi
- Vector store su disco (mmap)
- Batch processing

---

## 6. DEPLOYMENT & TESTING

### Local Development
```bash
# 1. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Prepare knowledge base
python scripts/setup_knowledge_base.py

# 3. Test RAG
python scripts/test_rag.py

# 4. Run agent
python scripts/run_agent.py
```

### API Endpoint
```
POST /api/v1/query
{
  "question": "What are the strategic priorities?",
  "volume_filter": null,  # Optional: "I", "II", "III"
  "include_cross_refs": true
}
```

---

## 7. EVALUATION METRICS

Per la challenge:
- **Accuracy**: Correttezza risposte vs. documenti
- **Citation Precision**: Accuratezza citazioni
- **Response Time**: < 5 secondi
- **Context Relevance**: Score > 0.8
- **User Satisfaction**: Feedback qualitativo

---

## 8. DIFFERENTIATORI PER CHALLENGE

✅ **Multi-Document RAG**: 3 volumi correlati  
✅ **Intelligent Chunking**: Rispetta struttura documenti  
✅ **Precise Citations**: Volume + Section + Page  
✅ **Cross-Referencing**: Collegamenti automatici  
✅ **Domain-Specific**: Aviation safety terminology  
✅ **UiPath SDK**: Agente nativo, non wrapper  
✅ **LangChain**: RAG chain professionale  
✅ **Scalable**: Architettura modulare  

---

**Next Steps**: Implementazione codice per ogni componente
