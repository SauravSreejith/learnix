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
  - `sentence-transformers` – Semantic vector embeddings
  - `scikit-learn` – Cosine similarity
  - `numpy` – Numerical simulations
  - `langchain-google-genai` – Gemini LLM + Embeddings
  - `chromadb` – Persistent vector store
  - `pypdf` – PDF parsing
  - `python-dotenv` – Secure env var handling
  - `flask-cors` – CORS for frontend

### 🌐 Frontend

- **Repo**: [murugnn/learnix](https://github.com/murugnn/learnix)
- **Framework**: React.js (Vite)
- **Language**: TypeScript
- **Styling**:
  - `tailwindcss`
  - `shadcn/ui`
- **Libraries**:
  - `react-router-dom` – Routing
  - `lucide-react` – Icons
- **Tools**:
  - `Vite` – Build tool
  - `npm` – Package manager

---

## ⚙️ Installation

### Prerequisites

- Python 3.10+ and `pip`
- Node.js and `npm`
- Google Gemini API Key
  
---

### 🔧 Backend Setup

```bash
# Clone the backend repo
git clone <your-backend-repository-url>
cd engine  # or your backend folder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
touch .env
# Then edit it with your Gemini key
# e.g., nano .env
````

Your `.env` should contain:

```env
GEMINI_API_KEY="AIzaSy...YOUR_API_KEY_HERE"
```

---

### 🎨 Frontend Setup

```bash
# In a separate folder
git clone https://github.com/SauravSreejith/passpilot-web.git
cd passpilot-web

# Install frontend dependencies
npm install
```

---

## 🚀 Running the App

You’ll need **two terminals**: one for backend, one for frontend.

---

### ▶️ Start Backend

```bash
# In backend directory
source venv/bin/activate
python run_server.py
```

> The backend runs on `http://localhost:5000`.

---

### ▶️ Start Frontend

```bash
# In frontend directory
npm run dev
```

> The frontend runs on `http://localhost:5173`.

---

## 📚 Project Documentation

### 🎯 Vision: From Anxiety to Strategy

Learnix turns exam stress into smart study strategies—helping students prepare confidently with AI-powered plans and expert-backed guidance. **Study smarter, not harder!**

---

### 🧠 Component 1: Exam Analysis Engine (`ExamAnalyzer`)

#### 📌 Semantic Question Analysis

* **Model**: `all-MiniLM-L6-v2`
* **Goal**: Understand question *meaning*, not just keywords
* **Method**: Embed both user input and database questions → compute cosine similarity

#### 📌 Pass-Strategy Algorithm

* **Formula**:
  `Strategic Value = Topic Frequency × Average Marks Per Appearance`
* **Mechanism**:

  * Calculate user’s deficit
  * Rank unstudied topics by Strategic Value
  * Recommend highest ROI topics until gap is closed

#### 📌 Monte Carlo Simulation

* Generate 100,000 simulated papers
* For each:

  * Roll for topic appearance (based on historical probability)
  * Assign random historical mark value
  * Tally up if student would pass
* **Output**: Pass probability = % of simulations ≥ target score

---

### 📘 Component 2: RAG Knowledge Engine (`RAGAnalyzer`)

#### 💡 Pipeline Overview

1. **Load & Split**:
   Parse PDFs → Chunk with overlap using `RecursiveCharacterTextSplitter`

2. **Embed & Store**:
   Use `embedding-001` → Store in `ChromaDB`

3. **Retrieve**:
   Query embedded → Retrieve top chunks with vector similarity

4. **Generate**:
   Use `Gemini 1.5 Flash` to answer based only on relevant context

> ✳️ This grounds the LLM’s answers, reducing hallucination.

---

## 🖼️ Screenshots

---

## 👩‍💻 Team Contributions

* **Anagha K** – Frontend Lead
  Built the entire React frontend with Vite, TypeScript, TailwindCSS, and Shadcn/UI.

* **Saurav Sreejith** – Backend & Algorithms
  Built the Flask API, semantic search engine, strategic value algorithm, and Monte Carlo simulator.

* **Shreya Padmakumar** – AI & RAG Specialist
  Designed the RAGAnalyzer pipeline using LangChain, Gemini, ChromaDB, and PDF processing.

* **S Murugan** – DevOps & Architecture
  Structured the repo split, wrote `run_server.py`, handled dependency and environment management.


