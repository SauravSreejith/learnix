import os
import logging
import sys
import json
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


class RAGAnalyzer:
    """
    Handles RAG tasks using a persistent ChromaDB vectorstore.
    Allows for filtering retrievals by source document and logs interactions.
    """

    def __init__(self, persist_directory: str):
        self.persist_directory = persist_directory
        # Use a valid Groq model. 'mixtral-8x7b-32768' is a good choice.
        self.llm = ChatGroq(model_name="qwen/qwen3-32b", temperature=0.1)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        self.vectorstore = None
        self.qa_chain = None
        self.log_filepath = "qa_history.json"  # Path for the JSON log file

    def _get_indexed_files_metadata_path(self):
        return os.path.join(self.persist_directory, "indexed_files.json")

    def _needs_reindexing(self, pdf_folder: str):
        """Checks if the PDFs on disk are different from the ones indexed."""
        current_pdf_files = sorted([f for f in os.listdir(pdf_folder) if f.endswith('.pdf')])
        metadata_path = self._get_indexed_files_metadata_path()

        if not os.path.exists(metadata_path):
            return True

        with open(metadata_path, 'r') as f:
            indexed_files = json.load(f)

        return current_pdf_files != indexed_files

    def _index_all_documents(self, pdf_folder: str):
        """Processes all PDFs, creates, and persists the vectorstore."""
        logger.info(f"Indexing all PDF documents from {pdf_folder}. This may take a while...")
        pdf_files = [os.path.join(pdf_folder, f) for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
        
        if not pdf_files:
            logger.error(f"No PDF files found in {pdf_folder} to index.")
            return

        all_docs = []
        for pdf_file in pdf_files:
            try:
                loader = PyPDFLoader(pdf_file)
                all_docs.extend(loader.load())
            except Exception as e:
                logger.error(f"Failed to load or process {os.path.basename(pdf_file)}: {e}")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
        docs_split = text_splitter.split_documents(all_docs)

        self.vectorstore = Chroma.from_documents(
            documents=docs_split,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        # Save metadata of indexed files
        with open(self._get_indexed_files_metadata_path(), 'w') as f:
            json.dump(sorted([os.path.basename(f) for f in pdf_files]), f)

        logger.info("Vectorstore created and persisted successfully.")


    def load_or_create_vectorstore(self, pdf_folder: str):
        """Loads the persistent vectorstore or creates it if it's missing or outdated."""
        if self._needs_reindexing(pdf_folder):
            logger.info("Changes in PDF directory detected. Re-indexing all documents.")
            self._index_all_documents(pdf_folder)
        else:
            logger.info(f"Loading existing vectorstore from {self.persist_directory}")
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        logger.info("Vectorstore is ready.")

    def prepare_filtered_qa_chain(self, selected_pdf_paths: list[str]):
        """Configures the QA chain to retrieve from a selected subset of documents."""
        if not self.vectorstore:
            logger.error("Vectorstore not loaded. Cannot prepare QA chain.")
            return

        retriever = self.vectorstore.as_retriever(
            search_kwargs={'filter': {'source': {'$in': selected_pdf_paths}}}
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever
        )
        logger.info(f"QA chain prepared. Retrieving answers only from: {', '.join([os.path.basename(p) for p in selected_pdf_paths])}")

    def _log_interaction(self, query: str, answer: str):
        """Appends a query-answer pair to the JSON log file."""
        try:
            # Check if file exists and is not empty to decide how to load
            if os.path.exists(self.log_filepath) and os.path.getsize(self.log_filepath) > 0:
                with open(self.log_filepath, 'r') as f:
                    log_data = json.load(f)
            else:
                log_data = []

            # Append new entry
            log_data.append({"query": query, "answer": answer})

            # Write updated data back to file
            with open(self.log_filepath, 'w') as f:
                json.dump(log_data, f, indent=4)
            logger.info(f"Interaction logged to {self.log_filepath}")

        except Exception as e:
            logger.error(f"Failed to log interaction to JSON file: {e}")

    def ask(self, query: str) -> str:
        """Asks a question using the currently configured QA chain and logs the interaction."""
        if not self.qa_chain:
            error_message = "Error: QA chain is not ready. Please select documents first."
            self._log_interaction(query, error_message)
            return error_message
        try:
            result = self.qa_chain.invoke({"query": query})
            answer = result.get('result', "Could not find an answer.")
            self._log_interaction(query, answer)
            return answer
        except Exception as e:
            logger.error(f"Error during RAG query processing: {e}", exc_info=True)
            error_message = "An error occurred while processing the answer."
            self._log_interaction(query, error_message)
            return error_message


def select_pdfs_from_indexed(pdf_folder: str) -> list[str]:
    """Displays a menu for the user to select from available PDFs."""
    os.makedirs(pdf_folder, exist_ok=True)
    pdf_files = sorted([f for f in os.listdir(pdf_folder) if f.endswith('.pdf') and os.path.isfile(os.path.join(pdf_folder, f))])
    
    if not pdf_files:
        print(f"No PDF files found in the '{pdf_folder}' directory.")
        print("Please add PDF files to that folder and restart the program.")
        return []

    print("\nPlease select which of the indexed PDFs you want to work with:")
    for i, filename in enumerate(pdf_files):
        print(f"  [{i+1}] {filename}")

    while True:
        try:
            choice = input("\nEnter the numbers of the PDFs (e.g., 1, 3), or 'all': ")
            if choice.strip().lower() == 'all':
                return [os.path.join(pdf_folder, fname) for fname in pdf_files]

            selected_indices = [int(i.strip()) - 1 for i in choice.split(',')]
            selected_paths = []
            valid_selection = True
            for i in selected_indices:
                if 0 <= i < len(pdf_files):
                    selected_paths.append(os.path.join(pdf_folder, pdf_files[i]))
                else:
                    print(f"Error: Invalid number '{i+1}'. Please choose from the list.")
                    valid_selection = False
            
            if selected_paths and valid_selection:
                return selected_paths
        except (ValueError, IndexError):
            print("Error: Invalid input. Please enter numbers separated by commas (e.g., 1, 3).")

def start_qa_session(rag_system: RAGAnalyzer):
    """Starts an interactive loop to ask questions."""
    print("\nEntering Q&A Session.")
    print("Type your question and press Enter. Type 'quit' or 'exit' to return to the menu.")
    while True:
        query = input("\nQuestion: ")
        if query.lower() in ['quit', 'exit']:
            break
        if not query.strip():
            continue
        
        answer = rag_system.ask(query)
        print("\nAnswer:")
        print(answer)

def main():
    print("Initializing RAG Q&A System...")
    
    rag_system = RAGAnalyzer(persist_directory=CHROMA_DB_FOLDER)
    rag_system.load_or_create_vectorstore(pdf_folder=PDF_DOCS_FOLDER)

    while True:
        selected_paths = select_pdfs_from_indexed(PDF_DOCS_FOLDER)
        if not selected_paths:
            break

        rag_system.prepare_filtered_qa_chain(selected_paths)
        
        session_active = True
        while session_active:
            print("\n" + "="*20)
            print(f"Active Documents: {', '.join([os.path.basename(p) for p in selected_paths])}")
            print("\nMenu:")
            print("  [1] Ask questions about the selected documents")
            print("  [2] Select a different set of documents")
            print("  [3] Exit")
            
            choice = input("\nEnter your choice: ")

            if choice == '1':
                start_qa_session(rag_system)
            elif choice == '2':
                session_active = False # Break inner loop to re-run PDF selection
            elif choice == '3':
                print("Exiting program.")
                sys.exit(0)
            else:
                print("Invalid choice. Please enter a number from 1 to 3.")


if __name__ == '__main__':
    PDF_DOCS_FOLDER = "my_pdfs"
    CHROMA_DB_FOLDER = "my_chroma_db" # Folder for the persistent database

    if not os.getenv("GROQ_API_KEY"):
        logger.error("FATAL: GROQ_API_KEY environment variable not set. Please create a .env file with the key.")
        sys.exit(1)

    main()