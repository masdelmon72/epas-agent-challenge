#!/bin/bash

# Script di setup per EPAS Agent Challenge
# Ubuntu 22.04 - Python Environment

echo "=== EPAS Agent Setup - UiPath Challenge ==="
echo ""

# 1. Verifica Python
echo "1. Verifica versione Python..."
python3 --version
pip3 --version

# 2. Aggiorna pip
echo ""
echo "2. Aggiornamento pip..."
pip3 install --upgrade pip

# 3. Installa dipendenze core
echo ""
echo "3. Installazione dipendenze core..."
pip3 install uipath-sdk
pip3 install langchain
pip3 install langchain-community
pip3 install langchain-openai

# 4. Installa dipendenze per RAG e PDF
echo ""
echo "4. Installazione dipendenze RAG e processing PDF..."
pip3 install pypdf
pip3 install faiss-cpu  # Vector store per RAG
pip3 install sentence-transformers  # Per embeddings
pip3 install tiktoken  # Token counter per OpenAI

# 5. Installa dipendenze utility
echo ""
echo "5. Installazione utility..."
pip3 install python-dotenv  # Gestione variabili ambiente
pip3 install requests
pip3 install pydantic

# 6. Installa dipendenze opzionali (per funzionalità avanzate)
echo ""
echo "6. Installazione dipendenze opzionali..."
pip3 install chromadb  # Alternative vector store
pip3 install openai  # Client OpenAI diretto

# 7. Verifica installazioni
echo ""
echo "7. Verifica installazioni..."
python3 -c "import uipath; print(f'✓ UiPath SDK: {uipath.__version__}')" 2>/dev/null || echo "✗ UiPath SDK non installato"
python3 -c "import langchain; print('✓ LangChain installato')" 2>/dev/null || echo "✗ LangChain non installato"
python3 -c "import faiss; print('✓ FAISS installato')" 2>/dev/null || echo "✗ FAISS non installato"

echo ""
echo "=== Setup completato! ==="
echo ""
echo "Prossimi passi:"
echo "1. Crea file .env con le tue API keys"
echo "2. Posiziona i PDF EASA nella cartella data/"
echo "3. Esegui lo script di preparazione knowledge base"