# AI Fashion House

A project for ADK Hackathon with Google Cloud: a multi-agent system that helps you find design inspiration, create fashion images and runway videos.

# What is AI-Fashion Home?

This project is an AI-driven fashion design assistant that transforms user prompts into rich visual outputs using a modular, multi-agent system. Built specifically for fashion concept generation, it automates every step — from idea interpretation to high-fidelity visual creation — by orchestrating a team of intelligent agents.

# How it works?

At its core, the platform uses a multi-agent architecture, where each agent specializes in a discrete task: analyzing user input, retrieving visual references, generating descriptive fashion language, producing images, and organizing media into moodboards. These agents communicate asynchronously to create a dynamic, composable workflow tailored to creative exploration.

Users can input vague or expressive fashion ideas, and the system responds with structured, historically grounded outputs — including AI-generated images, curated archive references, and CSV reports summarizing matches and distances. Everything is generated, enhanced, and visualized in real time.

# Target audience

The platform is ideal for fashion designers, educators, archivists, and creators who need rapid visual prototyping, moodboard generation, or access to stylistic inspiration derived from curated datasets and open-access museum archives.

# Tech

By combining LLMs, retrieval-augmented generation, and autonomous tool orchestration, this project offers a glimpse into the future of creative automation — where intelligent agents assist with storytelling, research, and visual design, all in a single, seamless pipeline.

# Multi-Agent architecture

![Multi-Agent Architecture](images/multi-agent-architecture.png)

In AI-Fashion Home, we use a multi-agent architecture to handle different tasks in the fashion design process. Specifically we automate the following steps:

1. **Input Analysis**: The system analyzes user input to understand the fashion concept.
2. **Visual Reference Retrieval**: The met_rage agent retrieves visual references from the Met Museum's open-access collection, which includes over 500,000 images of artworks and artifacts. 
   - **BigQuery RAG**: The system uses BigQuery to perform retrieval-augmented generation (RAG) to find relevant visual references.
   - **Google GenAI**: Further, it uses 'text-embedding-005' model to generate embeddings for the retrieved references.
   - **Gemini Multimodal Understanding**: The system uses Gemini multimodal understanding capabilities to analyze the retrieved images and extract the information needed for the style agent to generate the prompt.
3. **Internet Search**: The system performs an internet search to find additional images and information that can be used for the style agent to generate the prompt that will be used to generate the images. To do so, the research agent relies on the Google Search Grounding to retrieve relevant images and information from the web.
3. **Style Prompt Generation**: A style agent obtain the retrieved visual references and internet search results by implementin a Sequential Pattern, and fuerther it merges using an agregator assistant agent to generate a style prompt.
4. **Artifacts Generation and pipelines orchestration**: This task is handled by the creative agent, which uses the style prompt to generate fashion images and runway videos, under the hood the agent use Imagen3 and Veo3 to generate the images and videos.


# Installation

## Setting  MET BigQuery RAG

 Refer to the [met_rage](met_rage/README.md) for instructions on how to set up the BigQuery RAG for the Met Museum's open-access collection.


## Running the project

1. Create a Python environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

2. Install the required dependencies:

```bash
pip install ai-fashion-house
```
3. Set up the environment variables:

   - You can set the environment variables in your terminal or create a `.env` file in the root directory of your project.
   - If you choose to create a `.env` file, make sure to include the following variables:

```bash  
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


4. Run the following command to start the AI Fashion House ui:

```bash
ai-fashion-house start
```

5. Open your web browser and go to `http://localhost:8080` to access the AI Fashion House UI.