"""Agent loop — ReACT cycle via Anthropic tool_use API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from sigil.agent.tools import ToolRegistry


class AgentBackend(Protocol):
    """Protocol for LLM backends that support tool use."""

    def chat(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> Any: ...


class AnthropicAgentBackend:
    """Anthropic Claude backend with tool_use support."""

    def __init__(self, model: str = "claude-sonnet-4-20250514") -> None:
        self._model = model
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                import anthropic
            except ImportError as err:
                msg = (
                    "anthropic package not installed. "
                    "Install with: pip install anthropic"
                )
                raise ImportError(msg) from err
            self._client = anthropic.Anthropic()
        return self._client

    def chat(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> Any:
        client = self._get_client()
        return client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system,
            messages=messages,
            tools=tools,
        )


@dataclass
class AgentLoop:
    """ReACT agent loop that iterates between LLM and tools."""

    backend: AgentBackend
    tools: ToolRegistry
    system_prompt: str
    max_iterations: int = 10
    _messages: list[dict[str, Any]] = field(default_factory=list)

    @property
    def messages(self) -> list[dict[str, Any]]:
        """Current conversation messages."""
        return list(self._messages)

    @property
    def turn_count(self) -> int:
        """Number of user turns so far."""
        return sum(1 for m in self._messages if m["role"] == "user"
                   and isinstance(m["content"], str))

    def reset(self) -> None:
        """Clear conversation history."""
        self._messages.clear()

    def trim_history(self, max_turns: int = 20) -> None:
        """Keep only the last N user-assistant turn pairs."""
        if self.turn_count <= max_turns:
            return
        # Find the index of the Nth-from-end user message
        user_count = 0
        cut_idx = 0
        for i in range(len(self._messages) - 1, -1, -1):
            msg = self._messages[i]
            if msg["role"] == "user" and isinstance(msg["content"], str):
                user_count += 1
                if user_count >= max_turns:
                    cut_idx = i
                    break
        self._messages = self._messages[cut_idx:]

    def process_user_message(self, message: str) -> str:
        """Process a user message through the ReACT loop.

        Returns the final text response from the agent.
        """
        self._messages.append({"role": "user", "content": message})
        self.trim_history()

        tool_defs = self.tools.api_definitions()

        for _ in range(self.max_iterations):
            response = self.backend.chat(
                system=self.system_prompt,
                messages=self._messages,
                tools=tool_defs,
            )

            # Store assistant response
            self._messages.append({
                "role": "assistant",
                "content": response.content,
            })

            # Extract tool use blocks
            tool_uses = [
                block for block in response.content
                if block.type == "tool_use"
            ]

            if not tool_uses:
                # No tool calls — extract text and return
                return _extract_text(response.content)

            # Execute each tool and feed results back
            tool_results = []
            for tool_use in tool_uses:
                result = self.tools.execute(tool_use.name, tool_use.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result,
                })

            self._messages.append({
                "role": "user",
                "content": tool_results,
            })

        return "Reached maximum tool call iterations. Please try again."


def _extract_text(content: list[Any]) -> str:
    """Extract text from Anthropic response content blocks."""
    parts = []
    for block in content:
        if hasattr(block, "text"):
            parts.append(block.text)
    return "\n".join(parts) if parts else ""
