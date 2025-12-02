"""
Backend API Wrapper for EPLC Assistant
This module wraps the backend logic for the Streamlit frontend
"""

import os
import sys
from dotenv import load_dotenv
from chromadb import PersistentClient
from openai import OpenAI

# Runtime environment settings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

# System prompt
GEN_SYSTEM = """You are an assistant that drafts paste-ready text for a chosen phase of the Enterprise Product Lifecycle (EPLC).
Each vector database corresponds to a specific phase (Requirement, Design, Implementation, or Development).
Use the phase, template, and section to stay in scope.
Be concise, specific, and professional (120–180 words)."""


class EPLCBackend:
    """Backend handler for EPLC document generation and Q&A"""
    
    def __init__(self):
        """Initialize the backend with OpenAI and ChromaDB connections"""
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY missing in .env file")
        
        self.chat_model = os.getenv("CHAT_MODEL", "gpt-4o-mini")
        self.top_k = int(os.getenv("TOP_K", "6"))
        self.sim_filter = float(os.getenv("SIM_FILTER", "0.45"))
        self.min_sim = float(os.getenv("MIN_SIM", "0.35"))
        self.target_min = int(os.getenv("TARGET_MIN_WORDS", "120"))
        self.target_max = int(os.getenv("TARGET_MAX_WORDS", "180"))
        
        self.oa = OpenAI(api_key=self.api_key, base_url="https://api.openai.com/v1")
        
        self.PHASE_PATHS = {
            "requirement": "./vector_db/Requirement_db",
            "design": "./vector_db/Design_db",
            "implementation": "./vector_db/Implementation_db",
            "development": "./vector_db/Development_db",
        }
    
    def embed_1024(self, text: str):
        """Generate 1024-dimensional embeddings for text"""
        resp = self.oa.embeddings.create(
            model="text-embedding-3-large",
            dimensions=1024,
            input=text,
        )
        return resp.data[0].embedding
    
    def query_database(self, collection, text: str):
        """Query the vector database with embedded text"""
        try:
            emb = self.embed_1024(text)
            res = collection.query(
                query_embeddings=[emb],
                n_results=self.top_k,
                include=["documents", "distances"],
            )
            docs = res.get("documents", [[]])[0]
            dists = res.get("distances", [[]])[0]
            return docs, dists
        except Exception as e:
            print(f"[retriever] query failed: {e}", file=sys.stderr)
            return [], []
    
    @staticmethod
    def dist_to_sim(d):
        """Convert distance to similarity score"""
        try:
            return 1.0 - float(d)
        except:
            return 0.0
    
    def filter_by_threshold(self, docs, dists):
        """Filter documents by similarity threshold"""
        return [d for d, dist in zip(docs, dists) 
                if self.dist_to_sim(dist) >= self.sim_filter]
    
    def join_context(self, docs):
        """Join context documents into a single string"""
        return "\n\n---\n\n".join(docs) if docs else "(no strong matches)"
    
    def chat_generate(self, system, user):
        """Generate response using OpenAI chat completion"""
        resp = self.oa.chat.completions.create(
            model=self.chat_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return (resp.choices[0].message.content or "").strip()
    
    def generate_document_section(self, phase: str, template: str, 
                                   section: str, details: str, 
                                   instructions: str = ""):
        """
        Generate document sections for EPLC phases
        
        Args:
            phase: EPLC phase (requirement/design/implementation/development)
            template: Document template name
            section: Section name to generate
            details: User-provided context/details
            instructions: Additional instructions (optional)
        
        Returns:
            dict: {'success': bool, 'draft': str, 'error': str}
        """
        try:
            phase = phase.lower()
            
            if phase not in self.PHASE_PATHS:
                return {
                    'success': False,
                    'error': f"Invalid phase. Must be one of: {', '.join(self.PHASE_PATHS.keys())}"
                }
            
            chroma_path = self.PHASE_PATHS[phase]
            if not os.path.exists(chroma_path):
                return {
                    'success': False,
                    'error': f"Database folder for phase '{phase}' not found at {chroma_path}"
                }
            
            # Connect to ChromaDB
            chroma_client = PersistentClient(path=chroma_path)
            collections = [c.name for c in chroma_client.list_collections()]
            
            if not collections:
                return {
                    'success': False,
                    'error': f"No collections found in {phase} database"
                }
            
            coll = chroma_client.get_collection(collections[0])
            
            # Set default instructions if not provided
            if not instructions:
                instructions = f"Concise, specific, {self.target_min}-{self.target_max} words."
            
            # Query the database
            query_text = f"{phase.title()} Phase | Template: {template} | Section: {section}\n{details}"
            docs, dists = self.query_database(coll, query_text)
            kept = self.filter_by_threshold(docs, dists)
            context = self.join_context(kept)
            
            # Generate the draft
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
            
            draft = self.chat_generate(GEN_SYSTEM, user_prompt)
            
            # Add assumptions if similarity is too low
            best_sim = max([self.dist_to_sim(d) for d in dists], default=0.0)
            if best_sim < (self.min_sim * 0.75):
                draft += (
                    "\n\nAssumptions & Next Steps:\n"
                    "- Confirm data categories and user groups.\n"
                    "- Validate environmental dependencies.\n"
                    "- List technical or security risks.\n"
                    "- Identify owner responsibilities.\n"
                )
            
            return {
                'success': True,
                'draft': draft,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'draft': None
            }
    
    def answer_question(self, question: str, phase: str = "implementation"):
        """
        Answer a general EPLC question
        
        Args:
            question: User's question
            phase: EPLC phase to search (default: implementation)
        
        Returns:
            dict: {'success': bool, 'answer': str, 'error': str}
        """
        try:
            phase = phase.lower()
            
            if phase not in self.PHASE_PATHS:
                phase = "implementation"  # Default fallback
            
            chroma_path = self.PHASE_PATHS[phase]
            if not os.path.exists(chroma_path):
                return {
                    'success': False,
                    'error': f"Database folder for phase '{phase}' not found"
                }
            
            chroma_client = PersistentClient(path=chroma_path)
            collections = [c.name for c in chroma_client.list_collections()]
            
            if not collections:
                return {
                    'success': False,
                    'error': "No collections found in database"
                }
            
            coll = chroma_client.get_collection(collections[0])
            
            # Query the database
            docs, dists = self.query_database(coll, question)
            kept = self.filter_by_threshold(docs, dists)
            context = self.join_context(kept)
            
            # Generate answer
            system_prompt = """You are an EPLC (Enterprise Product Lifecycle) assistant. 
Answer questions based on the provided context from EPLC documentation and policies.
Be concise, accurate, and professional."""
            
            user_prompt = f"""
CONTEXT:
{context}

QUESTION:
{question}

Please provide a clear and helpful answer based on the context above.
"""
            
            answer = self.chat_generate(system_prompt, user_prompt)
            
            return {
                'success': True,
                'answer': answer,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'answer': None
            }
