import os, sys, json
from dotenv import load_dotenv
from chromadb import PersistentClient
from openai import OpenAI

# Runtime environment settings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

# System prompt for generation
GEN_SYSTEM = """You are an assistant that drafts paste-ready text for a chosen phase of the Enterprise Product Lifecycle (EPLC).
Each vector database corresponds to a specific phase (Requirement, Design, Implementation, or Development).
Use the phase, template, and section to stay in scope.
Be concise, specific, and professional (120–180 words)."""


def eprint(*a, **kw):
    print(*a, file=sys.stderr, **kw)


# EMBEDDING
def embed_1024(client: OpenAI, text: str):
    resp = client.embeddings.create(
        model="text-embedding-3-large",
        dimensions=1024,
        input=text,
    )
    return resp.data[0].embedding


# RETRIEVER
class Retriever:
    def __init__(self, client, collection, k=6):
        self.client = client
        self.collection = collection
        self.k = k

    def query(self, text: str):
        try:
            emb = embed_1024(self.client, text)
            res = self.collection.query(
                query_embeddings=[emb],
                n_results=self.k,
                include=["documents", "distances"],
            )
            docs = res.get("documents", [[]])[0]
            dists = res.get("distances", [[]])[0]
            return docs, dists
        except Exception as e:
            eprint("[retriever] query failed:", e)
            return [], []

    @staticmethod
    def dist_to_sim(d):
        try:
            return 1.0 - float(d)
        except:
            return 0.0


def filter_by_threshold(docs, dists, sim_th=0.45):
    return [d for d, dist in zip(docs, dists) if Retriever.dist_to_sim(dist) >= sim_th]


def join_context(docs):
    return "\n\n---\n\n".join(docs) if docs else "(no strong matches)"


# MISSING INFO CHECKER
def detect_missing_info(client, model, template_text, user_input):
    """
    Compare user input with template_text and detect missing required elements.
    Shown AFTER generation (post-generation).
    """
    prompt = f"""
You are an EPLC completeness checker.

TEMPLATE CONTEXT (EPLC guidance from vector DB):
{template_text}

USER INPUT:
{user_input}

TASK:
1. Identify key EPLC-required elements implied by TEMPLATE CONTEXT.
2. Check which elements are missing from USER INPUT.
3. Return a bullet list of missing items.
4. If nothing is missing, return exactly: "No major missing elements."
"""

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You check completeness of input vs template."},
            {"role": "user", "content": prompt},
        ],
        temperature=0
    )
    return resp.choices[0].message.content.strip()


# CHAT GENERATION
def chat_generate(client, model, system, user):
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return (resp.choices[0].message.content or "").strip()


# INPUT HELPERS
def prompt_multiline(hint: str):
    print(hint)
    print("(Finish with an empty line)")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip():
            break
        lines.append(line)
    return "\n".join(lines).strip()


