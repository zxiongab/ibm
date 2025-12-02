# Import packages
import os, sys
from typing import List, Tuple
from dotenv import load_dotenv
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# Runtime and performance settings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

# Environment setup
load_dotenv()

# Basic config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Root dir for all Chroma DBs
DB_ROOT = os.getenv("CHROMA_ROOT", os.path.join(BASE_DIR, "vector_db"))

TOP_K      = int(os.getenv("TOP_K", "6"))
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY missing in .env")

DB_EPLC_PATH = os.path.join(DB_ROOT, "EPLCFramework_db")
DB_HHS_PATH  = os.path.join(DB_ROOT, "HHS_db")

# Initialize embedding model
sbert = SentenceTransformer("BAAI/bge-large-en-v1.5", device="cpu")

# Connect to both Chroma DBs
eplc_db = PersistentClient(path=DB_EPLC_PATH)
hhs_db  = PersistentClient(path=DB_HHS_PATH)

# Automatically bind the single collection in each DB
def get_single_collection(db, label: str):
    cols = db.list_collections()
    if not cols:
        raise RuntimeError(
            f"[error] No collections found in DB: {label}. "
            f"Check DB path and that data has been imported."
        )
    if len(cols) > 1:
        names = [c.name for c in cols]
        raise RuntimeError(
            f"[error] Multiple collections found in DB: {label}: {names}. "
            f"Please pick one explicitly."
        )
    return cols[0]

coll_eplc = get_single_collection(eplc_db, "EPLCFramework_db")
coll_hhs  = get_single_collection(hhs_db, "HHS_db")

# Database probe utility
def probe_index(c, label: str):
    """Probe one record and return embedding dimension, or None on error."""
    try:
        peek = c.get(limit=1, include=["embeddings"])
        emb_list = peek.get("embeddings")

        if emb_list is None or len(emb_list) == 0:
            return None

        first = emb_list[0]

        if hasattr(first, "shape"):
            emb_dim = int(first.shape[-1])
        else:
            emb_dim = len(first)

        return emb_dim
    except Exception as e:
        print(f"[probe] error while probing {label}:", e)
        return None

# Embedding dimension validation
emb_dim_eplc = probe_index(coll_eplc, "EPLCFramework_db")
emb_dim_hhs  = probe_index(coll_hhs, "HHS_db")

try:
    _probe_vec = sbert.encode(["test"], normalize_embeddings=True)[0]
    model_dim = len(_probe_vec)

    def check_dim(name: str, emb_dim):
        if emb_dim is None:
            print(f"[check] warning: could not infer embedding dim for {name}; skip dim check")
            return
        if int(emb_dim) != model_dim:
            print(
                f"[check] Embedding dim mismatch for {name}: "
                f"collection={emb_dim}, model={model_dim}"
            )
            sys.exit(1)

    check_dim("EPLCFramework_db", emb_dim_eplc)
    check_dim("HHS_db",          emb_dim_hhs)

    print(
        f"[check] ok: model_dim={model_dim}, "
        f"EPLC_dim={emb_dim_eplc}, HHS_dim={emb_dim_hhs}"
    )
except Exception as e:
    print("[check] error while validating embedding dim:", e)
    sys.exit(1)

# Initialize OpenAI client
oa = OpenAI(api_key=OPENAI_API_KEY)

# Embedding and retrieval utilities
def embed(texts: List[str]) -> List[List[float]]:
    return sbert.encode(texts, normalize_embeddings=True).tolist()

def retrieve(query: str, k: int = TOP_K) -> Tuple[list, list, list]:
    qv = sbert.encode([f"query: {query}"], normalize_embeddings=True).tolist()

    # EPLC
    res_eplc = coll_eplc.query(
        query_embeddings=qv,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    ids_eplc   = res_eplc.get("ids", [[]])[0]
    docs_eplc  = res_eplc.get("documents", [[]])[0]
    dists_eplc = res_eplc.get("distances", [[]])[0]

    # HHS
    res_hhs = coll_hhs.query(
        query_embeddings=qv,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    ids_hhs   = res_hhs.get("ids", [[]])[0]
    docs_hhs  = res_hhs.get("documents", [[]])[0]
    dists_hhs = res_hhs.get("distances", [[]])[0]

    combined = []
    for id_, doc_, dist_ in zip(ids_eplc, docs_eplc, dists_eplc):
        combined.append((id_, doc_, dist_, "EPLC"))
    for id_, doc_, dist_ in zip(ids_hhs, docs_hhs, dists_hhs):
        combined.append((id_, doc_, dist_, "HHS"))

    if not combined:
        return [], [], []

    # Smaller distance = more similar
    combined.sort(key=lambda x: x[2])
    combined = combined[:k]

    ids   = [c[0] for c in combined]
    docs  = [c[1] for c in combined]
    dists = [c[2] for c in combined]
    return ids, docs, dists

def pretty_sim(dist: float) -> float:
    try:
        return 1.0 - float(dist)
    except Exception:
        return float("nan")

# Dual-DB exact match
def retrieve_exact(substring: str, k: int = TOP_K) -> Tuple[list, list, list]:
    combined_ids, combined_docs, combined_dists = [], [], []

    for coll in (coll_eplc, coll_hhs):
        try:
            res = coll.get(
                where_document={"$contains": substring},
                include=["documents", "metadatas"],
                limit=k,
            )
        except Exception as e:
            print("[retrieve_exact] error:", e)
            continue

        ids  = res.get("ids", [])
        docs = res.get("documents", [])
        combined_ids.extend(ids)
        combined_docs.extend(docs)
        combined_dists.extend([0.0] * len(docs))

    if len(combined_docs) > k:
        combined_ids   = combined_ids[:k]
        combined_docs  = combined_docs[:k]
        combined_dists = combined_dists[:k]

    return combined_ids, combined_docs, combined_dists

# Prompt construction and LLM interaction
SYSTEM_PROMPT = (
    "You are an EPLC assistant. Answer only using the information in the CONTEXT. "
    "If the answer can be inferred from the context, explain it briefly. "
    "If the context provides no relevant information, reply exactly: Not specified in the provided context."
)

def make_prompt(question: str, docs: List[str]) -> str:
    context = "\n\n---\n\n".join(docs)
    return f"CONTEXT:\n{context}\n\nQUESTION:\n{question}\n"

def ask_openai(prompt: str) -> str:
    try:
        resp = oa.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        return f"[openai error] {e}"

# Interactive main loop
def main():
    # Simple startup check: make sure collections are usable
    try:
        coll_eplc.count()
        coll_hhs.count()
    except Exception as e:
        print("[startup] Collection error:", e)
        sys.exit(1)

    print(f"[ready] Using GPT model: {CHAT_MODEL} | top_k={TOP_K}")
    print("Ask any EPLC question. Type 'exit' to quit.")

    while True:
        try:
            q = input("\nQ> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye.")
            break

        if not q or q.lower() in {"exit", "quit"}:
            print("bye.")
            break

        print("Processing...")

        ids, docs, dists = retrieve_exact(q, TOP_K)
        if not docs:
            # Fall back to semantic retrieval if no exact hits
            ids, docs, dists = retrieve(q, TOP_K)
        if not docs:
            print("A> Not specified in the provided context.")
            continue

        prompt = make_prompt(q, docs)
        answer = ask_openai(prompt)
        print("\nA>", answer if answer else "Not specified in the provided context.")
        print("   citations:", ids)


if __name__ == "__main__":
    main()
