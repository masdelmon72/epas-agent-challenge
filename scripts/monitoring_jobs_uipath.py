"""
UiPath Job Monitor & Analytics
Sistema di monitoraggio e analisi per job UiPath Orchestrator
"""

# ============================================================================
# PARTE 1: IMPORT E CONFIGURAZIONE
# ============================================================================

print("=== UiPath Job Monitor - Inizializzazione ===\n")

import os
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from collections import defaultdict
import pandas as pd

# Import per visualizzazione
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOT_AVAILABLE = True
except ImportError:
    PLOT_AVAILABLE = False
    print("⚠ Matplotlib/Seaborn non disponibili - grafici disabilitati")

# Import UiPath
try:
    import uipath
    UIPATH_AVAILABLE = True
    print("✓ UiPath SDK disponibile")
except ImportError:
    UIPATH_AVAILABLE = False
    print("⚠ UiPath SDK non disponibile - modalità demo")

print()

# ============================================================================
# PARTE 2: CONFIGURAZIONE CREDENZIALI
# ============================================================================

from google.colab import userdata

# Carica credenziali UiPath
try:
    UIPATH_CLIENT_ID = userdata.get('UIPATH_CLIENT_ID')
    UIPATH_CLIENT_SECRET = userdata.get('UIPATH_CLIENT_SECRET')
    UIPATH_TENANT_NAME = userdata.get('UIPATH_TENANT_NAME')
    UIPATH_ORGANIZATION_ID = userdata.get('UIPATH_ORGANIZATION_ID')
    
    # Opzionali
    try:
        UIPATH_FOLDER_ID = userdata.get('UIPATH_FOLDER_ID')
    except:
        UIPATH_FOLDER_ID = None
    
    print("✓ Credenziali UiPath caricate")
    
except Exception as e:
    print(f"✗ Errore caricamento credenziali: {e}")
    print("Aggiungi le credenziali nei Secrets di Colab")
    UIPATH_AVAILABLE = False

print()

# ============================================================================
# PARTE 3: UIPATH CLIENT AVANZATO
# ============================================================================

