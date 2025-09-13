import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from typing import List, Dict, Any
from groq import AuthenticationError

logger = logging.getLogger(__name__)
load_dotenv()


class RAGAnalyzer:
    def __init__(self, pdf_folder: str, persist_directory: str):
        self.pdf_folder = pdf_folder
        self.persist_directory = persist_directory

        logger.info("Initializing RAG with local HuggingFaceEmbeddings.")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            cache_folder='./cache'
        )
        self.llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.1)
        self.vectorstore = None
        self.base_retriever = None
        os.makedirs(self.pdf_folder, exist_ok=True)
        os.makedirs(self.persist_directory, exist_ok=True)

    def _load_and_split_documents(self) -> list:
        pdf_path = Path(self.pdf_folder)
        all_pdf_files = list(pdf_path.rglob("*.pdf"))
        if not all_pdf_files:
            logger.warning(f"No PDF files found in {self.pdf_folder}. The RAG system will have no data.")
            return []
        logger.info(f"Found {len(all_pdf_files)} PDF documents to load for indexing.")
        documents = []
        for pdf_file in all_pdf_files:
            try:
                loader = PyPDFLoader(str(pdf_file))
                documents.extend(loader.load())
            except Exception as e:
                logger.error(f"Failed to load or process {pdf_file}: {e}")
        if not documents:
            logger.error("Could not load any content from the PDF files found.")
            return []
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        split_docs = text_splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} document pages into {len(split_docs)} text chunks.")
        return split_docs

    def index_documents(self):
        documents_to_index = self._load_and_split_documents()
        if not documents_to_index:
            logger.error("No documents to index. Vectorstore creation aborted.")
            return
        logger.info("Creating new vectorstore and indexing documents...")
        self.vectorstore = Chroma.from_documents(
            documents=documents_to_index,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        logger.info(f"Successfully indexed documents and saved vectorstore to {self.persist_directory}")

    def load_or_create_vectorstore(self):
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            logger.info(f"Loading existing vectorstore from {self.persist_directory}")
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        else:
            logger.warning(f"No existing vectorstore found in '{self.persist_directory}'. Indexing new documents.")
            self.index_documents()
        if self.vectorstore:
            self._prepare_base_retriever()

    def _prepare_base_retriever(self):
        if not self.vectorstore:
            logger.error("Cannot prepare retriever: vectorstore is not initialized.")
            return
        self.base_retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        logger.info("RAG base retriever is ready.")

    def ask(self, query: str, source_filter: List[str] = None) -> Dict[str, Any]:
        if not self.base_retriever:
            return {"result": "Error: The Question-Answering system is not ready. No documents may have been indexed.",
                    "source_documents": []}
        logger.info(f"RAG query: '{query}', Sources: {source_filter or 'All'}")
        retriever_to_use = self.base_retriever
        if source_filter:
            retriever_to_use = self.vectorstore.as_retriever(
                search_kwargs={'filter': {'source': {'$in': source_filter}}, "k": 3}
            )
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm, chain_type="stuff", retriever=retriever_to_use, return_source_documents=True
        )
        try:
            result = qa_chain.invoke({"query": query})
            sources = []
            if 'source_documents' in result:
                unique_sources = {}
                for doc in result.get('source_documents', []):
                    # --- THIS IS THE CORRECTED BLOCK ---
                    # The multi-assignment is broken into separate lines.
                    metadata = doc.metadata
                    source_file = os.path.basename(metadata.get("source", "Unknown"))
                    page = metadata.get("page", -1) + 1

                    if source_file not in unique_sources:
                        unique_sources[source_file] = page
                sources = [{"source": src, "page": pg} for src, pg in unique_sources.items()]
            return {"result": result.get('result', "Sorry, I couldn't find an answer."), "source_documents": sources}
        except AuthenticationError as e:
            logger.error(f"Groq Authentication Error: {e}", exc_info=True)
            return {
                "result": "Groq API Authentication Error. Please ensure your GROQ_API_KEY is correct in the .env file and the server has been restarted.",
                "source_documents": []
            }
        except Exception as e:
            logger.error(f"Error during RAG query processing: {e}", exc_info=True)
            return {
                "result": "An error occurred while trying to find an answer. Please check the server logs for details.",
                "source_documents": []}