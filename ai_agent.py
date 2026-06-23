import ast
import json

from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages.ai import AIMessage
from langchain_core.messages.tool import ToolMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

load_dotenv()

DEFAULT_SYSTEM_PROMPT = (
    "Act as a smart, friendly, and precise AI chatbot. "
    "Format answers with clean Markdown when lists, headings, tables, or code improve readability."
)


def _build_system_prompt(system_prompt, memory_summary):
    prompt = system_prompt.strip() if system_prompt else DEFAULT_SYSTEM_PROMPT
    if memory_summary:
        prompt = (
            f"{prompt}\n\n"
            "Conversation memory summary:\n"
            f"{memory_summary.strip()}\n\n"
            "Use this memory only when it helps answer the user."
        )
    return prompt


def _parse_tool_content(content):
    if isinstance(content, list):
        return content
    if not isinstance(content, str):
        return []
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(content)
            return parsed if isinstance(parsed, list) else []
        except (ValueError, SyntaxError, TypeError, json.JSONDecodeError):
            continue
    return []


def _extract_sources(response_messages):
    sources = []
    seen_urls = set()
    for message in response_messages:
        if not isinstance(message, ToolMessage):
            continue
        for result in _parse_tool_content(message.content):
            if not isinstance(result, dict):
                continue
            url = result.get("url")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            sources.append(
                {
                    "title": result.get("title") or url,
                    "url": url,
                    "content": result.get("content") or "",
                }
            )
    return sources


def get_response_from_ai_agent(
    model_name,
    messages,
    allow_search,
    system_prompt,
    memory_summary="",
):
    llm = ChatGroq(model=model_name)
    tools = [TavilySearchResults(max_results=3)] if allow_search else []
    agent = create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=_build_system_prompt(system_prompt, memory_summary),
    )

    response = agent.invoke({"messages": messages})
    response_messages = response.get("messages", [])
    ai_messages = [
        message.content
        for message in response_messages
        if isinstance(message, AIMessage) and message.content
    ]

    final_response = (
        ai_messages[-1]
        if ai_messages
        else "I could not generate a response. Please try again."
    )

    return {
        "response": final_response,
        "sources": _extract_sources(response_messages),
    }


def summarize_conversation(model_name, previous_summary, messages):
    llm = ChatGroq(model=model_name)
    conversation = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in messages
    )
    prompt = (
        "Update the conversation memory summary for an AI assistant.\n"
        "Keep durable user preferences, goals, project facts, and decisions.\n"
        "Remove small talk and details that are no longer useful.\n\n"
        f"Previous summary:\n{previous_summary or 'No previous summary.'}\n\n"
        f"New conversation messages:\n{conversation}\n\n"
        "Updated summary:"
    )
    response = llm.invoke(prompt)
    return response.content.strip()
