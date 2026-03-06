use pyo3::prelude::*;

/// Sigil performance core — Rust extensions via PyO3.
/// Currently a stub. Will contain performance-critical lexer/parser/interpreter code.
#[pymodule]
fn _sigil_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", "0.1.0")?;
    Ok(())
}
