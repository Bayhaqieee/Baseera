# Baseera AI - Islamic Knowledge Assistant

**Baseera** (Arabic for "Insight") is an advanced AI-powered chatbot and educational platform designed to provide accurate, context-aware answers regarding Islamic teachings. It leverages **Retrieval-Augmented Generation (RAG)** to ground its responses in authentic sources (Quran & Hadith) while utilizing web search for broader context.

Beyond chat, Baseera offers interactive features for Quranic study (*Murajaah*) and gamified learning.

## 🌟 Features

  * **AI Chatbot (RAG)**:
      * Two-agent CrewAI system: A **Researcher** gathers data from religious texts and the web, and a **Synthesizer** formulates the final answer.
      * Vector Search: Uses **Milvus** to semantic search through the Quran and Hadith.
      * Web Search: Integrated self-hosted **SearxNG** instance for privacy-focused web queries.
      * Citations: Every answer includes references to specific Surahs, Ayats, or Hadiths.
  * **Quran Dictionary**: Browse the Quran with translations and audio.
  * **Hadith Dictionary**: Search and browse Hadith collections (Sahih Bukhari, Muslim, etc.).
  * **Murajaah (Memorization Tool)**:
      * Listen to specific Surahs recited by world-renowned Qaris.
      * **Continuous Autoplay**: Seamlessly moves from verse to verse and surah to surah.
      * **Eastern Arabic Numerals**: Authentic styling for verse markers.
  * **Interactive Games**:
      * **Ayat Guesser**: Test your memorization by listening to audio clips and identifying the Surah and Ayat.
      * Supports filtering by specific Surah or Juz'.

## 🛠️ Tech Stack

  * **Backend**: Python (Flask)
  * **AI Framework**: CrewAI, LangChain
  * **LLM Provider**: Azure OpenAI (GPT-4 / GPT-3.5)
  * **Vector Database**: Milvus (Docker)
  * **Search Engine**: SearxNG (Docker)
  * **Data Handling**: Pandas, Kaggle API
  * **Frontend**: HTML5, CSS3, JavaScript (Vanilla)

-----

## 🚀 Getting Started

### Prerequisites

  * **Python 3.10+**
  * **Docker & Docker Compose** (for Milvus and SearxNG)
  * **Azure OpenAI API Key**
  * **Kaggle API Key** (for downloading datasets)

### 1\. Clone the Repository

```bash
git clone https://github.com/Bayhaqieee/Baseera.git
cd Baseera
```

### 2\. Environment Configuration

1.  Copy the example environment file:

    ```bash
    cp .env.example .env
    ```

2.  Open `.env` and fill in your credentials:

      * **Azure OpenAI**: API Key, Endpoint, Deployment names.
      * **Milvus**: Default is `localhost` / `19530`.
      * **SearxNG**: Default is `http://localhost:8080`.

3.  **Kaggle Setup**:

      * Place your `kaggle.json` API key in your home directory:
          * **Windows**: `C:\Users\<YourUser>\.kaggle\kaggle.json`
          * **Linux/Mac**: `~/.kaggle/kaggle.json`

### 3\. Start Infrastructure (Docker)

Baseera requires Milvus (for vector storage) and SearxNG (for web search) to be running.

**Start Milvus:**

```bash
docker-compose up -d
```

**Start SearxNG:**

```bash
cd searxng
docker-compose up -d
cd ..
```

### 4\. Install Dependencies

Create a virtual environment and install the required Python packages.

```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install flask python-dotenv crewai langchain_openai langchain_community pymilvus tiktoken requests pandas kaggle tqdm
```

### 5\. Ingest Data

Before running the app for the first time, you need to download the datasets (Quran/Hadith) and generate vector embeddings.

1.  Start the Flask app (see step 6).
2.  Open your browser or use curl to trigger the ingestion endpoint:
    ```
    http://127.0.0.1:5001/ingest
    ```
    *This process may take several minutes as it downloads data from Kaggle and generates embeddings via Azure OpenAI.*

### 6\. Run the Application

```bash
python app.py
```

Access the application at: `http://127.0.0.1:5001`

-----

## 📂 Project Structure

  * **`app.py`**: Main Flask application entry point. Handles routes (`/`, `/ask`, `/game`, `/murajaah`) and rate limiting.
  * **`crew_setup.py`**: Defines the CrewAI agents (Researcher & Synthesizer) and their tasks.
  * **`data_pipeline.py`**: Handles downloading datasets from Kaggle, processing CSVs, and checking internet connectivity (online/offline modes).
  * **`search_tools.py`**: Logic for routing search queries to either Wikipedia or SearxNG.
  * **`vector_store.py`**: Manages connections to the Milvus vector database.
  * **`config.py`**: Centralized configuration loading from `.env`.
  * **`templates/`**: HTML templates for the UI.
  * **`static/`**: CSS, JavaScript, and image assets.
  * **`searxng/`**: Configuration for the self-hosted search engine.

## ⚠️ Rate Limiting

To prevent abuse and manage costs, the application enforces a **Token Bucket Rate Limit**:

  * **Limit**: 2000 input tokens per IP address per 24 hours.
  * If the limit is exceeded, the API will return a `429` error.

## 🤝 Contributing

Contributions are welcome\! Please feel free to submit a Pull Request.

## 📄 License

[MIT License](https://www.google.com/search?q=LICENSE)