# Hello World

The simplest Sigil program — a single constant and a single rule.

**Source:** `examples/basics/hello.sigil`

---

## Full source

```sigil
-- hello.sigil
-- The simplest Sigil program: a single rule evaluation

define greeting as "Hello from Sigil!" -- (1)!

rule hello_world: -- (2)!
  when true -- (3)!
  then print greeting -- (4)!
  explain "This is the simplest possible Sigil program" -- (5)!
```

1. `define` creates an immutable constant. `greeting` holds the text `"Hello from Sigil!"`.
2. `rule` declares a named rule. Rules are the primary construct in Sigil.
3. `when true` means this rule always fires — there's no condition to check.
4. `then print greeting` is the action — it prints the value of `greeting`.
5. `explain` attaches a human-readable reason to the rule's execution trace.

---

## Running it

```bash
sigil run examples/basics/hello.sigil
```

Output:

```
Hello from Sigil!
```

With trace:

```bash
sigil run examples/basics/hello.sigil --trace
```

---

## Key concepts

- **`define`** creates immutable constants
- **`rule`** declares a named rule with a condition (`when`) and action (`then`)
- **`explain`** provides an audit-trail explanation for why the rule fired
- **`when true`** is the simplest condition — the rule always fires
