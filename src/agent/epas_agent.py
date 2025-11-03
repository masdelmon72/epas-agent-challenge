# src/agent/epas_agent.py

import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

try:
    from uipath import OrchestratorClient
    UIPATH_AVAILABLE = True
except ImportError:
    UIPATH_AVAILABLE = False
    print("⚠️ UiPath SDK non installato — modalità simulazione attiva.")


# =====================================================================
# CONFIG DA ENV
# =====================================================================
UIPATH_URL = os.getenv("UIPATH_URL")
UIPATH_CLIENT_ID = os.getenv("UIPATH_CLIENT_ID")
UIPATH_CLIENT_SECRET = os.getenv("UIPATH_CLIENT_SECRET")
UIPATH_RPA_WORKFLOW = os.getenv("UIPATH_RPA_WORKFLOW", "EPAS_Agent_Bridge")
FOLDER_PATH = os.getenv("UIPATH_FOLDER_PATH", "Shared")
POLL_INTERVAL = 3
TIMEOUT = 120


# =====================================================================
# CLASSE: UiPathAgentClient
# =====================================================================
class UiPathAgentClient:
    """Lancia un workflow RPA ponte su UiPath che invoca il tuo Agent locale."""

    def __init__(self):
        self.available = UIPATH_AVAILABLE
        self.sdk = None

        if self.available:
            try:
                print("🔑 Autenticazione su UiPath Cloud...")
                self.sdk = OrchestratorClient(
                    orchestrator_url=UIPATH_URL,
                    client_id=UIPATH_CLIENT_ID,
                    client_secret=UIPATH_CLIENT_SECRET,
                    scope="OR.Execution OR.Jobs",
                    debug=True
                )
                self.sdk.authenticate()
                print("✅ Autenticazione riuscita")
            except Exception as e:
                print(f"❌ Errore autenticazione: {e}")
                self.available = False

    def call_agent(self, query: str, context: str) -> dict:
        if not self.available:
            return self._simulate_agent(query, context)

        input_arguments = {
            "in_query": query,
            "in_context": context
        }

        try:
            # Avvio workflow ponte
            print(f"🚀 Avvio workflow '{UIPATH_RPA_WORKFLOW}' con {input_arguments} ...")
            job = self.sdk.jobs.start_process(
                process_name=UIPATH_RPA_WORKFLOW,
                input_arguments=input_arguments,
                folder_path=FOLDER_PATH
            )

            job_id = job.id
            print(f"📄 Job avviato. Job ID: {job_id}, Stato iniziale: {job.state}")

            # Polling job
            elapsed = 0
            while elapsed < TIMEOUT:
                jobs = self.sdk.jobs.get_jobs(folder_path=FOLDER_PATH)
                current_job = next((j for j in jobs if j.id == job_id), None)

                if current_job:
                    state = current_job.state
                    if state == "Successful":
                        output = getattr(current_job, "output_arguments", {}) or {}
                        return {
                            "status": "success",
                            "job_id": job_id,
                            "response_text": output.get("out_response_text", ""),
                            "response_html": output.get("out_response_html", ""),
                            "duration": elapsed
                        }
                    elif state == "Faulted":
                        return {"status": "error", "job_id": job_id, "error": "Job Faulted"}

                    print(f"⏳ Job state: {state} ({elapsed}s)")
                else:
                    print(f"⏳ Job ID {job_id} non ancora presente nella lista dei jobs")

                time.sleep(POLL_INTERVAL)
                elapsed += POLL_INTERVAL

            return {"status": "timeout", "error": f"Job non completato entro {TIMEOUT}s"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _simulate_agent(self, query: str, context: str) -> dict:
        """Simulazione in assenza di UiPath SDK."""
        print("🎭 Simulazione Agent attiva...")
        time.sleep(2)
        return {
            "status": "success",
            "job_id": f"demo-{int(time.time())}",
            "response_text": "Demo Agent Response",
            "response_html": f"<p>Query: {query}</p><p>Context: {context[:250]}...</p>",
            "duration": 2.0
        }


# =====================================================================
# FUNZIONE PUBBLICA
# =====================================================================
def run_epas_agent(rag_chain, query: str) -> dict:
    """
    Esegue pipeline completa:
      1. Recupera contesto dal RAG locale
      2. Passa query + contesto all'Agent tramite workflow RPA
    """
    print(f"\n🔹 Esecuzione EPAS Agent per query: {query}")

    # Step 1 — Recupero contesto dal RAG
    rag_result = rag_chain.query(query)

    # Step 2 — Invio a UiPath Agent (workflow ponte)
    agent_client = UiPathAgentClient()
    agent_result = agent_client.call_agent(
        query=query,
        context=rag_result["answer"]
    )

    # Step 3 — Output combinato
    return {
        "query": query,
        "rag_answer": rag_result["answer"],
        "agent_response": agent_result
    }
