# SourceAgent

SourceAgent is an agentic AI research chatbot built with FastAPI, LangGraph,
Groq, and Tavily. It provides a clean browser chat interface where users can ask
questions, enable web search, view cited sources, and keep conversations saved in
the browser.

## Highlights

- Agentic workflow powered by LangGraph ReAct agents
- Fast Groq-backed LLM responses
- Optional Tavily web search for source-backed answers
- Clickable source links when search is used
- Saved chat history in browser `localStorage`
- Memory modes for no memory, session memory, or summarized memory
- Markdown rendering with code block support
- FastAPI backend with request validation
- Vercel-ready Python API routes
- Static HTML, CSS, and JavaScript frontend
- Optional Docker Compose setup for local development

## Demo Flow

1. Start a new chat.
2. Choose a Groq model.
3. Select a memory mode.
4. Enable Tavily web search when you need current information or cited sources.
5. Ask a question and continue the conversation from the saved sidebar history.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | HTML, CSS, JavaScript |
| Backend | FastAPI, Pydantic |
| Agent | LangGraph ReAct agent |
| LLM | Groq |
| Web Search | Tavily |
| Deployment | Vercel |
| Optional Local Runtime | Docker, Docker Compose |

## Architecture

```text
Browser UI
  |
  | POST /api/chat
  | POST /api/chat/stream
  | POST /api/memory/summarize
  v
FastAPI Backend
  |
  v
LangGraph ReAct Agent
  |
  |-- Groq LLM
  |
  |-- Tavily Search Tool, optional

Browser localStorage
  |
  v
Saved chat history
```

## Project Structure

```text
.
├── api/
│   └── index.py          # Vercel Python entrypoint
├── public/
│   └── index.html        # Static browser frontend
├── ai_agent.py           # LangGraph agent, Tavily tool setup, source extraction
├── backend.py            # FastAPI app, schemas, validation, and routes
├── requirements.txt      # Python dependencies
├── Pipfile               # Optional Pipenv dependency file
├── vercel.json           # Vercel routing and build config
├── Dockerfile            # Optional container runtime
├── docker-compose.yml    # Optional backend + frontend local setup
├── .env.example          # Environment variable template
└── .gitignore
```

## Requirements

- Python 3.11+
- Groq API key
- Tavily API key, only required when web search is enabled

## Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Add your keys:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

`GROQ_API_KEY` is required for all chat responses. `TAVILY_API_KEY` is only
required when Tavily web search is enabled in the UI or API request.

## Run Locally

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI backend:

```bash
python backend.py
```

In a second terminal, serve the frontend:

```bash
python -m http.server 8501 -d public
```

Open the app:

```text
http://127.0.0.1:8501
```

FastAPI docs are available at:

```text
http://127.0.0.1:9999/docs
```

## Run With Docker Compose

```bash
docker compose up --build
```

Then open:

```text
http://127.0.0.1:8501
```

## API Usage

Send a chat request:

```bash
curl -X POST http://127.0.0.1:9999/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "llama-3.3-70b-versatile",
    "system_prompt": "You are a concise technical mentor.",
    "messages": [
      {
        "role": "user",
        "content": "Explain LangGraph in simple terms."
      }
    ],
    "allow_search": false,
    "memory_summary": ""
  }'
```

Main endpoints:

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Health check |
| `POST` | `/api/chat` | Generate an agent response |
| `POST` | `/api/chat/stream` | Return a text streaming response |
| `POST` | `/api/memory/summarize` | Update a summarized memory string |

Supported model names:

- `llama-3.3-70b-versatile`
- `mixtral-8x7b-32768`

## Deploy To Vercel

1. Push this repository to GitHub.
2. Import the repository in Vercel.
3. Set the framework preset to `Other`.
4. Add environment variables:
   - `GROQ_API_KEY`
   - `TAVILY_API_KEY`
5. Deploy.

Vercel serves the frontend from `public/index.html` and routes `/api/*` requests
to the FastAPI app through `api/index.py`.

## Configuration Notes

- Chats are stored in the user's browser with `localStorage`.
- No database is required for the current version.
- Vercel serverless functions should not be used for durable local file storage.
- Do not commit `.env` or real API keys.
- For local frontend development on a different backend URL, set
  `window.SOURCEAGENT_API_BASE` before the app script runs.

## Roadmap

- User authentication
- Database-backed chat storage
- Document upload and RAG
- True token streaming from the model provider
- Automated backend tests
- Request logging and observability

## Contributing

Contributions are welcome. Fork the repository, create a feature branch, make
your changes, and open a pull request with a clear description of what changed.

## License

Add a license file before using this project in production or accepting external
contributions.
