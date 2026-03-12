"""Interactive session for Sigil Code agent."""

from __future__ import annotations

import sys
from pathlib import Path

from sigil.agent.loop import AgentLoop, AnthropicAgentBackend
from sigil.agent.prompts import build_agent_system_prompt
from sigil.agent.tools import ToolRegistry


class SigilCodeSession:
    """Manages the interactive Sigil Code agent session."""

    def __init__(
        self,
        working_dir: Path | None = None,
        model: str = "claude-sonnet-4-20250514",
        backend: object | None = None,
    ) -> None:
        self._working_dir = (working_dir or Path.cwd()).resolve()
        self._tools = ToolRegistry(self._working_dir)
        self._backend = backend or AnthropicAgentBackend(model)
        self._loop = AgentLoop(
            backend=self._backend,
            tools=self._tools,
            system_prompt=build_agent_system_prompt(),
        )

    @property
    def working_dir(self) -> Path:
        return self._working_dir

    @property
    def turn_count(self) -> int:
        return self._loop.turn_count

    def process(self, message: str) -> str:
        """Send a message to the agent and return the response."""
        return self._loop.process_user_message(message)

    def reset(self) -> None:
        """Reset conversation history."""
        self._loop.reset()

    def list_files(self) -> list[str]:
        """List .sigil files in the working directory."""
        return [
            str(f.relative_to(self._working_dir))
            for f in sorted(self._working_dir.rglob("*.sigil"))
        ]

    def handle_local_command(self, cmd: str) -> str | None:
        """Handle local :commands. Returns response or None if not a command."""
        cmd = cmd.strip()
        if not cmd.startswith(":"):
            return None

        if cmd == ":help":
            return (
                "Sigil Code commands:\n"
                "  :help     Show this help\n"
                "  :reset    Clear conversation history\n"
                "  :files    List .sigil files in working directory\n"
                "  :history  Show conversation turn count\n"
                "  :pwd      Show working directory"
            )
        if cmd == ":reset":
            self.reset()
            return "Conversation reset."
        if cmd == ":files":
            files = self.list_files()
            if not files:
                return "No .sigil files found."
            lines = [f"  {f}" for f in files]
            return "\n".join(lines)
        if cmd == ":history":
            return f"Conversation turns: {self.turn_count}"
        if cmd == ":pwd":
            return f"Working directory: {self._working_dir}"

        return f"Unknown command: {cmd}. Type :help for commands."


def _setup_readline() -> None:
    """Set up readline for history and basic completion."""
    try:
        import readline
    except ImportError:
        return

    import atexit
    import contextlib

    history_file = Path.home() / ".sigil_code_history"
    with contextlib.suppress(FileNotFoundError):
        readline.read_history_file(str(history_file))
    readline.set_history_length(1000)
    atexit.register(readline.write_history_file, str(history_file))

    # Basic command completion
    commands = [":help", ":reset", ":files", ":history", ":pwd", "exit"]

    def completer(text: str, state: int) -> str | None:
        matches = [c for c in commands if c.startswith(text)]
        if state < len(matches):
            return matches[state]
        return None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")


def run_agent_session(
    working_dir: Path | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> None:
    """Run the interactive Sigil Code agent session."""
    print("Sigil Code v0.1.0 — AI assistant for the Sigil language")
    print("Type 'exit' to quit, ':help' for commands.\n")

    session = SigilCodeSession(working_dir=working_dir, model=model)
    _setup_readline()

    while True:
        try:
            user_input = input("sigil-code> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        stripped = user_input.strip()
        if not stripped:
            continue
        if stripped in ("exit", "quit"):
            break

        # Handle local commands
        local_result = session.handle_local_command(stripped)
        if local_result is not None:
            print(local_result)
            continue

        # Send to agent
        try:
            response = session.process(stripped)
            print(response)
        except ImportError as e:
            print(f"[sigil-code] Error: {e}", file=sys.stderr)
            break
        except Exception as e:
            print(f"[sigil-code] Error: {e}", file=sys.stderr)
