# Language Interoperability: Deep Dive

How successful languages achieve FFI, and what Sigil should learn from them.

---

## 1. The JVM Model: Clojure, Kotlin, Scala

### Clojure → Java (The Hosted Language Pattern)

Clojure was designed from day one as a **hosted language** on the JVM. This is the most relevant pattern for Sigil's Python hosting.

**How it works**:
- Every Clojure function compiles to a JVM class implementing `IFn`
- Clojure data structures implement standard Java interfaces (`java.util.List`, `java.util.Map`)
- Java objects are Clojure objects — no wrapper, no proxy, no copying
- The same GC manages everything

**Interop syntax**:
```clojure
;; Call Java methods (zero overhead — same as javac output)
(.toUpperCase "hello")        ;; → "HELLO"

;; Create Java objects
(java.util.HashMap.)          ;; new HashMap()

;; Access fields
(.-length "hello")            ;; .length

;; Type hints eliminate reflection (performance)
(defn fast-length [^String s] (.length s))
```

**Performance**:
- Without type hints: reflection-based dispatch (~100x slower)
- With type hints: identical bytecode to Java (~0 overhead)

**Clojure's interop design choices relevant to Sigil**:
1. Host objects are first-class (no wrapping)
2. Type hints are optional but available for performance
3. The host's type system is accessible but not mandatory
4. Interop is syntactically lightweight (not a ceremony)

### Kotlin → Java

Kotlin takes a different approach: 100% Java-compatible by design.

- Every Kotlin class IS a JVM class
- Kotlin can extend Java classes, implement Java interfaces
- Java code can use Kotlin classes without knowing they're Kotlin
- `@JvmStatic`, `@JvmOverloads` annotations for Java-friendly APIs

**Key difference from Clojure**: Kotlin aims for full bidirectional compatibility. Clojure aims for "Java is available when needed."

**Sigil parallel**: Sigil should follow Clojure's approach — Python is available when needed, but Sigil doesn't try to be Python-compatible at the class level.

### Scala → Java

Scala's interop is more complex due to its richer type system (higher-kinded types, implicits, path-dependent types). These features don't map cleanly to JVM bytecode, leading to:
- Complex name mangling
- Unexpected boxing/unboxing
- Binary compatibility challenges across Scala versions

**Lesson for Sigil**: Don't try to map Sigil's full type system through the FFI boundary. Keep the boundary simple (basic types, records, lists).

---

## 2. The C ABI Model: Zig, Rust

### Zig → C (Zero-Cost Interop)

Zig has the most seamless C interop of any modern language:

```zig
// Import and use C headers directly
const c = @cImport({
    @cInclude("stdio.h");
    @cInclude("stdlib.h");
});

pub fn main() void {
    _ = c.printf("Hello from Zig calling C!\n");
    const ptr = c.malloc(100);
    defer c.free(ptr);
}
```

**How it works**:
- `@cImport` invokes an embedded Clang compiler to parse C headers
- C types are automatically mapped to Zig types
- C functions are called with zero overhead (direct call, same ABI)
- Zig can serve as a C compiler: `zig cc -o output file.c`
- Zig's build system can compile C/C++ sources as part of the build

**Why this is impressive**:
- No binding generator step (no SWIG, no bindgen)
- No FFI declaration files
- Changes to C headers automatically propagate
- Even handles C preprocessor macros (translates to Zig comptime)

**What Zig CAN'T do**: C++ interop (C++ ABI is not stable). Only C ABI.

### Rust → C (Safe but Manual)

```rust
// Declare external C functions
extern "C" {
    fn printf(format: *const c_char, ...) -> c_int;
    fn malloc(size: size_t) -> *mut c_void;
    fn free(ptr: *mut c_void);
}

// Call within unsafe block
unsafe {
    printf(b"Hello from Rust!\n\0".as_ptr() as *const c_char);
}
```

