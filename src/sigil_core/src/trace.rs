//! Trace serialization for Sigil execution traces.
//!
//! Provides fast JSON serialization of trace data from Rust.

use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// A serializable condition trace.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConditionTraceData {
    pub description: String,
    pub result: bool,
    pub skipped: bool,
}

/// A serializable rule trace.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RuleTraceData {
    pub rule_name: String,
    pub priority: i64,
    pub fired: bool,
    pub conditions: Vec<ConditionTraceData>,
    pub action_description: Option<String>,
    pub explain: Option<String>,
    pub duration_ms: f64,
}

/// A serializable neural trace.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NeuralTraceData {
    pub function_name: String,
    pub model_id: String,
    pub confidence: f64,
    pub threshold: f64,
    pub used_fallback: bool,
    pub latency_ms: f64,
    pub error: Option<String>,
}

/// A serializable program trace.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProgramTraceData {
    pub rule_traces: Vec<RuleTraceData>,
    pub neural_traces: Vec<NeuralTraceData>,
    pub output_lines: Vec<String>,
    pub total_duration_ms: f64,
}

/// Serialize a program trace (given as a Python dict) to JSON.
#[pyfunction]
pub fn serialize_trace_json(trace_dict: HashMap<String, PyObject>, py: Python<'_>) -> PyResult<String> {
    let trace = extract_trace_data(trace_dict, py)?;
    serde_json::to_string_pretty(&trace)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("JSON serialization failed: {}", e)))
}

/// Serialize a program trace to compact JSON (no whitespace).
#[pyfunction]
pub fn serialize_trace_compact(trace_dict: HashMap<String, PyObject>, py: Python<'_>) -> PyResult<String> {
    let trace = extract_trace_data(trace_dict, py)?;
    serde_json::to_string(&trace)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("JSON serialization failed: {}", e)))
}

fn extract_trace_data(
    trace_dict: HashMap<String, PyObject>,
    py: Python<'_>,
) -> PyResult<ProgramTraceData> {
    let rule_traces = extract_rule_traces(&trace_dict, py)?;
    let neural_traces = extract_neural_traces(&trace_dict, py)?;
    let output_lines = extract_string_list(&trace_dict, "output_lines", py)?;
    let total_duration_ms = trace_dict
        .get("total_duration_ms")
        .map(|v| v.extract::<f64>(py))
        .transpose()?
        .unwrap_or(0.0);

    Ok(ProgramTraceData {
        rule_traces,
        neural_traces,
        output_lines,
        total_duration_ms,
    })
}

fn extract_rule_traces(
    trace_dict: &HashMap<String, PyObject>,
    py: Python<'_>,
) -> PyResult<Vec<RuleTraceData>> {
    let Some(rules_obj) = trace_dict.get("rule_traces") else {
        return Ok(Vec::new());
    };
    let rules_list = rules_obj.bind(py);
    let mut traces = Vec::new();

    for item in rules_list.try_iter()? {
        let item: Bound<'_, PyAny> = item?;
        traces.push(RuleTraceData {
            rule_name: item.getattr("rule_name")?.extract()?,
            priority: item.getattr("priority")?.extract()?,
            fired: item.getattr("fired")?.extract()?,
            conditions: extract_condition_traces(&item)?,
            action_description: item
                .getattr("action_description")
                .ok()
                .and_then(|v: Bound<'_, PyAny>| v.extract().ok()),
            explain: item
                .getattr("explain")
                .ok()
                .and_then(|v: Bound<'_, PyAny>| v.extract().ok()),
            duration_ms: item
                .getattr("duration_ms")
                .ok()
                .and_then(|v: Bound<'_, PyAny>| v.extract().ok())
                .unwrap_or(0.0),
        });
    }
    Ok(traces)
}

fn extract_condition_traces(rule_obj: &Bound<'_, PyAny>) -> PyResult<Vec<ConditionTraceData>> {
    let conditions = rule_obj.getattr("conditions")?;
    let mut traces = Vec::new();
    for item in conditions.try_iter()? {
        let item: Bound<'_, PyAny> = item?;
        traces.push(ConditionTraceData {
            description: item.getattr("description")?.extract()?,
            result: item.getattr("result")?.extract()?,
            skipped: item
                .getattr("skipped")
                .ok()
                .and_then(|v: Bound<'_, PyAny>| v.extract().ok())
                .unwrap_or(false),
        });
    }
    Ok(traces)
}

fn extract_neural_traces(
    trace_dict: &HashMap<String, PyObject>,
    py: Python<'_>,
) -> PyResult<Vec<NeuralTraceData>> {
    let Some(neural_obj) = trace_dict.get("neural_traces") else {
        return Ok(Vec::new());
    };
    let neural_list = neural_obj.bind(py);
    let mut traces = Vec::new();

    for item in neural_list.try_iter()? {
        let item: Bound<'_, PyAny> = item?;
        traces.push(NeuralTraceData {
            function_name: item.getattr("function_name")?.extract()?,
            model_id: item.getattr("model_id")?.extract()?,
            confidence: item.getattr("confidence")?.extract()?,
            threshold: item.getattr("threshold")?.extract()?,
            used_fallback: item.getattr("used_fallback")?.extract()?,
            latency_ms: item
                .getattr("latency_ms")
                .ok()
                .and_then(|v: Bound<'_, PyAny>| v.extract().ok())
                .unwrap_or(0.0),
            error: item
                .getattr("error")
                .ok()
                .and_then(|v: Bound<'_, PyAny>| v.extract().ok()),
        });
    }
    Ok(traces)
}

fn extract_string_list(
    trace_dict: &HashMap<String, PyObject>,
    key: &str,
    py: Python<'_>,
) -> PyResult<Vec<String>> {
    let Some(obj) = trace_dict.get(key) else {
        return Ok(Vec::new());
    };
    obj.extract::<Vec<String>>(py)
}
