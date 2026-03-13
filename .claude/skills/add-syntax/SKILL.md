---
description: 10-step workflow for adding new language syntax to Sigil
---

# Add Syntax

Structured workflow for adding a new syntactic construct to the Sigil language.

## Steps

1. **Specify**: Describe the new syntax in natural language. Write 2-3 example `.sigil` snippets showing usage.

2. **Grammar**: Add the production rule to `docs/spec/GRAMMAR.peg`. Ensure it's unambiguous and fits the PEG precedence.

3. **Token**: If new keywords are needed, add to `TokenType` enum in `src/sigil/lexer/tokens.py` and to `KEYWORDS` set.

4. **Lexer tests**: Add lexer tests in `tests/lexer/` verifying the new tokens are produced.

5. **AST node**: Add frozen dataclass to `src/sigil/ast/nodes.py`. Use tuples for sequences. Include `SourceLocation`.

6. **Parser**: Add `_parse_X()` method to `src/sigil/parser/parser.py`. Wire into the right precedence level.

7. **Parser tests**: Add parser tests in `tests/parser/` for happy path + error cases.

8. **Semantics**: Define what the construct means in `docs/spec/SEMANTICS.md`.

9. **Interpreter**: Add evaluation logic to `src/sigil/interpreter/evaluator.py`. Add interpreter tests.

10. **Type checker**: Add type checking logic if applicable. Add type checker tests.

## Validation

After all steps:
```bash
source .venv/bin/activate && pytest tests/ -v --tb=short
source .venv/bin/activate && ruff check src/ tests/
```

Update `ai_docs/STATUS.md` and `docs/spec/GRAMMAR.peg` with the changes.
