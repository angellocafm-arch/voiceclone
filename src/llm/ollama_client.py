"""
VoiceClone — Ollama LLM Client

Python client for Ollama API with support for:
- Chat completions (streaming and non-streaming)
- Tool use (function calling)
- Health checks
- Automatic model selection based on hardware
- Fallback mode when Ollama is unavailable

MIT License — Vertex Developer 2026
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Callable, Optional

import httpx

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL = "mistral:7b-instruct-q4_K_M"
CHAT_ENDPOINT = "/api/chat"
GENERATE_ENDPOINT = "/api/generate"
TAGS_ENDPOINT = "/api/tags"
EMBEDDINGS_ENDPOINT = "/api/embed"
HEALTH_TIMEOUT = 5.0
CHAT_TIMEOUT = 120.0


class OllamaStatus(Enum):
    """Ollama server status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    MODEL_LOADING = "model_loading"
    ERROR = "error"


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    name: Optional[str] = None  # Tool name for tool responses

    def to_dict(self) -> dict[str, Any]:
        """Convert to Ollama API format."""
        msg: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls
        if self.name:
            msg["name"] = self.name
        return msg


@dataclass
class ToolDefinition:
    """A tool that the LLM can call."""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema
    handler: Callable[..., Any]
    confirmation_level: str = "none"  # none | single | double | blocked

    def to_ollama_format(self) -> dict[str, Any]:
        """Convert to Ollama tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ChatResponse:
    """Response from a chat completion."""
    message: ChatMessage
    model: str
    done: bool = True
    total_duration_ns: int = 0
    eval_count: int = 0
    tool_calls: list[dict[str, Any]] = field(default_factory=list)

    @property
    def has_tool_calls(self) -> bool:
        """Whether the response contains tool calls."""
        return bool(self.tool_calls)

    @property
    def duration_ms(self) -> float:
        """Response duration in milliseconds."""
        return self.total_duration_ns / 1_000_000


@dataclass
class StreamChunk:
    """A single chunk from a streaming response."""
    content: str
    done: bool = False
    model: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


class OllamaClient:
    """
    Async client for Ollama API.

    Handles chat completions, tool use, streaming, health checks,
    and fallback when Ollama is unavailable.

    Usage:
        client = OllamaClient(model="mistral:7b")
        response = await client.chat([
            ChatMessage(role="user", content="Hola")
        ])
    """

    def __init__(
        self,
        host: str = DEFAULT_OLLAMA_HOST,
        model: str = DEFAULT_MODEL,
        system_prompt: str = "",
        tools: Optional[list[ToolDefinition]] = None,
        timeout: float = CHAT_TIMEOUT,
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.system_prompt = system_prompt
        self.tools: dict[str, ToolDefinition] = {}
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
        self._status = OllamaStatus.DISCONNECTED
        self._last_health_check: float = 0

        if tools:
            for tool in tools:
                self.register_tool(tool)

    # ─── Tool Registration ────────────────────────────────

    def register_tool(self, tool: ToolDefinition) -> None:
        """Register a tool that the LLM can call."""
        self.tools[tool.name] = tool
        logger.info("Registered tool: %s", tool.name)

    def unregister_tool(self, name: str) -> None:
        """Unregister a tool by name."""
        self.tools.pop(name, None)

    def _get_tools_list(self) -> list[dict[str, Any]]:
        """Get tools in Ollama API format."""
        return [t.to_ollama_format() for t in self.tools.values()]

    # ─── Health Check ─────────────────────────────────────

    async def health_check(self) -> OllamaStatus:
        """
        Check if Ollama is running and responsive.

        Returns:
            OllamaStatus indicating the server state.
        """
        try:
            response = await self._client.get(
                f"{self.host}{TAGS_ENDPOINT}",
                timeout=HEALTH_TIMEOUT,
            )
            if response.status_code == 200:
                self._status = OllamaStatus.CONNECTED
                self._last_health_check = time.time()
                return OllamaStatus.CONNECTED
            self._status = OllamaStatus.ERROR
            return OllamaStatus.ERROR
        except (httpx.ConnectError, httpx.TimeoutException):
            self._status = OllamaStatus.DISCONNECTED
            return OllamaStatus.DISCONNECTED
        except Exception as e:
            logger.error("Ollama health check error: %s", e)
            self._status = OllamaStatus.ERROR
            return OllamaStatus.ERROR

    async def is_healthy(self) -> bool:
        """Quick health check returning boolean."""
        status = await self.health_check()
        return status == OllamaStatus.CONNECTED

    async def list_models(self) -> list[dict[str, Any]]:
        """List available models in Ollama."""
        try:
            response = await self._client.get(
                f"{self.host}{TAGS_ENDPOINT}",
                timeout=HEALTH_TIMEOUT,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
            return []
        except Exception as e:
            logger.error("Failed to list models: %s", e)
            return []

    # ─── Chat (Non-streaming) ─────────────────────────────

    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        use_tools: bool = True,
    ) -> ChatResponse:
        """
        Send a chat completion request to Ollama.

        Args:
            messages: List of chat messages.
            model: Override model for this request.
            temperature: Sampling temperature (0.0 - 2.0).
            use_tools: Whether to include registered tools.

        Returns:
            ChatResponse with the assistant's reply.

        Raises:
            ConnectionError: If Ollama is not available.
            TimeoutError: If the request times out.
        """
        payload: dict[str, Any] = {
            "model": model or self.model,
            "messages": [m.to_dict() for m in messages],
            "stream": False,
            "options": {"temperature": temperature},
        }

        if use_tools and self.tools:
            payload["tools"] = self._get_tools_list()

        try:
            response = await self._client.post(
                f"{self.host}{CHAT_ENDPOINT}",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            msg_data = data.get("message", {})
            tool_calls = msg_data.get("tool_calls", [])

            return ChatResponse(
                message=ChatMessage(
                    role=msg_data.get("role", "assistant"),
                    content=msg_data.get("content", ""),
                    tool_calls=tool_calls,
                ),
                model=data.get("model", self.model),
                done=data.get("done", True),
                total_duration_ns=data.get("total_duration", 0),
                eval_count=data.get("eval_count", 0),
                tool_calls=tool_calls,
            )
        except httpx.ConnectError:
            raise ConnectionError(
                "No se pudo conectar a Ollama. "
                "¿Está corriendo? Ejecuta: ollama serve"
            )
        except httpx.TimeoutException:
            raise TimeoutError(
                f"Ollama no respondió en {self.timeout}s. "
                "El modelo puede estar cargándose."
            )

    # ─── Chat (Streaming) ─────────────────────────────────

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream a chat completion from Ollama.

        Yields StreamChunk objects as the model generates text.

        Args:
            messages: List of chat messages.
            model: Override model for this request.
            temperature: Sampling temperature.

        Yields:
            StreamChunk with partial content.
        """
        payload: dict[str, Any] = {
            "model": model or self.model,
            "messages": [m.to_dict() for m in messages],
            "stream": True,
            "options": {"temperature": temperature},
        }

        try:
            async with self._client.stream(
                "POST",
                f"{self.host}{CHAT_ENDPOINT}",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        msg = data.get("message", {})
                        yield StreamChunk(
                            content=msg.get("content", ""),
                            done=data.get("done", False),
                            model=data.get("model", ""),
                            tool_calls=msg.get("tool_calls", []),
                        )
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
        except httpx.ConnectError:
            raise ConnectionError("No se pudo conectar a Ollama.")

    # ─── Tool Execution ───────────────────────────────────

    async def execute_tool_calls(
        self,
        tool_calls: list[dict[str, Any]],
        confirm_callback: Optional[Callable[[str, str, dict], bool]] = None,
    ) -> list[ChatMessage]:
        """
        Execute tool calls from the LLM and return tool results.

        Args:
            tool_calls: List of tool call dicts from the model.
            confirm_callback: Optional callback for confirmation.
                Receives (tool_name, confirmation_level, args) → bool.

        Returns:
            List of ChatMessage with role="tool" containing results.
        """
        results: list[ChatMessage] = []

        for call in tool_calls:
            func = call.get("function", {})
            tool_name = func.get("name", "")
            tool_args = func.get("arguments", {})

            tool_def = self.tools.get(tool_name)
            if not tool_def:
                results.append(ChatMessage(
                    role="tool",
                    content=json.dumps({
                        "error": f"Tool '{tool_name}' not found",
                    }),
                    name=tool_name,
                ))
                continue

            # Check confirmation level
            if tool_def.confirmation_level == "blocked":
                results.append(ChatMessage(
                    role="tool",
                    content=json.dumps({
                        "error": f"Action '{tool_name}' is blocked for security.",
                    }),
                    name=tool_name,
                ))
                continue

            if tool_def.confirmation_level != "none" and confirm_callback:
                confirmed = confirm_callback(
                    tool_name, tool_def.confirmation_level, tool_args
                )
                if not confirmed:
                    results.append(ChatMessage(
                        role="tool",
                        content=json.dumps({
                            "status": "cancelled",
                            "message": "Action cancelled by user.",
                        }),
                        name=tool_name,
                    ))
                    continue

            # Execute tool
            try:
                if callable(tool_def.handler):
                    import asyncio
                    if asyncio.iscoroutinefunction(tool_def.handler):
                        result = await tool_def.handler(**tool_args)
                    else:
                        result = tool_def.handler(**tool_args)
                else:
                    result = {"error": "Tool handler is not callable"}

                results.append(ChatMessage(
                    role="tool",
                    content=json.dumps(result) if isinstance(result, dict) else str(result),
                    name=tool_name,
                ))
                logger.info("Tool '%s' executed successfully", tool_name)

            except Exception as e:
                logger.error("Tool '%s' failed: %s", tool_name, e)
                results.append(ChatMessage(
                    role="tool",
                    content=json.dumps({
                        "error": str(e),
                        "tool": tool_name,
                    }),
                    name=tool_name,
                ))

        return results

    # ─── Agent Loop (Chat + Tools) ────────────────────────

    async def agent_chat(
        self,
        messages: list[ChatMessage],
        max_tool_rounds: int = 5,
        confirm_callback: Optional[Callable] = None,
    ) -> ChatResponse:
        """
        Run a full agent loop: chat → tool calls → results → chat.

        Keeps calling tools until the model gives a final text response
        or max_tool_rounds is reached.

        Args:
            messages: Initial message list.
            max_tool_rounds: Maximum tool call rounds.
            confirm_callback: Confirmation callback for tools.

        Returns:
            Final ChatResponse with the assistant's answer.
        """
        conversation = list(messages)

        for round_num in range(max_tool_rounds):
            response = await self.chat(conversation, use_tools=True)

            if not response.has_tool_calls:
                return response

            # Add assistant message with tool calls
            conversation.append(response.message)

            # Execute tools and add results
            tool_results = await self.execute_tool_calls(
                response.tool_calls,
                confirm_callback=confirm_callback,
            )
            conversation.extend(tool_results)

            logger.info(
                "Agent round %d: %d tool calls executed",
                round_num + 1,
                len(tool_results),
            )

        # Max rounds reached — get final response without tools
        return await self.chat(conversation, use_tools=False)

    # ─── Embeddings ───────────────────────────────────────

    async def embed(
        self,
        text: str | list[str],
        model: Optional[str] = None,
    ) -> list[list[float]]:
        """
        Generate embeddings for text using Ollama.

        Args:
            text: Single string or list of strings.
            model: Embedding model (default: main model).

        Returns:
            List of embedding vectors.
        """
        input_text = [text] if isinstance(text, str) else text

        try:
            response = await self._client.post(
                f"{self.host}{EMBEDDINGS_ENDPOINT}",
                json={
                    "model": model or self.model,
                    "input": input_text,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embeddings", [])
        except Exception as e:
            logger.error("Embedding request failed: %s", e)
            return []

    # ─── Cleanup ──────────────────────────────────────────

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> OllamaClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
