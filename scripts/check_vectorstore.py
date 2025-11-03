import sys
from pathlib import Path

# Aggiungi la cartella principale al path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pickle
import faiss
from sentence_transformers import SentenceTransformer
from src.config.settings import settings

vectorstore_dir = settings.vectorstore_dir
chunks_path = vectorstore_dir / "chunks.pkl"
index_path = vectorstore_dir / "faiss_index.bin"

print("🔍 Checking EPAS vectorstore...\n")

# 1️⃣ Check if files exist
if not chunks_path.exists() or not index_path.exists():
    print(f"❌ Missing vectorstore files in {vectorstore_dir}")
    exit(1)

# 2️⃣ Load chunks
chunks = pickle.load(open(chunks_path, "rb"))
print(f"✅ Loaded {len(chunks)} chunks")

sample = chunks[0]
print(f"🧩 Sample chunk keys: {list(sample.keys())}")
text_field = "text" if "text" in sample else "content" if "content" in sample else None
if not text_field:
    print("❌ Could not find text field ('text' or 'content') in chunks.")
    exit(1)
print(f"✅ Using text field: {text_field}\n")

# 3️⃣ Load FAISS index
index = faiss.read_index(str(index_path))
print(f"✅ FAISS index loaded with {index.ntotal} vectors")
print(f"📏 Dimension: {index.d}")
print(f"⚙️  Metric type: {index.metric_type}\n")

# 4️⃣ Test similarity search
model = SentenceTransformer(settings.embedding_model)
query = "crew training requirements for pilots"
embedding = model.encode([query])

D, I = index.search(embedding, 5)
print(f"🔎 Similarity scores: {D[0]}")
print(f"📚 Indices returned: {I[0]}")

if I[0][0] == -1 or all(score < 0.2 for score in D[0]):
    print("\n⚠️  No similar results found — possible mismatch in embedding model or metric.")
else:
    print("\n✅ Similar vectors found! The index is compatible.")
