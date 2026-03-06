"""Interactive REPL for the Sigil language."""

from __future__ import annotations

from dataclasses import dataclass, field

from sigil.ast import nodes as ast
from sigil.errors import SigilError
from sigil.interpreter.environment import Environment
from sigil.interpreter.evaluator import Evaluator
from sigil.interpreter.trace import format_trace
from sigil.interpreter.values import Value, format_value
from sigil.lexer import tokenize
from sigil.parser import parse

# Keywords that indicate the input is a top-level declaration
_DECLARATION_KEYWORDS = frozenset({
    "define", "type", "compute", "neural", "rule", "import", "from", "module",
})

# Keywords that indicate the input is a statement (wrap in main:)
_STATEMENT_KEYWORDS = frozenset({
    "given", "for", "if", "return", "evaluate",
})


@dataclass
class ReplOutput:
    """Output from processing a single REPL input."""

    lines: list[str] = field(default_factory=list)
    result: Value = None
    show_result: bool = False


class ReplSession:
    """Holds persistent state across REPL inputs."""

    def __init__(self) -> None:
        self._evaluator = Evaluator()
        self._env = Environment()
        self._rules: list[ast.RuleDecl] = []
        self.trace_on: bool = False

    @property
    def env(self) -> Environment:
        return self._env

    @property
    def rules(self) -> list[ast.RuleDecl]:
        return list(self._rules)

    @property
    def compute_funcs(self) -> dict[str, ast.ComputeDecl]:
        return dict(self._evaluator._compute_funcs)

    @property
    def type_defs(self) -> dict[str, ast.TypeDecl]:
        return dict(self._evaluator._type_defs)

    def process_input(self, text: str) -> ReplOutput:
        """Process a single REPL input and return output."""
        stripped = text.strip()
        if not stripped:
            return ReplOutput()

        # Special commands
        if stripped.startswith(":"):
            return self._handle_command(stripped)

        # Classify and prepare source
        source = self._prepare_source(stripped)
        is_expr = self._is_expression_input(stripped)

        # Lex → parse → evaluate
        try:
            tokens = tokenize(source, "<repl>")
            program = parse(tokens, "<repl>")
            result, trace, self._env = self._evaluator.eval_program_repl(
                program, self._env, self._rules,
            )
        except SigilError as e:
            return ReplOutput(lines=[f"Error: {e}"])

        output = ReplOutput()

        # Collect print output
        output.lines.extend(trace.output_lines)

        # Show trace if toggled on
        if self.trace_on and trace.rule_traces:
            output.lines.append(format_trace(trace))

        # Show result for bare expressions only
        if is_expr and result is not None:
            output.result = result
            output.show_result = True

        return output

    def _prepare_source(self, text: str) -> str:
        """Classify input and wrap if needed."""
        first_word = text.split()[0] if text.split() else ""

        if first_word in _DECLARATION_KEYWORDS:
            return text

        # Statements and expressions get wrapped in a main block
        # Indent each line
        indented = "\n".join("  " + line for line in text.splitlines())
        return f"main:\n{indented}"

    def _is_expression_input(self, text: str) -> bool:
        """Check if input is a bare expression (should show => result)."""
        first_word = text.split()[0] if text.split() else ""
        return (
            first_word not in _DECLARATION_KEYWORDS
            and first_word not in _STATEMENT_KEYWORDS
        )

    def _handle_command(self, cmd: str) -> ReplOutput:
        """Handle special :commands."""
        cmd = cmd.strip()

        if cmd == ":env":
            return self._cmd_env()
        if cmd == ":rules":
            return self._cmd_rules()
        if cmd == ":funcs":
            return self._cmd_funcs()
        if cmd == ":types":
            return self._cmd_types()
        if cmd == ":trace":
            self.trace_on = not self.trace_on
            state = "on" if self.trace_on else "off"
            return ReplOutput(lines=[f"Trace: {state}"])
        if cmd == ":reset":
            self._evaluator = Evaluator()
            self._env = Environment()
            self._rules = []
            return ReplOutput(lines=["Session reset."])
        if cmd == ":help":
            return self._cmd_help()

        return ReplOutput(lines=[f"Unknown command: {cmd}. Type :help for help."])

    def _cmd_env(self) -> ReplOutput:
        bindings = self._env.all_bindings()
        if not bindings:
            return ReplOutput(lines=["  (empty)"])
        lines = [f"  {name} = {format_value(val)}" for name, val in sorted(bindings.items())]
        return ReplOutput(lines=lines)

    def _cmd_rules(self) -> ReplOutput:
        if not self._rules:
            return ReplOutput(lines=["  (no rules)"])
        lines = [
            f"  {r.name} (priority {r.priority})" for r in self._rules
        ]
        return ReplOutput(lines=lines)

    def _cmd_funcs(self) -> ReplOutput:
        funcs = self._evaluator._compute_funcs
        if not funcs:
            return ReplOutput(lines=["  (no functions)"])
        lines = []
        for name, decl in sorted(funcs.items()):
            params = ", ".join(p.name for p in decl.params)
            lines.append(f"  {name}({params})")
        return ReplOutput(lines=lines)

    def _cmd_types(self) -> ReplOutput:
        types = self._evaluator._type_defs
        if not types:
            return ReplOutput(lines=["  (no types)"])
        lines = [f"  {name}" for name in sorted(types)]
        return ReplOutput(lines=lines)

    def _cmd_help(self) -> ReplOutput:
        return ReplOutput(lines=[
            "Sigil REPL commands:",
            "  :env     Show current environment bindings",
            "  :rules   Show defined rules",
            "  :funcs   Show defined compute functions",
            "  :types   Show defined types",
            "  :trace   Toggle execution trace display",
            "  :reset   Reset session (clear all state)",
            "  :help    Show this help",
            "  exit     Exit the REPL",
        ])


def needs_continuation(text: str) -> bool:
    """Check if input needs more lines (multi-line detection)."""
    lines = text.splitlines()
    if not lines:
        return False
    last = lines[-1]

    # Last line ends with colon → block start
    if last.rstrip().endswith(":"):
        return True

    # Unbalanced brackets
    open_count = text.count("[") + text.count("(")
    close_count = text.count("]") + text.count(")")
    return open_count > close_count


def run_repl() -> None:
    """Run the interactive REPL loop."""
    print("Sigil REPL v0.1.0")
    print("Type :help for commands, 'exit' to quit.\n")

    session = ReplSession()
    buffer: list[str] = []

    while True:
        try:
            prompt = "sigil> " if not buffer else "  ...> "
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            break

        # Exit commands
        if not buffer and line.strip() in ("exit", "quit"):
            break

        buffer.append(line)
        text = "\n".join(buffer)

        # Multi-line: continue if needed (unless empty line ends block)
        if buffer and needs_continuation(text) and line.strip():
            continue

        # Process complete input
        buffer = []
        output = session.process_input(text)

        for out_line in output.lines:
            print(out_line)
        if output.show_result:
            print(f"=> {format_value(output.result)}")
