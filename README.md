
# HACKNOVA: LEARNIX

## 🔗 Project Repository
### 👥 Team Name: Stardust Crusaders
**Members**: Anagha K, Saurav Sreejith, Shreya Padmakumar, S Murugan

---

## 📘 Project Description

**Learnix** is an AI-powered exam study assistant designed to support students across multiple curricula—including KTU, CBSE and ICSE —by helping them prepare more effectively and confidently for their exams. It is built to address the common challenges students face during time-constrained study periods, providing structured, data-driven guidance that prioritizes meaningful learning over last-minute cramming.

Learnix leverages artificial intelligence, historical question analysis, syllabus mapping, and textbook-backed insights to offer personalized study plans, highlight high-impact topics, and provide real-time progress tracking. Students can access concise revision materials, ask curriculum-specific questions, and receive accurate explanations sourced directly from their textbooks using a Retrieval-Augmented Generation (RAG) model.

The platform is not a shortcut for passing exams—it’s a comprehensive study companion that empowers students to plan, understand, and revise efficiently. By focusing on thoughtful learning strategies and effort optimization, Learnix helps students build confidence, manage stress, and achieve better academic outcomes without compromising on comprehension.

---

## 🛠️ Technologies & Components

### 📦 Backend (Engine)

- **Language**: Python 3.10+
- **Frameworks**:
  - `Flask` – REST API
  - `LangChain` – RAG orchestration
- **Libraries**:
  - `sentence-transformers` & `langchain-huggingface` – Semantic vector embeddings
  - `scikit-learn` – Cosine similarity
  - `numpy` – Numerical simulations
  - `langchain-groq` – High-speed LLM for Q&A
  - `chromadb` – Persistent vector store
  - `pypdf` – PDF parsing
  - `python-dotenv` – Secure environment variable handling
  - `flask-cors` – CORS for frontend

### 🌐 Frontend

- **Framework**: Next.js (React Framework)
- **Language**: TypeScript
- **Styling**:
  - `tailwindcss`
  - `shadcn/ui`
- **Libraries**:
  - Next.js App Router – File-based routing
  - `react-markdown` – Renders AI-generated markdown
  - `@tailwindcss/typography` – Styles markdown content
  - `lucide-react` – Icons
- **Tools**:
  - `Next.js CLI` – Build tool
  - `npm` – Package manager

---

## ⚙️ Installation

### Prerequisites

- Python 3.10+ and `pip`
- Node.js and `npm`
- **Groq API Key** (for the RAG Tutor)

---

### 🔧 Backend Setup

```bash
# Clone the backend repository
git clone <your-backend-repository-url>
cd <backend-folder-name>

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create the environment file
touch .env
```

Now, edit the `.env` file to include your Groq API key, which you can get for free from the [Groq Console](https://console.groq.com/keys).

Your `.env` should contain:

```env
GROQ_API_KEY="gsk_...YOUR_API_KEY_HERE"
```

---

### 🎨 Frontend Setup

```bash
# In a separate terminal, clone the frontend repository
git clone <your-frontend-repository-url>
cd <frontend-folder-name>

# Install frontend dependencies
npm install
```

---

## 🚀 Running the App

You will need **two separate terminals**: one for the backend and one for the frontend.

---

### ▶️ Start Backend

```bash
# In your backend directory, with the virtual environment active
python run_server.py
```

> The backend server will run on `http://localhost:5000`.

---

### ▶️ Start Frontend

```bash
# In your frontend directory
npm run dev
```

> The frontend development server will run on `http://localhost:3000`.

---

## 📚 Project Documentation

### 🎯 Vision: From Anxiety to Strategy

Learnix turns exam stress into smart study strategies—helping students prepare confidently with AI-powered plans and expert-backed guidance. **Study smarter, not harder!**

---

### 🧠 Component 1: Exam Analysis Engine (`ExamAnalyzer`)

#### 📌 Semantic Question Analysis

*   **Model**: `all-MiniLM-L6-v2`
*   **Goal**: Understand question *meaning*, not just keywords.
*   **Method**: Embed both user queries and all database questions into vectors, then compute cosine similarity to find the closest matches.

#### 📌 Pass-Strategy Algorithm

*   **Formula**: `Strategic Value = Topic Frequency × Average Marks Per Appearance`
*   **Mechanism**:
    1.  Calculate the student's current mark deficit based on their target.
    2.  Rank all unstudied topics by their "Strategic Value."
    3.  Recommend the topics with the highest return on investment (ROI) until the mark deficit is covered.

#### 📌 Monte Carlo Simulation

*   Generate 10,000+ simulated exam papers based on historical data.
*   For each simulated paper:
    *   Use historical probability to determine if a topic appears.
    *   If it appears, assign a random mark value from its past occurrences.
    *   Calculate the total score based on the student's studied topics.
*   **Output**: Calculate the pass probability as the percentage of simulated exams where the student's score met or exceeded the pass mark.

---

### 📘 Component 2: RAG Knowledge Engine (`RAGAnalyzer`)

#### 💡 Pipeline Overview

1.  **Load & Split**:
    Parse all PDF textbooks and reference materials into text, then chunk them with overlap using `RecursiveCharacterTextSplitter`.

2.  **Embed & Store**:
    Use the local `all-MiniLM-L6-v2` model (via `HuggingFaceEmbeddings`) to convert text chunks into vector embeddings and store them persistently in `ChromaDB`.

3.  **Retrieve**:
    When a user asks a question, embed their query and retrieve the most relevant text chunks from ChromaDB using vector similarity search.

4.  **Generate**:
    Send the user's question along with the retrieved text chunks to a high-speed LLM (`Llama 3` via `Groq`) and instruct it to generate an answer based *only* on the provided context.

> ✳️ This process grounds the LLM’s answers in factual, textbook-based knowledge, drastically reducing the risk of hallucination and ensuring curriculum accuracy.

---

## 🖼️ Screenshots

*(Add your project screenshots here)*

---

## 👩‍💻 Team Contributions

*   **Anagha K** – Frontend Lead
    Built the entire responsive frontend using Next.js, TypeScript, TailwindCSS, and Shadcn/UI.

*   **Saurav Sreejith** – Backend & Algorithms
    Developed the Flask API, the semantic search engine, the strategic value algorithm, and the Monte Carlo pass probability simulator.

*   **Shreya Padmakumar** – AI & RAG Specialist
    Designed and implemented the `RAGAnalyzer` pipeline using LangChain, Groq, HuggingFace Embeddings, and ChromaDB for PDF-based Q&A.

*   **S Murugan** – DevOps & Architecture
    Structured the monorepo, wrote the `run_server.py` startup script, and managed dependencies and environment configurations for seamless integration.