# MAIN
def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key:
        eprint("OPENAI_API_KEY missing in .env")
        sys.exit(1)

    chat_model = os.getenv("CHAT_MODEL", "gpt-4o-mini")
    top_k = int(os.getenv("TOP_K", "6"))
    sim_filter = float(os.getenv("SIM_FILTER", "0.45"))
    min_sim = float(os.getenv("MIN_SIM", "0.35"))
    target_min = int(os.getenv("TARGET_MIN_WORDS", "120"))
    target_max = int(os.getenv("TARGET_MAX_WORDS", "180"))

    # OpenAI
    oa = OpenAI(api_key=api_key, base_url="https://api.openai.com/v1")

    # Phase → DB folder mapping
    PHASE_PATHS = {
        "requirement": "./vector_db/Requirement_db",
        "design": "./vector_db/Design_db",
        "implementation": "./vector_db/Implementation_db",
        "development": "./vector_db/Development_db",
    }

    print("Ask any EPLC Generation question (type 'exit' to quit)\n")

    while True:
        phase = input("Which Phase? (Requirement / Design / Implementation / Development)\n> ").strip().lower()
        if phase == "exit":
            break

        if phase not in PHASE_PATHS:
            print("Invalid phase. Please choose: Requirement / Design / Implementation / Development.\n")
            continue

        chroma_path = PHASE_PATHS[phase]

        if not os.path.exists(chroma_path):
            eprint(f"DB folder for phase '{phase}' not found: {chroma_path}")
            continue

        chroma_client = PersistentClient(path=chroma_path)
        colls = [c.name for c in chroma_client.list_collections()]

        if not colls:
            eprint(f"No collections found under {phase} DB.")
            continue

        coll = chroma_client.get_collection(colls[0])
        retriever = Retriever(oa, coll, k=top_k)
        print(f"[ready] Connected to {phase.title()} Phase DB ({colls[0]})\n")

        # Template + Section input
        while True:
            template = input("Which Template?\n> ").strip()
            if template.lower() == "exit":
                return
            if template:
                break
            print("Template is required. Please enter a template name (or type 'exit' to quit).\n")

        while True:
            section = input("Which Section?\n> ").strip()
            if section.lower() == "exit":
                return
            if section:
                break
            print("Section is required. Please enter a section name (or type 'exit' to quit).\n")

        # Required product/context details
        while True:
            details = prompt_multiline("\nDescribe your product/context:")
            if details:
                break
            print("Product/context description is required. Please provide some details.\n")

        instructions = prompt_multiline("\n(Optional) Any extra instructions?")
        if not instructions:
            instructions = f"Concise, specific, {target_min}-{target_max} words."

        print("\nProcessing...\n")

        # Retrieval
        query_text = f"{phase.title()} Phase | Template: {template} | Section: {section}\n{details}"
        docs, dists = retriever.query(query_text)
        kept = filter_by_threshold(docs, dists, sim_filter)
        context = join_context(kept)

        user_prompt = f"""
CONTEXT:
{context}

QUESTION:
Draft the {section} section for the {template} in the {phase.title()} Phase.

User details:
{details}

Instructions:
{instructions}
"""

        draft = chat_generate(oa, chat_model, GEN_SYSTEM, user_prompt)

        best_sim = max([Retriever.dist_to_sim(d) for d in dists], default=0.0)
        if best_sim < (min_sim * 0.75):
            draft += (
                "\n\nAssumptions & Next Steps:\n"
                "- Confirm data categories and user groups.\n"
                "- Validate environmental dependencies.\n"
                "- List technical or security risks.\n"
                "- Identify owner responsibilities.\n"
            )

        # Missing Info after first draft
        missing = detect_missing_info(oa, chat_model, context, details)

        print("\n==== GENERATED DRAFT ====\n")
        print(draft)

        print("\n==== MISSING REQUIRED INFORMATION ====\n")
        print(missing)
        print("\n=======================================================\n")

        # ----- Satisfaction / Regenerate / Refine loop -----
        while True:
            follow = prompt_multiline(
                "Are you satisfied? Type 'yes' to finish, 'back' to restart, 'r' to regenerate, or enter new instructions:"
            )

            if follow.strip() == "":
                return

            if follow.lower() in ("yes", "y"):
                return

            if follow.lower() in ("back", "b"):
                break

            if follow.lower() in ("exit", "quit", "q"):
                return

            # REGENERATE (same inputs, new draft) + rerun missing-info
            if follow.lower() in ("r", "regenerate"):
                print("\nRegenerating...\n")
                regenerate_prompt = f"""
CONTEXT:
{context}

TASK:
Regenerate the entire {section} section for the {template} in the {phase.title()} Phase,
using the same user details. Produce a clearly different, improved version.
Keep {target_min}-{target_max} words.
"""
                draft = chat_generate(oa, chat_model, GEN_SYSTEM, regenerate_prompt)

                # rerun missing-info after regenerate
                missing = detect_missing_info(oa, chat_model, context, details)

                print("\n==== REGENERATED DRAFT ====\n")
                print(draft)

                print("\n==== MISSING REQUIRED INFORMATION ====\n")
                print(missing)
                print("\n===========================\n")
                continue

            # otherwise: treat input as follow-up instructions
            follow_text = follow.strip()

            refine_prompt = f"""
CONTEXT:
{context}

CURRENT DRAFT:
{draft}

FOLLOW-UP INSTRUCTIONS:
{follow_text}

TASK:
Regenerate the entire section with meaningful updates that fully reflect the new instructions.
"""

            print("\nProcessing...\n")

            draft = chat_generate(oa, chat_model, GEN_SYSTEM, refine_prompt)

            # rerun missing-info after refine
            missing = detect_missing_info(oa, chat_model, context, details)

            print("\n==== UPDATED DRAFT ====\n")
            print(draft)

            print("\n==== MISSING REQUIRED INFORMATION ====\n")
            print(missing)
            print("\n=======================\n")


if __name__ == "__main__":
    main()