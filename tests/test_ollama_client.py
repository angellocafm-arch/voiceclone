"""
Tests for OllamaClient — VoiceClone LLM module.

Tests cover:
- ChatMessage/ToolDefinition serialization
- OllamaClient initialization
- Tool registration
- Tool execution with confirmation levels
- Agent loop logic (mocked)

Run: python -m pytest tests/test_ollama_client.py -v
"""

import asyncio
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.llm.ollama_client import (
    ChatMessage,
    ChatResponse,
    OllamaClient,
    OllamaStatus,
    StreamChunk,
    ToolDefinition,
)


def test_chat_message_to_dict() -> None:
    """ChatMessage serializes correctly."""
    msg = ChatMessage(role="user", content="Hola")
    d = msg.to_dict()
    assert d == {"role": "user", "content": "Hola"}

    msg_with_tools = ChatMessage(
        role="assistant",
        content="",
        tool_calls=[{"function": {"name": "test", "arguments": {}}}],
    )
    d2 = msg_with_tools.to_dict()
    assert "tool_calls" in d2
    assert len(d2["tool_calls"]) == 1


def test_chat_message_tool_response() -> None:
    """Tool response messages include name."""
    msg = ChatMessage(role="tool", content='{"result": "ok"}', name="create_folder")
    d = msg.to_dict()
    assert d["role"] == "tool"
    assert d["name"] == "create_folder"


def test_tool_definition_format() -> None:
    """ToolDefinition converts to Ollama format."""
    tool = ToolDefinition(
        name="create_folder",
        description="Create a folder",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Folder path"},
            },
            "required": ["path"],
        },
        handler=lambda path: {"success": True},
    )

    fmt = tool.to_ollama_format()
    assert fmt["type"] == "function"
    assert fmt["function"]["name"] == "create_folder"
    assert "parameters" in fmt["function"]
    assert fmt["function"]["parameters"]["properties"]["path"]["type"] == "string"


def test_tool_definition_confirmation_levels() -> None:
    """ToolDefinition supports different confirmation levels."""
    tool_none = ToolDefinition(
        name="list_files",
        description="List files",
        parameters={"type": "object", "properties": {}},
        handler=lambda: [],
        confirmation_level="none",
    )
    assert tool_none.confirmation_level == "none"

    tool_double = ToolDefinition(
        name="delete_file",
        description="Delete a file",
        parameters={"type": "object", "properties": {"path": {"type": "string"}}},
        handler=lambda path: None,
        confirmation_level="double",
    )
    assert tool_double.confirmation_level == "double"


def test_chat_response_properties() -> None:
    """ChatResponse computed properties work."""
    resp = ChatResponse(
        message=ChatMessage(role="assistant", content="Hello"),
        model="mistral:7b",
        total_duration_ns=1_500_000_000,
        tool_calls=[],
    )
    assert not resp.has_tool_calls
    assert resp.duration_ms == 1500.0

    resp_with_tools = ChatResponse(
        message=ChatMessage(role="assistant", content=""),
        model="mistral:7b",
        tool_calls=[{"function": {"name": "test"}}],
    )
    assert resp_with_tools.has_tool_calls


def test_stream_chunk() -> None:
    """StreamChunk holds partial content."""
    chunk = StreamChunk(content="Hola", done=False, model="mistral:7b")
    assert chunk.content == "Hola"
    assert not chunk.done

    final = StreamChunk(content="", done=True, model="mistral:7b")
    assert final.done


def test_client_initialization() -> None:
    """OllamaClient initializes with correct defaults."""
    client = OllamaClient()
    assert client.host == "http://localhost:11434"
    assert client.model == "mistral:7b-instruct-q4_K_M"
    assert client._status == OllamaStatus.DISCONNECTED
    assert len(client.tools) == 0


def test_client_custom_config() -> None:
    """OllamaClient respects custom configuration."""
    client = OllamaClient(
        host="http://custom:1234",
        model="llama3.1:8b",
        timeout=30.0,
    )
    assert client.host == "http://custom:1234"
    assert client.model == "llama3.1:8b"
    assert client.timeout == 30.0


def test_tool_registration() -> None:
    """Tools register and unregister correctly."""
    client = OllamaClient()

    tool = ToolDefinition(
        name="test_tool",
        description="A test tool",
        parameters={"type": "object", "properties": {}},
        handler=lambda: {"ok": True},
    )

    client.register_tool(tool)
    assert "test_tool" in client.tools
    assert len(client._get_tools_list()) == 1

    client.unregister_tool("test_tool")
    assert "test_tool" not in client.tools
    assert len(client._get_tools_list()) == 0


