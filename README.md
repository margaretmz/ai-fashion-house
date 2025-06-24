# AI Fashion House

A project built for the **ADK Hackathon with Google Cloud**, **AI Fashion House** is a multi-agent system designed to assist with design inspiration, fashion image generation, and cinematic runway video creation.

## What is AI Fashion House?

AI Fashion House is an AI-powered fashion design assistant that transforms expressive or abstract user prompts into rich visual content. Built on a modular, multi-agent architecture, it automates the entire creative pipeline—from concept interpretation to high-fidelity visual generation—by coordinating a set of intelligent, specialized agents.

## How It Works

The system relies on a multi-agent framework, where each agent handles a specific step in the creative process. These agents operate asynchronously, enabling a flexible and dynamic design workflow:

1. **Input Analysis**
   Interprets user input to identify themes, fashion concepts, and stylistic cues.

2. **Visual Reference Retrieval**
   The `met_rag_agent` agent searches the Metropolitan Museum of Art's open-access archive (over 500,000 images) to retrieve relevant historical references.

   * **BigQuery RAG**: Performs semantic retrieval using Retrieval-Augmented Generation with BigQuery.
   * **GenAI Embeddings**: Embeds captions using the `text-embedding-005` model for similarity comparison.
   * **Gemini Multimodal Analysis**: Processes both images and text to extract stylistic and structural fashion details.

3. **Internet Search Expansion**
   The `search_agent` agent uses Google Search Grounding to retrieve contemporary fashion references from the web.

4. **Style Prompt Generation**
   The `promp_writer_agent` & `fashion_design` agents organize visual data using a sequential pattern and combines it via an aggregator assistant to produce a detailed, fashion-specific prompt.

5. **Artifact Creation and Orchestration**
   The `marketing_agent` agent uses the style prompt to generate visual outputs:

   * **Imagen 3** is used to produce high-quality fashion images.
   * **Veo 3** generates stylized runway videos.

## Target Audience

AI Fashion House is designed for:

* Fashion designers exploring new creative directions
* Educators and students in fashion design programs
* Archivists and curators seeking to combine history with generative AI
* Creators and developers interested in visual storytelling and AI-powered prototyping

## Technology Stack

This project integrates:

* Google Cloud (Vertex AI, BigQuery, Cloud Storage)
* Gemini API and GenAI text/image embedding models
* Imagen 3 and Veo 3 for advanced image and video synthesis
* A modular, multi-agent orchestration system

## Multi-Agent Architecture

![Multi-Agent Architecture](https://raw.githubusercontent.com/margaretmz/ai-fashion-house/main/images/multi-agent-architecture.png)

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

### Setting Up MET BigQuery RAG

See the [met\_rage README](met_rage/README.md) for full setup instructions.

### Create and Activate Python Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

```bash
pip install ai-fashion-house
```

### Configure Environment Variables

Create a `.env` file in the root directory with the following content:

```env
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_API_KEY=<YOUR_GOOGLE_API_KEY>
GOOGLE_CLOUD_PROJECT=<YOUR_GOOGLE_CLOUD_PROJECT>
GOOGLE_CLOUD_LOCATION=<YOUR_GOOGLE_CLOUD_LOCATION>

BIGQUERY_DATASET_ID=met_data
BIGQUERY_EMBEDDINGS_MODEL_ID=embeddings_model
BIGQUERY_EMBEDDINGS_TABLE_ID=fashion_ai_outputs_embeddings

VEO2_OUTPUT_GCS_URI=gs://myfiles2025
VEO2_MODEL_ID=veo-3.0-generate-preview
IMAGEN_MODEL_ID=imagen-4.0-generate-preview-06-06
```

### Run the Application

```bash
ai-fashion-house start
```

Open your browser and navigate to:

```
http://localhost:8080
```

to access the AI Fashion House interface.

![Fashion House interface](https://raw.githubusercontent.com/margaretmz/ai-fashion-house/main/images/Screenshot1.png)

![Fashion House interface 2](https://raw.githubusercontent.com/margaretmz/ai-fashion-house/main/images/Screenshot2.png)