class UiPathMonitor:
    """Client avanzato per monitoraggio UiPath Orchestrator"""
    
    def __init__(self):
        self.available = UIPATH_AVAILABLE
        self.client = None
        self.authenticated = False
        
        if self.available:
            try:
                self._authenticate()
            except Exception as e:
                print(f"✗ Errore autenticazione: {e}")
                self.available = False
    
    def _authenticate(self):
        """Autentica il client con UiPath Cloud"""
        try:
            # Inizializza client
            self.client = uipath.Client()
            
            # Autentica
            self.client.authenticate(
                client_id=UIPATH_CLIENT_ID,
                client_secret=UIPATH_CLIENT_SECRET,
                tenant_name=UIPATH_TENANT_NAME,
                organization_id=UIPATH_ORGANIZATION_ID
            )
            
            self.authenticated = True
            print("✓ Autenticazione UiPath completata")
            
        except Exception as e:
            raise Exception(f"Errore autenticazione: {e}")
    
    def get_jobs(self, 
                 status: Optional[str] = None,
                 days_back: int = 7,
                 folder_id: Optional[str] = None) -> List[Dict]:
        """Ottiene lista job con filtri"""
        if not self.available:
            return self._get_demo_jobs()
        
        try:
            # Calcola date
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Parametri filtro
            filter_params = {
                'startTime': start_date.isoformat(),
                'endTime': end_date.isoformat()
            }
            
            if status:
                filter_params['state'] = status
            
            if folder_id or UIPATH_FOLDER_ID:
                filter_params['folderId'] = folder_id or UIPATH_FOLDER_ID
            
            # Recupera jobs
            jobs = self.client.jobs.get_jobs(**filter_params)
            
            # Converti in dict
            jobs_list = []
            for job in jobs:
                jobs_list.append({
                    'id': job.id,
                    'key': job.key,
                    'state': job.state,
                    'process_name': job.release_name,
                    'start_time': job.start_time,
                    'end_time': job.end_time,
                    'creation_time': job.creation_time,
                    'robot': job.robot_name,
                    'input_arguments': job.input_arguments,
                    'output_arguments': job.output_arguments,
                    'info': job.info
                })
            
            return jobs_list
            
        except Exception as e:
            print(f"✗ Errore recupero jobs: {e}")
            return []
    
    def get_job_details(self, job_id: str) -> Dict:
        """Ottiene dettagli completi di un job"""
        if not self.available:
            return self._get_demo_job_detail(job_id)
        
        try:
            job = self.client.jobs.get_job(job_id)
            
            return {
                'id': job.id,
                'key': job.key,
                'state': job.state,
                'process_name': job.release_name,
                'start_time': job.start_time,
                'end_time': job.end_time,
                'duration': self._calculate_duration(job.start_time, job.end_time),
                'robot': job.robot_name,
                'machine': job.host_machine_name,
                'input_arguments': job.input_arguments,
                'output_arguments': job.output_arguments,
                'info': job.info,
                'execution_logs': self._get_job_logs(job_id)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_job_logs(self, job_id: str) -> List[Dict]:
        """Ottiene i log di un job"""
        try:
            logs = self.client.logs.get_logs(job_key=job_id)
            return [{'message': log.message, 'level': log.level, 'timestamp': log.time_stamp} for log in logs]
        except:
            return []
    
    def _calculate_duration(self, start: str, end: str) -> float:
        """Calcola durata in secondi"""
        if not start or not end:
            return 0
        try:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            return (end_dt - start_dt).total_seconds()
        except:
            return 0
    
    def get_processes(self) -> List[Dict]:
        """Ottiene lista processi disponibili"""
        if not self.available:
            return self._get_demo_processes()
        
        try:
            releases = self.client.releases.get_releases()
            
            processes = []
            for release in releases:
                processes.append({
                    'name': release.name,
                    'key': release.key,
                    'version': release.process_version,
                    'description': release.description,
                    'environment': release.environment_name
                })
            
            return processes
            
        except Exception as e:
            print(f"✗ Errore recupero processi: {e}")
            return []
    
    def start_job(self, process_name: str, input_args: Dict = None) -> Dict:
        """Avvia un nuovo job"""
        if not self.available:
            return {'status': 'demo', 'message': 'Modalità demo attiva'}
        
        try:
            job = self.client.jobs.start(
                process_name=process_name,
                input_arguments=input_args or {}
            )
            
            return {
                'status': 'success',
                'job_id': job.id,
                'job_key': job.key,
                'process': process_name,
                'start_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def stop_job(self, job_id: str) -> Dict:
        """Ferma un job in esecuzione"""
        if not self.available:
            return {'status': 'demo', 'message': 'Modalità demo attiva'}
        
        try:
            self.client.jobs.stop(job_id)
            return {'status': 'success', 'job_id': job_id}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _get_demo_jobs(self) -> List[Dict]:
        """Dati demo per testing"""
        return [
            {
                'id': 'demo-1',
                'key': 'demo-key-1',
                'state': 'Successful',
                'process_name': 'AgentAssistantEpas',
                'start_time': datetime.now().isoformat(),
                'end_time': (datetime.now() + timedelta(seconds=45)).isoformat(),
                'robot': 'DemoRobot',
                'input_arguments': {'query': 'What is Part-145?'},
                'output_arguments': {'response': 'Part-145 is...'}
            }
        ]
    
    def _get_demo_processes(self) -> List[Dict]:
        """Processi demo"""
        return [
            {
                'name': 'AgentAssistantEpas',
                'key': 'epas-agent-1',
                'version': '1.0',
                'description': 'EPAS Agent Assistant',
                'environment': 'Production'
            }
        ]
    
    def _get_demo_job_detail(self, job_id: str) -> Dict:
        """Dettaglio job demo"""
        return {
            'id': job_id,
            'state': 'Successful',
            'process_name': 'AgentAssistantEpas',
            'duration': 45.5,
            'robot': 'DemoRobot',
            'input_arguments': {'query': 'test'},
            'output_arguments': {'response': 'test response'}
        }

# Inizializza monitor
monitor = UiPathMonitor()
print()

# ============================================================================
# PARTE 4: ANALYTICS CLASS
# ============================================================================

class JobAnalytics:
    """Analisi e statistiche sui job UiPath"""
    
    def __init__(self, monitor: UiPathMonitor):
        self.monitor = monitor
    
    def get_summary(self, days_back: int = 7) -> Dict:
        """Genera summary statistiche"""
        jobs = self.monitor.get_jobs(days_back=days_back)
        
        if not jobs:
            return {'error': 'Nessun job trovato'}
        
        # Calcola statistiche
        total = len(jobs)
        by_status = defaultdict(int)
        by_process = defaultdict(int)
        durations = []
        
        for job in jobs:
            by_status[job['state']] += 1
            by_process[job['process_name']] += 1
            
            if job.get('start_time') and job.get('end_time'):
                duration = self.monitor._calculate_duration(
                    job['start_time'], 
                    job['end_time']
                )
                if duration > 0:
                    durations.append(duration)
        
        summary = {
            'period_days': days_back,
            'total_jobs': total,
            'by_status': dict(by_status),
            'by_process': dict(by_process),
            'success_rate': (by_status.get('Successful', 0) / total * 100) if total > 0 else 0,
            'avg_duration': sum(durations) / len(durations) if durations else 0,
            'min_duration': min(durations) if durations else 0,
            'max_duration': max(durations) if durations else 0
        }
        
        return summary
    
    def get_process_stats(self, process_name: str, days_back: int = 30) -> Dict:
        """Statistiche per un processo specifico"""
        jobs = self.monitor.get_jobs(days_back=days_back)
        
        # Filtra per processo
        process_jobs = [j for j in jobs if j['process_name'] == process_name]
        
        if not process_jobs:
            return {'error': f'Nessun job trovato per {process_name}'}
        
        # Statistiche
        total = len(process_jobs)
        successful = sum(1 for j in process_jobs if j['state'] == 'Successful')
        failed = sum(1 for j in process_jobs if j['state'] == 'Faulted')
        
        return {
            'process': process_name,
            'period_days': days_back,
            'total_executions': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'failure_rate': (failed / total * 100) if total > 0 else 0
        }
    
    def export_to_dataframe(self, days_back: int = 7) -> pd.DataFrame:
        """Esporta jobs in DataFrame pandas"""
        jobs = self.monitor.get_jobs(days_back=days_back)
        
        if not jobs:
            return pd.DataFrame()
        
        # Prepara dati
        data = []
        for job in jobs:
            duration = self.monitor._calculate_duration(
                job.get('start_time', ''),
                job.get('end_time', '')
            )
            
            data.append({
                'Job ID': job['id'],
                'Process': job['process_name'],
                'Status': job['state'],
                'Robot': job.get('robot', 'N/A'),
                'Start Time': job.get('start_time', 'N/A'),
                'Duration (s)': duration
            })
        
        return pd.DataFrame(data)
    
    def plot_job_distribution(self, days_back: int = 7):
        """Visualizza distribuzione job per status"""
        if not PLOT_AVAILABLE:
            print("⚠ Matplotlib non disponibile")
            return
        
        summary = self.get_summary(days_back)
        
        if 'error' in summary:
            print(summary['error'])
            return
        
        # Crea grafico
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Status distribution
        statuses = list(summary['by_status'].keys())
        counts = list(summary['by_status'].values())
        
        colors = ['#28a745' if s == 'Successful' else '#dc3545' if s == 'Faulted' else '#ffc107' 
                  for s in statuses]
        
        ax1.bar(statuses, counts, color=colors)
        ax1.set_title(f'Job Distribution by Status ({days_back} days)')
        ax1.set_xlabel('Status')
        ax1.set_ylabel('Count')
        ax1.grid(axis='y', alpha=0.3)
        
        # Process distribution
        processes = list(summary['by_process'].keys())
        process_counts = list(summary['by_process'].values())
        
        ax2.barh(processes, process_counts, color='#007bff')
        ax2.set_title('Job Distribution by Process')
        ax2.set_xlabel('Count')
        ax2.grid(axis='x', alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        # Print summary
        print(f"\n📊 Summary Statistics:")
        print(f"  • Total Jobs: {summary['total_jobs']}")
        print(f"  • Success Rate: {summary['success_rate']:.1f}%")
        print(f"  • Avg Duration: {summary['avg_duration']:.1f}s")

# Inizializza analytics
analytics = JobAnalytics(monitor)
print("✓ Analytics engine pronto\n")

# ============================================================================
# PARTE 5: EPAS AGENT INTEGRATION
# ============================================================================

class EPASAgentIntegration:
    """Integrazione specifica per Agent Assistant EPAS"""
    
    def __init__(self, monitor: UiPathMonitor):
        self.monitor = monitor
        self.agent_process_name = "AgentAssistantEpas"
    
    def execute_epas_query(self, query: str, timeout: int = 60) -> Dict:
        """Esegue query tramite Agent EPAS e attende risposta"""
        print(f"🔍 Esecuzione query EPAS: '{query}'\n")
        
        # Prepara input
        input_args = {
            "query": query,
            "format": "html"  # Per Rich Text rendering
        }
        
        # Avvia job
        start_result = self.monitor.start_job(
            self.agent_process_name,
            input_args
        )
        
        if start_result['status'] != 'success':
            return {
                'status': 'error',
                'error': start_result.get('message', 'Unknown error')
            }
        
        job_id = start_result['job_id']
        print(f"✓ Job avviato: {job_id}")
        print("⏳ Attendo completamento...")
        
        # Polling per attendere completamento
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            job_details = self.monitor.get_job_details(job_id)
            
            state = job_details.get('state', 'Unknown')
            
            if state == 'Successful':
                print(f"✅ Job completato con successo!")
                
                # Estrai risposta
                output = job_details.get('output_arguments', {})
                response_html = output.get('response', output.get('html_response', ''))
                
                return {
                    'status': 'success',
                    'job_id': job_id,
                    'query': query,
                    'response_html': response_html,
                    'duration': job_details.get('duration', 0)
                }
            
            elif state == 'Faulted':
                print(f"❌ Job fallito")
                return {
                    'status': 'error',
                    'job_id': job_id,
                    'error': job_details.get('info', 'Job failed')
                }
            
            elif state in ['Pending', 'Running']:
                print(f"  ⏳ Status: {state}...")
                time.sleep(5)
            
            else:
                print(f"  ⚠ Status sconosciuto: {state}")
                time.sleep(5)
        
        # Timeout
        print(f"⏱ Timeout raggiunto ({timeout}s)")
        return {
            'status': 'timeout',
            'job_id': job_id,
            'message': f'Job non completato entro {timeout}s'
        }
    
    def format_html_response(self, html: str) -> str:
        """Formatta risposta HTML per visualizzazione"""
        from IPython.display import HTML, display
        
        # Wrappa in styled container
        styled_html = f"""
        <div style="
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            background: #f9f9f9;
            font-family: Arial, sans-serif;
            max-width: 800px;
        ">
            {html}
        </div>
        """
        
        display(HTML(styled_html))
        return html
    
    def get_epas_history(self, days_back: int = 7) -> List[Dict]:
        """Ottiene cronologia query EPAS"""
        jobs = self.monitor.get_jobs(days_back=days_back)
        
        # Filtra solo job EPAS
        epas_jobs = [j for j in jobs if j['process_name'] == self.agent_process_name]
        
        history = []
        for job in epas_jobs:
            input_args = job.get('input_arguments', {})
            output_args = job.get('output_arguments', {})
            
            history.append({
                'timestamp': job.get('start_time', 'N/A'),
                'query': input_args.get('query', 'N/A'),
                'status': job['state'],
                'response_preview': output_args.get('response', '')[:200] + '...' if output_args.get('response') else 'N/A'
            })
        
        return history

# Inizializza EPAS integration
epas = EPASAgentIntegration(monitor)
print("✓ EPAS Agent Integration pronta\n")

# ============================================================================
# PARTE 6: UTILITY FUNCTIONS
# ============================================================================

def list_jobs(status: str = None, days: int = 7):
    """Lista job con filtro opzionale"""
    jobs = monitor.get_jobs(status=status, days_back=days)
    
    print(f"\n📋 Jobs ultimi {days} giorni" + (f" - Status: {status}" if status else "") + "\n")
    
    if not jobs:
        print("Nessun job trovato")
        return
    
    for i, job in enumerate(jobs, 1):
        status_icon = "✅" if job['state'] == 'Successful' else "❌" if job['state'] == 'Faulted' else "⏳"
        print(f"{i}. {status_icon} [{job['state']}] {job['process_name']}")
        print(f"   ID: {job['id']}")
        print(f"   Start: {job.get('start_time', 'N/A')}")
        print()

def job_details(job_id: str):
    """Mostra dettagli completi di un job"""
    details = monitor.get_job_details(job_id)
    
    if 'error' in details:
        print(f"❌ Errore: {details['error']}")
        return
    
    print(f"\n📝 Dettagli Job: {job_id}\n")
    print(f"Process: {details.get('process_name', 'N/A')}")
    print(f"Status: {details.get('state', 'N/A')}")
    print(f"Duration: {details.get('duration', 0):.1f}s")
    print(f"Robot: {details.get('robot', 'N/A')}")
    print(f"\nInput Arguments:")
    print(json.dumps(details.get('input_arguments', {}), indent=2))
    print(f"\nOutput Arguments:")
    print(json.dumps(details.get('output_arguments', {}), indent=2))

def stats(days: int = 7):
    """Mostra statistiche"""
    summary = analytics.get_summary(days)
    
    if 'error' in summary:
        print(f"❌ {summary['error']}")
        return
    
    print(f"\n📊 Statistiche ultimi {days} giorni\n")
    print(f"Total Jobs: {summary['total_jobs']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Avg Duration: {summary['avg_duration']:.1f}s")
    print(f"\nBy Status:")
    for status, count in summary['by_status'].items():
        print(f"  • {status}: {count}")
    print(f"\nBy Process:")
    for process, count in summary['by_process'].items():
        print(f"  • {process}: {count}")

def ask_epas(query: str):
    """Esegue query tramite EPAS Agent"""
    result = epas.execute_epas_query(query)
    
    if result['status'] == 'success':
        print(f"\n📝 Risposta EPAS:\n")
        epas.format_html_response(result['response_html'])
        print(f"\n⏱ Durata: {result['duration']:.1f}s")
    else:
        print(f"\n❌ Errore: {result.get('error', result.get('message', 'Unknown error'))}")
    
    return result

def epas_history(days: int = 7):
    """Mostra cronologia query EPAS"""
    history = epas.get_epas_history(days)
    
    print(f"\n📜 Cronologia EPAS - ultimi {days} giorni\n")
    
    if not history:
        print("Nessuna query trovata")
        return
    
    for i, item in enumerate(history, 1):
        status_icon = "✅" if item['status'] == 'Successful' else "❌"
        print(f"{i}. {status_icon} [{item['timestamp']}]")
        print(f"   Query: {item['query']}")
        print(f"   Response: {item['response_preview']}\n")

def list_processes():
    """Lista processi disponibili"""
    processes = monitor.get_processes()
    
    print("\n🤖 Processi disponibili:\n")
    
    for i, proc in enumerate(processes, 1):
        print(f"{i}. {proc['name']} (v{proc['version']})")
        print(f"   Environment: {proc.get('environment', 'N/A')}")
        if proc.get('description'):
            print(f"   Description: {proc['description']}")
        print()

def export_jobs(days: int = 7, filename: str = "jobs_export.csv"):
    """Esporta jobs in CSV"""
    df = analytics.export_to_dataframe(days)
    
    if df.empty:
        print("Nessun job da esportare")
        return
    
    df.to_csv(filename, index=False)
    print(f"✓ {len(df)} jobs esportati in: {filename}")

# ============================================================================
# PARTE 7: DASHBOARD E TESTING
# ============================================================================

print("="*60)
print("=== UIPATH JOB MONITOR PRONTO ===")
print("="*60)

print(f"""
🎯 FUNZIONI DISPONIBILI:

📋 MONITORAGGIO:
  • list_jobs(status=None, days=7)       - Lista job
  • job_details(job_id)                   - Dettagli job specifico
  • stats(days=7)                         - Statistiche generali
  • list_processes()                      - Lista processi disponibili

🤖 EPAS AGENT:
  • ask_epas(query)                       - Esegui query EPAS Agent
  • epas_history(days=7)                  - Cronologia query EPAS

📊 ANALYTICS:
  • export_jobs(days=7, filename)         - Esporta jobs in CSV
  • analytics.plot_job_distribution(days) - Visualizza grafici

💡 ESEMPI:
""")

# Test automatico
if monitor.available:
    print("\n🧪 Test connessione UiPath...\n")
    
    # Lista processi
    processes = monitor.get_processes()
    if processes:
        print(f"✓ Trovati {len(processes)} processi")
        if any(p['name'] == 'AgentAssistantEpas' for p in processes):
            print("✓ AgentAssistantEpas trovato!")
    
    # Statistiche
    print("\n📊 Statistiche recenti:")
    stats(days=7)
    
    print(f"""
\n✅ MONITOR CONFIGURATO E PRONTO!

🚀 ESEMPI D'USO:

# Query EPAS Agent
ask_epas("What is Part-145?")

# Visualizza job recenti
list_jobs(days=3)

# Statistiche
stats(days=30)

# Cronologia EPAS
epas_history(days=7)

# Esporta dati
export_jobs(days=30, filename="epas_jobs.csv")
""")

else:
    print("\n⚠ Modalità demo - UiPath non disponibile")
    print("Configura le credenziali nei Secrets per funzionalità complete")