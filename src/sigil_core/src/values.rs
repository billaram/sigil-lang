//! Sigil value representation in Rust.
//!
//! Mirrors the Python `Value` union type for cross-boundary marshaling.

use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict, PyFloat, PyInt, PyList, PyNone, PyString};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Rust representation of a Sigil runtime value.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum SigilValue {
    None,
    Bool(bool),
    Int(i64),
    Float(f64),
    Text(String),
    Symbol(String),
    Record {
        type_name: Option<String>,
        fields: HashMap<String, SigilValue>,
    },
    List(Vec<SigilValue>),
}

impl SigilValue {
    /// Convert a Python object to a SigilValue.
    pub fn from_python(obj: &Bound<'_, PyAny>) -> PyResult<Self> {
        if obj.is_none() {
            return Ok(SigilValue::None);
        }
        if let Ok(b) = obj.downcast::<PyBool>() {
            return Ok(SigilValue::Bool(b.is_true()));
        }
        if let Ok(i) = obj.downcast::<PyInt>() {
            return Ok(SigilValue::Int(i.extract::<i64>()?));
        }
        if let Ok(f) = obj.downcast::<PyFloat>() {
            return Ok(SigilValue::Float(f.extract::<f64>()?));
        }
        if let Ok(s) = obj.downcast::<PyString>() {
            return Ok(SigilValue::Text(s.to_string()));
        }
        if let Ok(list) = obj.downcast::<PyList>() {
            let items: PyResult<Vec<SigilValue>> = list
                .iter()
                .map(|item| SigilValue::from_python(&item))
                .collect();
            return Ok(SigilValue::List(items?));
        }
        if let Ok(dict) = obj.downcast::<PyDict>() {
            let mut fields = HashMap::new();
            for (k, v) in dict.iter() {
                let key: String = k.extract()?;
                fields.insert(key, SigilValue::from_python(&v)?);
            }
            return Ok(SigilValue::Record {
                type_name: None,
                fields,
            });
        }
        // Check for Symbol (has .name attribute)
        if let Ok(name) = obj.getattr("name") {
            if let Ok(name_str) = name.extract::<String>() {
                if obj.get_type().name()? == "Symbol" {
                    return Ok(SigilValue::Symbol(name_str));
                }
            }
        }
        // Fallback: convert to string
        Ok(SigilValue::Text(obj.str()?.to_string()))
    }

    /// Convert a SigilValue back to a Python object.
    pub fn to_python(&self, py: Python<'_>) -> PyResult<PyObject> {
        match self {
            SigilValue::None => Ok(PyNone::get(py).into_pyobject(py)?.into_any().unbind()),
            SigilValue::Bool(b) => Ok(b.into_pyobject(py)?.into_any().unbind()),
            SigilValue::Int(i) => Ok(i.into_pyobject(py)?.into_any().unbind()),
            SigilValue::Float(f) => Ok(f.into_pyobject(py)?.into_any().unbind()),
            SigilValue::Text(s) => Ok(s.into_pyobject(py)?.into_any().unbind()),
            SigilValue::Symbol(name) => {
                let dict = PyDict::new(py);
                dict.set_item("name", name)?;
                Ok(dict.into_pyobject(py)?.into_any().unbind())
            }
            SigilValue::Record { fields, .. } => {
                let dict = PyDict::new(py);
                for (k, v) in fields {
                    dict.set_item(k, v.to_python(py)?)?;
                }
                Ok(dict.into_pyobject(py)?.into_any().unbind())
            }
            SigilValue::List(items) => {
                let list = PyList::empty(py);
                for item in items {
                    list.append(item.to_python(py)?)?;
                }
                Ok(list.into_pyobject(py)?.into_any().unbind())
            }
        }
    }
}
