# local-llm

This project runs local inference, improves data privacy, and eliminates subscription costs.

## Architecture Pipeline

* **Granite Embeddings**: The granite-embedding-small-english-r2 model tokenizes input text. Tokens become vector embeddings. Granite maps the semantic space.
* **Qdrant Vector Database**: Qdrant runs on localhost, stores high-dimensional vectors, and indexes vectors for similarity search.
* **Qwen Instruct LLM**: Qwen runs on the local GPU, consumes the context window, and generates code responses.

## Execution Flow

1. **Initialize Qdrant**: Docker spins up the database instance on port 6333.
2. **Execute Ingestion Pipeline**: The Ingestion script chunks markdown documents, calculates embeddings, and uploads vector payloads to the Qdrant collection.
3. **Query Local LLM**: Client hits the API endpoint. The API retrieves vector contexts from Qdrant. The API constructs the prompt template. Qwen generates the completion.

## API Endpoints

* **POST /chat**: Client transmits the chat payload. Request contains the question string, session identifier, target model parameter, and retrieval toggle boolean. The server yields a streaming character chunk stream.
* **GET /history/{session_id}**: Client requests the session record. The server retrieves the conversation history array.
* **GET /models**: Client requests the model roster. The server returns the supported model identifiers list and default model designation.
* **GET /health**: Client checks the system viability. The server returns the operational status confirmation.
* **GET /**: Serve the interactive user interface layout page.
* **GET /dashboard**: Redirect the HTTP request to the Qdrant vector database visualization client interface.

Local deployment optimizes latency. Local deployment eliminates subscription cost. Very premium.
