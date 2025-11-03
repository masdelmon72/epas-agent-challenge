# scripts/test_agent.py
from src.agent.epas_agent import run_epas_agent

if __name__ == "__main__":
    result = run_epas_agent(c=1, d=2)
    print("\n🧾 Risultato finale:")
    print(result)
