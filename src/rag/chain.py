import os
from dotenv import load_dotenv

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.rag.vectorstore import EPASVectorStore

# Carica variabili da .env
load_dotenv()


class EPASRAGChain:
    """
    EPAS RAG Chain basata su Mistral 7B Instruct
    - Vector Store: FAISS
    - LLM: HuggingFaceEndpoint (ChatHuggingFace wrapper)
    """

    def __init__(self, vectorstore_path: str = "data/vectorstore"):
        print("🔹 Inizializzazione EPAS RAG Chain con HuggingFace + Mistral...")

        # 🔐 Token Hugging Face
        hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        if not hf_token:
            raise ValueError(
                "❌ Token Hugging Face mancante. Crea un file `.env` con:\n"
                "HUGGINGFACEHUB_API_TOKEN=la_tua_chiave_hf"
            )

        # 📚 Carica vector store FAISS
        print(f"📂 Caricamento vector store FAISS da {vectorstore_path}")
        self.vectorstore = EPASVectorStore(vectorstore_path)
        self.retriever = self.vectorstore.db.as_retriever(search_kwargs={"k": 4})
        print("✅ Vector store caricato con successo.")

        # 🧠 Inizializza modello Mistral (chat endpoint)
        llm = HuggingFaceEndpoint(
            repo_id="mistralai/Mistral-7B-Instruct-v0.2",
            task="text-generation",
            temperature=0.3,
            max_new_tokens=512,
            huggingfacehub_api_token=hf_token,
        )

        # 💬 Crea Chat wrapper
        self.llm = ChatHuggingFace(llm=llm)

        # 📄 Prompt template
        self.prompt = ChatPromptTemplate.from_template("""
        You are **EPAS Assistant**, an aviation safety expert.
        Use the provided context from the European Plan for Aviation Safety (EPAS)
        to answer the question as accurately as possible.

        If the answer cannot be inferred from the context,
        politely respond that you don't have enough information.

        ---
        Context:
        {context}

        Question:
        {question}
        ---
        """)

        self.parser = StrOutputParser()

    def query(self, question: str):
        """Esegue una query sul RAG e restituisce la risposta."""
        print(f"🔎 Query ricevuta: {question}")

        # 🔍 Recupera i documenti rilevanti
        docs = self.retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in docs])

        # 🧩 Crea la chain (Prompt → LLM → Parser)
        chain = self.prompt | self.llm | self.parser

        # 🚀 Esegui inferenza
        print("💬 Invio della richiesta al modello Mistral...")
        response = chain.invoke({"context": context, "question": question})

        # 📤 Restituisci risultati
        return {
            "answer": response.strip(),
            "sources": [d.metadata.get("source", "unknown") for d in docs],
            "chunks": len(docs),
        }
