#[cfg(feature = "pyo3-ext")]
use pyo3::prelude::*;

// Modules that are only used via PyO3
#[cfg(feature = "pyo3-ext")]
mod matcher;
#[cfg(feature = "pyo3-ext")]
mod solver;
#[cfg(feature = "pyo3-ext")]
mod trace;
#[cfg(feature = "pyo3-ext")]
mod values;
#[cfg(feature = "pyo3-ext")]
mod verifier;

// VM module — core types are platform-agnostic, PyO3 wrapper is gated internally
pub mod vm;

// WASM frontend — lexer, parser, compiler (platform-agnostic Rust)
pub mod lexer;
pub mod parser;
pub mod compiler;

#[cfg(feature = "wasm")]
mod wasm;

/// Sigil performance core — Rust extensions via PyO3.
#[cfg(feature = "pyo3-ext")]
#[pymodule]
fn _sigil_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", "0.1.0")?;

    // Pattern matcher
    m.add_class::<matcher::ReteNetwork>()?;

    // Constraint solver
    m.add_class::<solver::ConstraintSolver>()?;

    // Trace serialization
    m.add_function(wrap_pyfunction!(trace::serialize_trace_json, m)?)?;
    m.add_function(wrap_pyfunction!(trace::serialize_trace_compact, m)?)?;

    // Formal verification
    m.add_function(wrap_pyfunction!(verifier::verify_program, m)?)?;

    // Bytecode VM
    m.add_class::<vm::SigilVM>()?;

    Ok(())
}
