import os
import time
from typing import Generator, List, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from ai_agent import get_response_from_ai_agent, summarize_conversation


ALLOWED_MODEL_NAMES = [
    "llama-3.3-70b-versatile",
    "mixtral-8x7b-32768",
]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value):
        if not value.strip():
            raise ValueError("Message content cannot be blank.")
        return value.strip()


class ChatRequest(BaseModel):
    model_name: str
    system_prompt: str = ""
    messages: List[ChatMessage] = Field(..., min_length=1)
    allow_search: bool = False
    memory_summary: str = ""


class SearchSource(BaseModel):
    title: str
    url: str
    content: str = ""


class ChatResponse(BaseModel):
    response: str
    model_name: str
    used_search: bool
    sources: List[SearchSource] = Field(default_factory=list)


class MemorySummaryRequest(BaseModel):
    model_name: str
    previous_summary: str = ""
    messages: List[ChatMessage] = Field(..., min_length=1)


class MemorySummaryResponse(BaseModel):
    summary: str


app = FastAPI(
    title="SourceAgent API",
    description="Groq-powered LangGraph research agent with Tavily web search and memory modes.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8501",
        "http://localhost:8501",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _validate_request(model_name, allow_search=False):
    if model_name not in ALLOWED_MODEL_NAMES:
        raise HTTPException(
            status_code=400,
            detail="Invalid model name. Please select a valid Groq model.",
        )
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is missing. Add it to your .env file.",
        )
    if allow_search and not os.getenv("TAVILY_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="TAVILY_API_KEY is missing. Add it to your .env file or disable web search.",
        )


def _to_agent_messages(messages):
    return [
        {"role": message.role, "content": message.content}
        for message in messages
    ]


def _stream_text(text) -> Generator[str, None, None]:
    for index in range(0, len(text), 24):
        yield text[index:index + 24]
        time.sleep(0.015)


@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    _validate_request(request.model_name, request.allow_search)
    try:
        agent_result = get_response_from_ai_agent(
            model_name=request.model_name,
            messages=_to_agent_messages(request.messages),
            allow_search=request.allow_search,
            system_prompt=request.system_prompt,
            memory_summary=request.memory_summary,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider request failed: {exc}") from exc

    return ChatResponse(
        response=agent_result["response"],
        model_name=request.model_name,
        used_search=bool(agent_result["sources"]),
        sources=agent_result["sources"],
    )


@app.post("/chat/stream")
@app.post("/api/chat/stream")
def chat_stream_endpoint(request: ChatRequest):
    _validate_request(request.model_name, request.allow_search)
    try:
        agent_result = get_response_from_ai_agent(
            model_name=request.model_name,
            messages=_to_agent_messages(request.messages),
            allow_search=request.allow_search,
            system_prompt=request.system_prompt,
            memory_summary=request.memory_summary,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider request failed: {exc}") from exc

    return StreamingResponse(_stream_text(agent_result["response"]), media_type="text/plain")


@app.post("/memory/summarize", response_model=MemorySummaryResponse)
@app.post("/api/memory/summarize", response_model=MemorySummaryResponse)
def summarize_memory_endpoint(request: MemorySummaryRequest):
    _validate_request(request.model_name)
    try:
        summary = summarize_conversation(
            model_name=request.model_name,
            previous_summary=request.previous_summary,
            messages=_to_agent_messages(request.messages),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Memory summary failed: {exc}") from exc

    return MemorySummaryResponse(summary=summary)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=9999)
