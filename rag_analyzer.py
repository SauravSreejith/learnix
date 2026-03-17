import os
import logging
import pickle
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from typing import List

logger = logging.getLogger(__name__)
load_dotenv()

class RAGAnalyzer:
    def __init__(self, pdf_folder: str, persist_directory: str):
        self.pdf_folder = pdf_folder
        self.persist_directory = persist_directory

        logger.info("Initializing RAG with OpenRouter LLM and Local Embeddings...")
        
        # REVERTED TO HUGGINGFACE LOCAL EMBEDDINGS
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2", 
            cache_folder="./cache"
        )
        
        # OpenRouter Implementation (Still using OpenRouter for chat!)
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model="meta-llama/llama-3.1-8b-instruct:free",
            streaming=True, 
            temperature=0
        )
        
        self.vectorstore = None
        self.ensemble_retriever = None
        os.makedirs(self.pdf_folder, exist_ok=True)
        os.makedirs(self.persist_directory, exist_ok=True)

    def load_or_create_vectorstore(self):
        bm25_path = os.path.join(self.persist_directory, 'bm25.pkl')
        if os.path.exists(self.persist_directory) and os.path.exists(bm25_path):
            logger.info("Loading existing Chroma vectorstore and BM25 index.")
            self.vectorstore = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)
            with open(bm25_path, 'rb') as f:
                self.bm25_retriever = pickle.load(f)
            self._prepare_base_retriever()
        else:
            logger.warning("No indexes found. You need to run indexing logic to chat with PDFs.")

    def _prepare_base_retriever(self):
        vector_retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[self.bm25_retriever, vector_retriever], weights=[0.3, 0.7]
        )
        logger.info("RAG Ensemble Retriever is ready.")

    def ask_stream(self, query: str, source_filter: List[str] = None):
        """Yields chunks of text and source documents for streaming"""
        if not self.ensemble_retriever:
            yield {"error": "RAG not ready."}
            return

        prompt = ChatPromptTemplate.from_template(
            """Answer the question based ONLY on the provided context. If you don't know, say you don't know.
        
        <context>
        {context}
        </context>
        
        Question: {input}"""
        )
        
        document_chain = create_stuff_documents_chain(self.llm, prompt)
        retrieval_chain = create_retrieval_chain(self.ensemble_retriever, document_chain)
        
        for chunk in retrieval_chain.stream({"input": query}):
            if "context" in chunk:
                unique_sources = {}
                for doc in chunk["context"]:
                    source_file = os.path.basename(doc.metadata.get("source", "Unknown"))
                    page = doc.metadata.get("page", -1) + 1
                    if source_file not in unique_sources:
                        unique_sources[source_file] = page
                
                formatted_sources = [{"source": src, "page": pg} for src, pg in unique_sources.items()]
                yield {"type": "sources", "data": formatted_sources}
                
            if "answer" in chunk:
                yield {"type": "token", "content": chunk["answer"]}