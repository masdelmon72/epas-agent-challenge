# scripts/run_addition_variables.py

import os
import time
from dotenv import load_dotenv
from uipath import UiPath

# =====================================================================
# CONFIGURAZIONE
# =====================================================================
load_dotenv()

UIPATH_URL = os.getenv("UIPATH_URL")
CLIENT_ID = os.getenv("UIPATH_CLIENT_ID")
CLIENT_SECRET = os.getenv("UIPATH_CLIENT_SECRET")

PROCESS_NAME = "RPA.Workflow"  # Nome del workflow pubblicato
FOLDER_PATH = "Shared"                  # Modern Folder dove si trova il workflow
INPUT_ARGS = {"in_C": 4, "in_D": 4}     # Esempio input arguments
TIMEOUT = 120                            # Timeout polling job in secondi

print("UIPATH_URL:", UIPATH_URL)
print("CLIENT_ID:", CLIENT_ID)
print("CLIENT_SECRET:", CLIENT_SECRET)

# =====================================================================
# AUTENTICAZIONE
# =====================================================================
try:
    print("🔑 Autenticazione su UiPath Cloud...")
    sdk = UiPath(
        base_url=UIPATH_URL,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scope="OR.Jobs OR.Execution",
        debug=True
    )
    print("✅ Autenticazione riuscita")
except Exception as e:
    print(f"❌ Errore autenticazione: {e}")
    exit(1)

# =====================================================================
# AVVIO WORKFLOW
# =====================================================================
try:
    print(f"🚀 Avvio workflow '{PROCESS_NAME}' con {INPUT_ARGS} ...")
    job = sdk.processes.invoke(
        PROCESS_NAME,
        input_arguments=INPUT_ARGS,
        folder_path=FOLDER_PATH
    )

    job_id = job.id
    print(f"📄 Job avviato. Job ID: {job_id}")
    print("Stato iniziale:", job.state)

except Exception as e:
    print(f"❌ Errore avvio workflow: {e}")
    exit(1)

# =====================================================================
# POLLING DELLO STATO DEL JOB
# =====================================================================
start = time.time()
while time.time() - start < TIMEOUT:
    try:
        job_status = sdk.jobs.get_job(job_id)
        state = job_status.state
        print("⏳ Job state:", state)

        if state == "Successful":
            output = job_status.output_arguments or {}
            print("✅ Job completato con successo!")
            print("Output:", output)
            break

        elif state == "Faulted":
            print("❌ Job Faulted")
            break

    except Exception as e:
        print("⚠️ Errore polling job:", e)

    time.sleep(3)
else:
    print(f"⏱ Timeout: il job non è completato entro {TIMEOUT} secondi")
    

