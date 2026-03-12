"""Tests for the agent ReACT loop with mock backend."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from sigil.agent.loop import AgentLoop, _extract_text
from sigil.agent.tools import ToolRegistry


@dataclass
class MockTextBlock:
    """Mock Anthropic text content block."""

    type: str = "text"
    text: str = ""


@dataclass
class MockToolUseBlock:
    """Mock Anthropic tool_use content block."""

    type: str = "tool_use"
    id: str = "tool_1"
    name: str = ""
    input: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.input is None:
            self.input = {}


@dataclass
class MockResponse:
    """Mock Anthropic API response."""

    content: list[Any] | None = None

    def __post_init__(self) -> None:
        if self.content is None:
            self.content = []


class MockBackend:
    """Mock LLM backend for testing the agent loop."""

    def __init__(self, responses: list[MockResponse] | None = None) -> None:
        self._responses = list(responses or [])
        self._call_count = 0
        self.calls: list[dict[str, Any]] = []

    def chat(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> MockResponse:
        self.calls.append({
            "system": system,
            "messages": messages,
            "tools": tools,
        })
        if self._call_count < len(self._responses):
            resp = self._responses[self._call_count]
        else:
            resp = MockResponse(content=[MockTextBlock(text="No more responses")])
        self._call_count += 1
        return resp


@pytest.fixture()
def tools(tmp_path: Path) -> ToolRegistry:
    return ToolRegistry(tmp_path)


class TestAgentLoop:
    def test_text_only_response(self, tools: ToolRegistry) -> None:
        backend = MockBackend([
            MockResponse(content=[MockTextBlock(text="Hello! I can help.")]),
        ])
        loop = AgentLoop(
            backend=backend,
            tools=tools,
            system_prompt="You are a test agent.",
        )
        result = loop.process_user_message("Hi")
        assert result == "Hello! I can help."

    def test_tool_call_then_response(self, tools: ToolRegistry) -> None:
        backend = MockBackend([
            # First: call validate tool
            MockResponse(content=[
                MockToolUseBlock(
                    name="validate",
                    input={"code": "define X as 42\n"},
                    id="tool_1",
                ),
            ]),
            # Second: return text after seeing tool result
            MockResponse(content=[
                MockTextBlock(text="Code is valid!"),
            ]),
        ])
        loop = AgentLoop(
            backend=backend,
            tools=tools,
            system_prompt="Test",
        )
        result = loop.process_user_message("Validate this code")
        assert result == "Code is valid!"
        # Backend should have been called twice
        assert len(backend.calls) == 2

    def test_tool_result_fed_back(self, tools: ToolRegistry) -> None:
        backend = MockBackend([
            MockResponse(content=[
                MockToolUseBlock(
                    name="validate",
                    input={"code": "define X as 42\n"},
                    id="tool_abc",
                ),
            ]),
            MockResponse(content=[MockTextBlock(text="Done")]),
        ])
        loop = AgentLoop(
            backend=backend,
            tools=tools,
            system_prompt="Test",
        )
        loop.process_user_message("Check this")

        # The second call should have tool_result in messages
        second_call_msgs = backend.calls[1]["messages"]
        # Find the tool_result message
        tool_result_msgs = [
            m for m in second_call_msgs
            if m["role"] == "user" and isinstance(m["content"], list)
        ]
        assert len(tool_result_msgs) == 1
        tool_result = tool_result_msgs[0]["content"][0]
        assert tool_result["tool_use_id"] == "tool_abc"
        # The result should be valid JSON from validate tool
        parsed = json.loads(tool_result["content"])
        assert parsed["valid"] is True

    def test_max_iterations_cap(self, tools: ToolRegistry) -> None:
        # Backend always returns tool calls — should stop at max_iterations
        responses = [
            MockResponse(content=[
                MockToolUseBlock(
                    name="list_project",
                    input={},
                    id=f"tool_{i}",
                ),
            ])
            for i in range(15)
        ]
        backend = MockBackend(responses)
        loop = AgentLoop(
            backend=backend,
            tools=tools,
            system_prompt="Test",
            max_iterations=3,
        )
        result = loop.process_user_message("Loop forever")
        assert "maximum" in result.lower()
        assert len(backend.calls) == 3

    def test_conversation_history_preserved(
        self, tools: ToolRegistry,
    ) -> None:
        backend = MockBackend([
            MockResponse(content=[MockTextBlock(text="First response")]),
            MockResponse(content=[MockTextBlock(text="Second response")]),
        ])
        loop = AgentLoop(
            backend=backend,
            tools=tools,
            system_prompt="Test",
        )
        loop.process_user_message("First message")
        loop.process_user_message("Second message")

        # Second call should have full history
        assert len(backend.calls[1]["messages"]) > 2

    def test_reset_clears_history(self, tools: ToolRegistry) -> None:
        backend = MockBackend([
            MockResponse(content=[MockTextBlock(text="R1")]),
            MockResponse(content=[MockTextBlock(text="R2")]),
        ])
        loop = AgentLoop(
            backend=backend,
            tools=tools,
            system_prompt="Test",
        )
        loop.process_user_message("Hello")
        assert loop.turn_count == 1
        loop.reset()
        assert loop.turn_count == 0
        loop.process_user_message("Fresh start")
        # After reset, first user message in the new call is "Fresh start"
        second_msgs = backend.calls[1]["messages"]
        user_msgs = [m for m in second_msgs if m["role"] == "user"
                     and isinstance(m["content"], str)]
        assert user_msgs[0]["content"] == "Fresh start"

    def test_turn_count(self, tools: ToolRegistry) -> None:
        backend = MockBackend([
            MockResponse(content=[MockTextBlock(text="R1")]),
            MockResponse(content=[MockTextBlock(text="R2")]),
        ])
        loop = AgentLoop(
            backend=backend,
            tools=tools,
            system_prompt="Test",
        )
        assert loop.turn_count == 0
        loop.process_user_message("One")
        assert loop.turn_count == 1
        loop.process_user_message("Two")
        assert loop.turn_count == 2

    def test_multiple_tool_calls(self, tools: ToolRegistry) -> None:
        backend = MockBackend([
            MockResponse(content=[
                MockToolUseBlock(
                    name="validate",
                    input={"code": "define A as 1\n"},
                    id="t1",
                ),
                MockToolUseBlock(
                    name="list_project",
                    input={},
                    id="t2",
                ),
            ]),
            MockResponse(content=[MockTextBlock(text="Both done")]),
        ])
        loop = AgentLoop(
            backend=backend,
            tools=tools,
            system_prompt="Test",
        )
        result = loop.process_user_message("Do two things")
        assert result == "Both done"

    def test_unknown_tool_handled(self, tools: ToolRegistry) -> None:
        backend = MockBackend([
            MockResponse(content=[
                MockToolUseBlock(
                    name="nonexistent",
                    input={},
                    id="t1",
                ),
            ]),
            MockResponse(content=[MockTextBlock(text="Handled error")]),
        ])
        loop = AgentLoop(
            backend=backend,
            tools=tools,
            system_prompt="Test",
        )
        result = loop.process_user_message("Call unknown tool")
        assert result == "Handled error"


class TestExtractText:
    def test_single_text_block(self) -> None:
        blocks = [MockTextBlock(text="Hello")]
        assert _extract_text(blocks) == "Hello"

    def test_mixed_blocks(self) -> None:
        blocks = [
            MockTextBlock(text="Before"),
            MockToolUseBlock(name="validate"),
            MockTextBlock(text="After"),
        ]
        assert _extract_text(blocks) == "Before\nAfter"

    def test_empty(self) -> None:
        assert _extract_text([]) == ""