def test_tools_list_format() -> None:
    """Tools list generates correct Ollama format."""
    client = OllamaClient()

    client.register_tool(ToolDefinition(
        name="tool_a",
        description="Tool A",
        parameters={"type": "object", "properties": {"x": {"type": "string"}}},
        handler=lambda x: x,
    ))
    client.register_tool(ToolDefinition(
        name="tool_b",
        description="Tool B",
        parameters={"type": "object", "properties": {}},
        handler=lambda: None,
    ))

    tools = client._get_tools_list()
    assert len(tools) == 2
    assert all(t["type"] == "function" for t in tools)
    names = {t["function"]["name"] for t in tools}
    assert names == {"tool_a", "tool_b"}


def test_tool_execution_blocked() -> None:
    """Blocked tools return error without executing."""
    client = OllamaClient()
    executed = False

    def dangerous_handler() -> dict:
        nonlocal executed
        executed = True
        return {"destroyed": True}

    client.register_tool(ToolDefinition(
        name="format_disk",
        description="Format disk",
        parameters={"type": "object", "properties": {}},
        handler=dangerous_handler,
        confirmation_level="blocked",
    ))

    results = asyncio.run(client.execute_tool_calls([
        {"function": {"name": "format_disk", "arguments": {}}},
    ]))

    assert len(results) == 1
    assert "blocked" in results[0].content.lower() or "security" in results[0].content.lower()
    assert not executed


def test_tool_execution_not_found() -> None:
    """Unknown tools return error."""
    client = OllamaClient()

    results = asyncio.run(client.execute_tool_calls([
        {"function": {"name": "nonexistent", "arguments": {}}},
    ]))

    assert len(results) == 1
    assert "not found" in results[0].content.lower()


def test_tool_execution_success() -> None:
    """Tools execute and return results."""
    client = OllamaClient()

    client.register_tool(ToolDefinition(
        name="add_numbers",
        description="Add two numbers",
        parameters={
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"},
            },
        },
        handler=lambda a, b: {"result": a + b},
    ))

    results = asyncio.run(client.execute_tool_calls([
        {"function": {"name": "add_numbers", "arguments": {"a": 3, "b": 4}}},
    ]))

    assert len(results) == 1
    data = json.loads(results[0].content)
    assert data["result"] == 7


def test_tool_execution_with_confirmation_denied() -> None:
    """Tools requiring confirmation can be denied."""
    client = OllamaClient()

    client.register_tool(ToolDefinition(
        name="delete_file",
        description="Delete file",
        parameters={"type": "object", "properties": {"path": {"type": "string"}}},
        handler=lambda path: {"deleted": path},
        confirmation_level="double",
    ))

    def deny_all(name: str, level: str, args: dict) -> bool:
        return False

    results = asyncio.run(client.execute_tool_calls(
        [{"function": {"name": "delete_file", "arguments": {"path": "/tmp/x"}}}],
        confirm_callback=deny_all,
    ))

    assert len(results) == 1
    assert "cancelled" in results[0].content.lower()


def test_tool_execution_with_confirmation_approved() -> None:
    """Tools requiring confirmation execute when approved."""
    client = OllamaClient()

    client.register_tool(ToolDefinition(
        name="move_file",
        description="Move file",
        parameters={
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "dest": {"type": "string"},
            },
        },
        handler=lambda source, dest: {"moved": True, "from": source, "to": dest},
        confirmation_level="single",
    ))

    def approve_all(name: str, level: str, args: dict) -> bool:
        return True

    results = asyncio.run(client.execute_tool_calls(
        [{"function": {"name": "move_file", "arguments": {"source": "/a", "dest": "/b"}}}],
        confirm_callback=approve_all,
    ))

    assert len(results) == 1
    data = json.loads(results[0].content)
    assert data["moved"] is True


def test_client_with_tools_init() -> None:
    """OllamaClient accepts tools in constructor."""
    tools = [
        ToolDefinition(
            name="tool1",
            description="T1",
            parameters={"type": "object", "properties": {}},
            handler=lambda: None,
        ),
        ToolDefinition(
            name="tool2",
            description="T2",
            parameters={"type": "object", "properties": {}},
            handler=lambda: None,
        ),
    ]

    client = OllamaClient(tools=tools)
    assert len(client.tools) == 2
    assert "tool1" in client.tools
    assert "tool2" in client.tools


# ─── Run all tests ────────────────────────────────────────

if __name__ == "__main__":
    import traceback

    tests = [
        (name, func)
        for name, func in globals().items()
        if name.startswith("test_") and callable(func)
    ]

    passed = 0
    failed = 0

    for name, func in sorted(tests):
        try:
            func()
            passed += 1
            print(f"  ✅ {name}")
        except Exception as e:
            failed += 1
            print(f"  ❌ {name}: {e}")
            traceback.print_exc()

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 50)

    if failed:
        sys.exit(1)
