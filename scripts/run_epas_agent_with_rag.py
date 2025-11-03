# scripts/run_epas_agent_with_rag.py

from src.agent.epas_agent import run_epas_agent
from src.rag.chain import EPASRAGChain  # usa la tua classe RAG locale

# =====================================================================
# DOMANDE EPAS REALI
# =====================================================================
EPAS_QUESTIONS = [
    "What are maintenance organization approval requirements?",
    "What is the procedure for safety checks on new equipment?",
    "Explain the compliance requirements for software updates.",
    "Describe the process for reporting operational incidents.",
    "Which approvals are required for critical maintenance tasks?",
    "What are the training requirements for crew members?"
]

# =====================================================================
# SCRIPT PRINCIPALE
# =====================================================================
if __name__ == "__main__":
    # Step 1 — inizializza RAG locale
    rag_chain = EPASRAGChain("data/vectorstore")  # percorso al tuo vectorstore

    # Step 2 — invia ogni domanda all'EPAS Agent
    for question in EPAS_QUESTIONS:
        print(f"\n🔹 Invio query all'EPAS Agent: {question}")

        # run_epas_agent recupera il contesto dal RAG e invia tutto al workflow RPA
        result = run_epas_agent(rag_chain, question)

        # Step 3 — stampa risultato
        print("\n📄 Risultato finale:")
        print(f"Query: {result['query']}")
        print(f"RAG Answer: {result['rag_answer']}")
        print(f"Agent Response: {result['agent_response']}")
