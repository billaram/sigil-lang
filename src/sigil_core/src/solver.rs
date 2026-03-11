//! Lightweight constraint solver for Sigil.
//!
//! Solves numeric constraints, range checks, set membership, and boolean logic.

use pyo3::prelude::*;
use std::collections::HashMap;

use crate::values::SigilValue;

/// A constraint on a variable.
#[derive(Debug, Clone)]
pub enum Constraint {
    Equals(SigilValue),
    NotEquals(SigilValue),
    GreaterThan(f64),
    LessThan(f64),
    Between(f64, f64),
    OneOf(Vec<SigilValue>),
}

/// Constraint solver — checks if a set of variable bindings satisfies constraints.
#[pyclass]
pub struct ConstraintSolver {
    constraints: HashMap<String, Vec<Constraint>>,
}

#[pymethods]
impl ConstraintSolver {
    #[new]
    pub fn new() -> Self {
        ConstraintSolver {
            constraints: HashMap::new(),
        }
    }

    /// Add an equality constraint: variable == value.
    pub fn add_equals(&mut self, variable: String, value: PyObject, py: Python<'_>) -> PyResult<()> {
        let sv = SigilValue::from_python(value.bind(py))?;
        self.constraints
            .entry(variable)
            .or_default()
            .push(Constraint::Equals(sv));
        Ok(())
    }

    /// Add a not-equals constraint: variable != value.
    pub fn add_not_equals(&mut self, variable: String, value: PyObject, py: Python<'_>) -> PyResult<()> {
        let sv = SigilValue::from_python(value.bind(py))?;
        self.constraints
            .entry(variable)
            .or_default()
            .push(Constraint::NotEquals(sv));
        Ok(())
    }

    /// Add a greater-than constraint: variable > threshold.
    pub fn add_greater_than(&mut self, variable: String, threshold: f64) {
        self.constraints
            .entry(variable)
            .or_default()
            .push(Constraint::GreaterThan(threshold));
    }

    /// Add a less-than constraint: variable < threshold.
    pub fn add_less_than(&mut self, variable: String, threshold: f64) {
        self.constraints
            .entry(variable)
            .or_default()
            .push(Constraint::LessThan(threshold));
    }

    /// Add a between constraint: low <= variable <= high.
    pub fn add_between(&mut self, variable: String, low: f64, high: f64) {
        self.constraints
            .entry(variable)
            .or_default()
            .push(Constraint::Between(low, high));
    }

    /// Add a one-of constraint: variable in {values}.
    pub fn add_one_of(&mut self, variable: String, values: Vec<PyObject>, py: Python<'_>) -> PyResult<()> {
        let sigil_values: Vec<SigilValue> = values
            .into_iter()
            .map(|v| SigilValue::from_python(v.bind(py)))
            .collect::<PyResult<Vec<_>>>()?;
        self.constraints
            .entry(variable)
            .or_default()
            .push(Constraint::OneOf(sigil_values));
        Ok(())
    }

    /// Check if the given bindings satisfy all constraints.
    /// Returns a list of (variable, constraint_description) for unsatisfied constraints.
    pub fn check(&self, bindings: HashMap<String, PyObject>, py: Python<'_>) -> PyResult<Vec<(String, String)>> {
        let sigil_bindings: HashMap<String, SigilValue> = bindings
            .into_iter()
            .map(|(k, v)| {
                let sv = SigilValue::from_python(v.bind(py))?;
                Ok((k, sv))
            })
            .collect::<PyResult<HashMap<_, _>>>()?;

        let mut violations: Vec<(String, String)> = Vec::new();

        for (var, constraints) in &self.constraints {
            let value = match sigil_bindings.get(var) {
                Some(v) => v,
                None => {
                    violations.push((var.clone(), "variable not bound".to_string()));
                    continue;
                }
            };

            for constraint in constraints {
                if !self.check_constraint(value, constraint) {
                    violations.push((var.clone(), format_constraint(constraint)));
                }
            }
        }

        Ok(violations)
    }

    /// Check if all constraints are satisfied (convenience method).
    pub fn is_satisfied(&self, bindings: HashMap<String, PyObject>, py: Python<'_>) -> PyResult<bool> {
        Ok(self.check(bindings, py)?.is_empty())
    }

    /// Return the number of constraints.
    pub fn constraint_count(&self) -> usize {
        self.constraints.values().map(|v| v.len()).sum()
    }
}

impl ConstraintSolver {
    fn check_constraint(&self, value: &SigilValue, constraint: &Constraint) -> bool {
        match constraint {
            Constraint::Equals(expected) => value == expected,
            Constraint::NotEquals(expected) => value != expected,
            Constraint::GreaterThan(threshold) => as_f64(value)
                .is_some_and(|v| v > *threshold),
            Constraint::LessThan(threshold) => as_f64(value)
                .is_some_and(|v| v < *threshold),
            Constraint::Between(low, high) => as_f64(value)
                .is_some_and(|v| v >= *low && v <= *high),
            Constraint::OneOf(options) => options.contains(value),
        }
    }
}

fn as_f64(value: &SigilValue) -> Option<f64> {
    match value {
        SigilValue::Int(i) => Some(*i as f64),
        SigilValue::Float(f) => Some(*f),
        _ => None,
    }
}

fn format_constraint(constraint: &Constraint) -> String {
    match constraint {
        Constraint::Equals(v) => format!("expected == {:?}", v),
        Constraint::NotEquals(v) => format!("expected != {:?}", v),
        Constraint::GreaterThan(t) => format!("expected > {}", t),
        Constraint::LessThan(t) => format!("expected < {}", t),
        Constraint::Between(lo, hi) => format!("expected between {} and {}", lo, hi),
        Constraint::OneOf(vals) => format!("expected one of {:?}", vals),
    }
}