**How it works**:
- `extern "C"` blocks declare C-ABI functions
- All C FFI calls require `unsafe` (Rust can't verify C memory safety)
- `bindgen` tool auto-generates Rust declarations from C headers
- `cc` crate compiles C sources as part of cargo build

**Rust's C++ story**:
- `cxx` crate: Safe C++ interop via a bridge DSL
- `autocxx`: Automated C++ binding generation
- Neither is zero-cost or fully automatic like Zig's C interop

---

## 3. The PyO3/maturin Model (Sigil's Choice)

### PyO3: Rust ↔ Python Binding

PyO3 is the bridge between Sigil's Python interpreter and its Rust core.

```rust
use pyo3::prelude::*;

/// A Rust function callable from Python
#[pyfunction]
fn evaluate_rules(rules: Vec<Rule>, facts: HashMap<String, Value>) -> PyResult<Decision> {
    let engine = RuleEngine::new(&rules);
    let result = engine.evaluate(&facts);
    Ok(result.into())
}

/// A Rust class usable from Python
#[pyclass]
struct ConstraintSolver {
    constraints: Vec<Constraint>,
}

#[pymethods]
impl ConstraintSolver {
    #[new]
    fn new() -> Self {
        ConstraintSolver { constraints: vec![] }
    }

    fn add_constraint(&mut self, constraint: Constraint) {
        self.constraints.push(constraint);
    }

    fn solve(&self, facts: &Facts) -> PyResult<Solution> {
        // Rust-speed solving
        Ok(internal_solve(&self.constraints, facts)?)
    }
}

/// Register the module
#[pymodule]
fn sigil_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(evaluate_rules, m)?)?;
    m.add_class::<ConstraintSolver>()?;
    Ok(())
}
```

**Type marshaling** (PyO3 handles automatically):

| Python Type | Rust Type | Overhead |
|------------|-----------|----------|
| `int` | `i64` / `i32` | Zero (unbox) |
| `float` | `f64` | Zero (unbox) |
| `str` | `String` / `&str` | Copy (UTF-8 verified) |
| `bool` | `bool` | Zero |
| `list` | `Vec<T>` | Copy (element-wise) |
| `dict` | `HashMap<K,V>` | Copy (element-wise) |
| `None` | `Option<T>` | Zero |
| Any Python object | `PyObject` / `Py<T>` | Reference (zero copy) |

**Performance**:
- Function call overhead: ~100ns per call (negligible for rule evaluation)
- Type conversion: proportional to data size (list of 1000 items ≈ 10μs)
- For hot paths: keep data in Rust, minimize Python↔Rust crossings

### maturin: Build System

maturin handles building and packaging Rust extensions for Python:

```bash
# Development (builds and installs in current venv)
maturin develop

# Production wheel
maturin build --release

# Publish to PyPI
maturin publish
```

**Integration with pyproject.toml**:
```toml
[build-system]
requires = ["maturin>=1.5,<2.0"]
build-backend = "maturin"

[tool.maturin]
module-name = "sigil._sigil_core"
features = ["pyo3/extension-module"]
```

---

## 4. Sigil's Interop Architecture

### Layer 1: Python FFI (Implicit Hosting)

Since Sigil's interpreter runs on Python, Python interop is "free":

```python
# In the Sigil interpreter
def evaluate_python_import(module_path: str) -> Any:
    """Import a Python module and make it available in Sigil."""
    return importlib.import_module(module_path)

def call_python_function(func: Callable, args: list, kwargs: dict) -> SigilValue:
    """Call a Python function and convert result to Sigil value."""
    result = func(*args, **kwargs)
    return marshal_python_to_sigil(result)
```

**Type boundary**:
```
Sigil Number    ↔  Python int/float
Sigil Text      ↔  Python str
Sigil Boolean   ↔  Python bool
Sigil Symbol    ↔  Python str (with ":" prefix convention)
Sigil List[T]   ↔  Python list (with element marshaling)
Sigil Record    ↔  Python dict / dataclass
Sigil Option[T] ↔  Python Optional[T]
Sigil None      ↔  Python None
```

### Layer 2: Rust FFI (Via PyO3)

Rust functions are exposed as Python functions, which Sigil calls transparently:

```
Sigil code → Sigil interpreter (Python) → sigil_core (Rust via PyO3) → result
```

The Sigil programmer doesn't need to know whether a function runs in Python or Rust. The `using rust` directive is an optimization hint, not a requirement.

### Layer 3: Neural Bridge (Via Python ML Libraries)

```
Sigil `neural` declaration → Python interpreter → transformers/torch → result with confidence
```

The neural bridge wraps Python ML libraries with Sigil-specific guarantees:
- Confidence scoring
- Fallback behavior
- Type checking on output
- Trace logging (neural vs symbolic)

---

## 5. Interop Design Principles for Sigil

Drawing from all studied languages:

| Principle | Source | Sigil Application |
|-----------|--------|-------------------|
| Host objects are first-class | Clojure | Python objects usable directly in Sigil |
| Interop is syntactically lightweight | Clojure, Zig | `import python pandas as pd` — one line |
| Type hints for performance | Clojure | Type annotations at FFI boundary optional but helpful |
| Unsafe boundary is explicit | Rust | `neural` keyword marks non-deterministic boundary |
| Build integration is seamless | Zig, maturin | `maturin develop` builds Python + Rust together |
| FFI types are simple | All | Only basic types cross the boundary |
| Errors translate cleanly | PyO3 | Python exceptions → Sigil errors with context |
