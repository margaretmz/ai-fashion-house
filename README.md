# AI Fashion House

**AI Fashion House** is a project created for the [ADK Hackathon with Google Cloud](https://devpost.com/software/fashion-olu3gj). 
It's a modular, multi-agent system that transforms fashion design ideas into beautiful visuals. 
It automates the entire creative pipeline — from finding design inspirations to generating fashion images and then cinematic runway 
videos — by coordinating a set of specialized, intelligent agents. It's built with [ADK](https://google.github.io/adk-docs/) and various Google Cloud tech.

## How It Works

The system relies on a multi-agent framework, where each agent handles a specific step in the creative process. These agents operate asynchronously, enabling a flexible and dynamic design workflow:

1. **Input Analysis**
   Interprets user input to identify themes, fashion concepts, and stylistic cues.

2. **Visual Reference Retrieval**
   The `met_rag_agent` agent searches the Metropolitan Museum of Art's open-access archive (over 500,000 images) to retrieve relevant historical designn references.

   * **BigQuery RAG**: Performs semantic retrieval using Retrieval-Augmented Generation (RAG) with BigQuery.
   * **GenAI Embeddings**: Embeds captions using the `text-embedding-005` model for similarity comparison (image search).
   * **Gemini Multimodal Analysis**: Processes both images and text to extract stylistic and structural fashion details.

3. **Internet Search Expansion**
   The `search_agent` agent uses Google Search Grounding to retrieve contemporary fashion references from the web.

4. **Style Prompt Generation**
   The `promp_writer_agent` & `fashion_design` agents organize visual data using a sequential pattern and combines it via an aggregator assistant to produce a detailed, fashion-specific prompt.

5. **Artifact Creation and Orchestration**
   The `marketing_agent` agent uses the style prompt to generate visual outputs:

   * **Imagen 3** is used to produce high-quality fashion images.
   * **Veo 3** generates stylized runway videos.
   * **Gemini** writes social media posts.

## Target Audience

* Fashion designers seeking design inspirations and showcase their designs visually
* Educators or students in fashion design education
* Archivists or curators seeking to combine design history with generative AI
* Creators and developers interested in visual storytelling and AI-powered prototyping

## Technology Stack

* Agent Development Kit [(ADK)](https://google.github.io/adk-docs/)
* Google Cloud (Vertex AI, BigQuery, Cloud Storage)
* Gemini API and GenAI text/image embedding models
* Imagen 3 and Veo 3 for advanced image and video synthesis
* A modular, multi-agent orchestration system

## Multi-Agent Architecture

![Multi-Agent Architecture](https://raw.githubusercontent.com/margaretmz/ai-fashion-house/main/images/agents-architecture.png)

Each step of the workflow is managed by a dedicated agent:

1. Input Analysis
2. Visual Reference Retrieval (`met_rag` agent)
   * BigQuery-based semantic search
   * Embedding generation and filtering
   * Multimodal image analysis
3. Web Search (`research_agent` agent)
4. Prompt Generation (`fashion_design` agent and aggregator)
5. Visual and Video Generation (`marketing_agent` agent using Imagen 3 and Veo 4)

## Installation
### Prerequisites:

1. Google Cloud SDK [(gcloud CLI)](https://cloud.google.com/sdk/docs/install) installed for authentication.
   
   - Terminal command: `gcloud init` and choose the project ID.
   - Set a default login: `gcloud auth application-default login`.

3. Access to Google Cloud: BigQuery, Gemini, Imagen 4, Veo 3 (public preview).

### Virtual Environment with Python 11.0 or Higher

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Package

```bash
pip install ai-fashion-house
```

### Configure Environment Variables to run the application

Create a `.env` file in the root directory with the following content:

```env
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_API_KEY=<your_google_api_key>
GOOGLE_CLOUD_PROJECT=<your_google_cloud_project_id>
GOOGLE_CLOUD_LOCATION=us-central1

# RAG settings
BIGQUERY_DATASET_ID=met_data
BIGQUERY_CONNECTION_ID=met_data_conn
BIGQUERY_REGION=US

# Embeddings and captioning models
BIGQUERY_EMBEDDINGS_MODEL_ID=embeddings_model
BIGQUERY_EMBEDDINGS_MODEL=text-embedding-005
BIGQUERY_CAPTIONING_MODEL_ID=gemini_model
BIGQUERY_CAPTIONING_MODEL=gemini-2.0-flash
BIGQUERY_TABLE_ID=fashion_ai_met
BIGQUERY_VECTOR_INDEX_ID=met_data_index

VEO2_MODEL_ID=veo-3.0-generate-preview
IMAGEN_MODEL_ID=imagen-4.0-generate-preview-06-06

MEDIA_FILES_BUCKET_GCS_URI=<gs://your-bucket-name>
```
Note: you will need to update `.env` with your own:
* Google API key (get it from [Google AI Studio](https://aistudio.google.com/app/apikey))
* Google Cloud project id
* Google Cloud bucket for storing generated images and videos

### Set Up MET RAG (Retrieval-Augmented Generation)

To simplify the installation process, you can use the `setup-rag` command to automatically configure the MET RAG (Retrieval-Augmented Generation) environment on GCP BigQuery. 
This command sets up the required dataset, connection, and vector index for the `met_rag_agent`.
In case the automated setup fails or you prefer manual deployment, we’ve also included the necessary BigQuery SQL scripts in the `scripts/` folder.

```bash
ai-fashion-house setup-rag
```

### Run the Application

```bash
ai-fashion-house start
```

Open your browser and navigate to:

```
http://localhost:8080
```

to access the AI Fashion House web UI interface.

![Fashion House interface](https://raw.githubusercontent.com/margaretmz/ai-fashion-house/main/images/Screenshot1.png)

![Fashion House interface 2](https://raw.githubusercontent.com/margaretmz/ai-fashion-house/main/images/Screenshot2.png)

### 🤝 Contributing

Contributions are welcome and appreciated! To contribute:

1. **Fork** this repository.
2. **Create a new branch** for your feature or fix.
3. **Commit** your changes with clear messages.
4. **Push** to your forked repository.
5. **Open a Pull Request (PR)** to the `main` branch with a description of your changes and any relevant context.

---

### 🛠️ Running the Project Locally

#### 1. Start the Backend

Run the backend server from the root directory:

```bash
ai-fashion-house start --reload
```

> 💡 Use the `--reload` flag to enable hot-reloading during development.

#### 2. Start the React Frontend

Open a new terminal, navigate to the `ui` directory, and run:

```bash
cd ui
npm install
npm run dev
```
Then open your browser and navigate to:
```
http://localhost:5173
```

#### 3. Build for Production

To generate the production build of the frontend:

```bash
npm run build
```

> ⚛️ The UI is a [React.js](https://reactjs.org/) app using Vite.



