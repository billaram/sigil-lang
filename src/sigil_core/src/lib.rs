use pyo3::prelude::*;

mod matcher;
mod solver;
mod trace;
mod values;
mod verifier;
mod vm;

/// Sigil performance core — Rust extensions via PyO3.
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
