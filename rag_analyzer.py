import os
import logging
import pickle
from pathlib import Path
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

from langchain_community.document_loaders import PyPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from typing import List, Dict, Any

logger = logging.getLogger(__name__)
load_dotenv()

class RAGAnalyzer:
    def __init__(self, pdf_folder: str, persist_directory: str):
        self.pdf_folder = pdf_folder
        self.persist_directory = persist_directory

        logger.info("Initializing RAG with OpenAI Embeddings and OpenRouter LLM.")
        
        openai_api_key = os.getenv("OPENAI_API_KEY", "dummy-key-for-embeddings")
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=openai_api_key
        )
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY", "dummy"),
            model="meta-llama/llama-3.1-8b-instruct:free",
            temperature=0,
            extra_body={
                "provider": {
                    "order": ["Anthropic", "Google", "OpenAI"],
                    "allow_fallbacks": True
                }
            }
        )
        
        self.vectorstore = None
        self.base_retriever = None
        self.bm25_retriever = None
        self.ensemble_retriever = None
        
        os.makedirs(self.pdf_folder, exist_ok=True)
        os.makedirs(self.persist_directory, exist_ok=True)

    def _load_and_split_documents(self) -> list:
        pdf_path = Path(self.pdf_folder)
        all_pdf_files = list(pdf_path.rglob("*.pdf"))
        if not all_pdf_files:
            logger.warning(f"No PDF files found in {self.pdf_folder}.")
            return []
            
        logger.info(f"Found {len(all_pdf_files)} PDF documents to load.")
        documents = []
        for pdf_file in all_pdf_files:
            try:
                loader = PyPDFLoader(str(pdf_file))
                documents.extend(loader.load())
            except Exception as e:
                logger.error(f"Failed to load {pdf_file}: {e}")
                
        if not documents:
            return []
            
        logger.info("Semantic chunking in progress...")
        text_splitter = SemanticChunker(self.embeddings)
        split_docs = text_splitter.split_documents(documents)
        logger.info(f"Split raw documents into {len(split_docs)} semantic chunks.")
        return split_docs

    def index_documents(self):
        docs = self._load_and_split_documents()
        if not docs:
            logger.error("No documents to index.")
            return
            
        logger.info("Creating Chroma vectorstore and BM25 index...")
        self.vectorstore = Chroma.from_documents(docs, self.embeddings, persist_directory=self.persist_directory)
        
        self.bm25_retriever = BM25Retriever.from_documents(docs)
        self.bm25_retriever.k = 3
        
        with open(os.path.join(self.persist_directory, 'bm25.pkl'), 'wb') as f:
            pickle.dump(self.bm25_retriever, f)
            
        logger.info("Finished creating and saving indexes.")

    def load_or_create_vectorstore(self):
        bm25_path = os.path.join(self.persist_directory, 'bm25.pkl')
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory) and os.path.exists(bm25_path):
            logger.info("Loading existing Chroma vectorstore and BM25 index.")
            self.vectorstore = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)
            with open(bm25_path, 'rb') as f:
                self.bm25_retriever = pickle.load(f)
        else:
            logger.info("Indexes not found or corrupted. Re-indexing...")
            self.index_documents()
            
        if self.vectorstore and self.bm25_retriever:
            self._prepare_base_retriever()

    def _prepare_base_retriever(self):
        vector_retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[self.bm25_retriever, vector_retriever],
            weights=[0.3, 0.7] # Vector search gets more weight for contextual understanding
        )
        logger.info("RAG Ensemble Retriever (Hybrid Search) is ready.")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _invoke_qa(self, qa_chain, query):
        return qa_chain.invoke({"query": query})

    def ask(self, query: str, source_filter: List[str] = None) -> Dict[str, Any]:
        if not self.ensemble_retriever:
            return {"result": "Error: RAG not ready.", "source_documents": []}
            
        # Due to LangChain limitations with EnsembleRetriever filtering, we gracefully skip source filtering
        # when using RRF hybrid search, as BM25 doesn't cleanly accept metadata filtering out of the box.
        retriever_to_use = self.ensemble_retriever
        
        # Create modern LCEL retrieval chain
        prompt = ChatPromptTemplate.from_template(
            """Answer the following question based only on the provided context:
        
        <context>
        {context}
        </context>
        
        Question: {input}"""
        )
        
        document_chain = create_stuff_documents_chain(self.llm, prompt)
        retrieval_chain = create_retrieval_chain(retriever_to_use, document_chain)
        
        try:
            result = retrieval_chain.invoke({"input": query})
            sources = []
            if 'context' in result:
                unique_sources = {}
                for doc in result.get('context', []):
                    metadata = doc.metadata
                    source_file = os.path.basename(metadata.get("source", "Unknown"))
                    page = metadata.get("page", -1) + 1
                    if source_file not in unique_sources:
                        unique_sources[source_file] = page
                sources = [{"source": src, "page": pg} for src, pg in unique_sources.items()]
            return {"result": result.get('answer', "No answer found."), "source_documents": sources}
            
        except Exception as e:
            logger.error(f"Error during RAG query: {e}", exc_info=True)
            return {"result": f"API Error: {e}", "source_documents": []}