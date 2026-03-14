//! VM value stack and VMValue type.

use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict, PyFloat, PyInt, PyList, PyString};
use std::collections::HashMap;
use std::fmt;

/// Runtime value in the VM — optimized for stack operations.
#[derive(Debug, Clone)]
pub enum VMValue {
    None,
    Unbound,
    Bool(bool),
    Int(i64),
    Float(f64),
    Text(String),
    Symbol(String),
    Record {
        type_name: Option<String>,
        fields: HashMap<String, VMValue>,
    },
    Variant {
        type_name: String,
        variant_name: String,
        fields: HashMap<String, VMValue>,
    },
    List(Vec<VMValue>),
    Closure {
        func_name: String,
        param_count: u8,
        captures: Vec<(String, VMValue)>,
    },
}

impl VMValue {
    pub fn is_truthy(&self) -> bool {
        match self {
            VMValue::None | VMValue::Unbound => false,
            VMValue::Bool(b) => *b,
            VMValue::Int(i) => *i != 0,
            VMValue::Float(f) => *f != 0.0,
            VMValue::Text(s) => !s.is_empty(),
            VMValue::List(items) => !items.is_empty(),
            _ => true,
        }
    }

    pub fn is_unbound(&self) -> bool {
        matches!(self, VMValue::Unbound)
    }

    pub fn is_empty(&self) -> bool {
        match self {
            VMValue::None | VMValue::Unbound => true,
            VMValue::List(items) => items.is_empty(),
            VMValue::Text(s) => s.is_empty(),
            _ => false,
        }
    }

    pub fn as_float(&self) -> Option<f64> {
        match self {
            VMValue::Int(i) => Some(*i as f64),
            VMValue::Float(f) => Some(*f),
            _ => Option::None,
        }
    }

    pub fn as_int(&self) -> Option<i64> {
        match self {
            VMValue::Int(i) => Some(*i),
            _ => Option::None,
        }
    }

    pub fn as_text(&self) -> Option<&str> {
        match self {
            VMValue::Text(s) => Some(s),
            _ => Option::None,
        }
    }

    pub fn list_len(&self) -> Option<usize> {
        match self {
            VMValue::List(items) => Some(items.len()),
            VMValue::Text(s) => Some(s.len()),
            _ => Option::None,
        }
    }

    pub fn list_contains(&self, element: &VMValue) -> bool {
        match self {
            VMValue::List(items) => items.iter().any(|item| values_equal(item, element)),
            _ => false,
        }
    }

    /// Convert from Python object.
    pub fn from_python(obj: &Bound<'_, PyAny>) -> PyResult<Self> {
        if obj.is_none() {
            return Ok(VMValue::None);
        }
        if let Ok(b) = obj.downcast::<PyBool>() {
            return Ok(VMValue::Bool(b.is_true()));
        }
        if let Ok(i) = obj.downcast::<PyInt>() {
            return Ok(VMValue::Int(i.extract::<i64>()?));
        }
        if let Ok(f) = obj.downcast::<PyFloat>() {
            return Ok(VMValue::Float(f.extract::<f64>()?));
        }
        if let Ok(s) = obj.downcast::<PyString>() {
            return Ok(VMValue::Text(s.to_string()));
        }
        if let Ok(list) = obj.downcast::<PyList>() {
            let items: PyResult<Vec<VMValue>> = list
                .iter()
                .map(|item| VMValue::from_python(&item))
                .collect();
            return Ok(VMValue::List(items?));
        }
        if let Ok(dict) = obj.downcast::<PyDict>() {
            // Check for Symbol dict: {"name": "..."}
            if dict.len() == 1 {
                if let Some(name_val) = dict.get_item("name")? {
                    if let Ok(name) = name_val.extract::<String>() {
                        return Ok(VMValue::Symbol(name));
                    }
                }
            }
            let mut fields = HashMap::new();
            for (k, v) in dict.iter() {
                let key: String = k.extract()?;
                fields.insert(key, VMValue::from_python(&v)?);
            }
            return Ok(VMValue::Record {
                type_name: None,
                fields,
            });
        }
        // Check for Symbol (has .name attribute and type is Symbol)
        if let Ok(name) = obj.getattr("name") {
            if let Ok(name_str) = name.extract::<String>() {
                if obj.get_type().name()? == "Symbol" {
                    return Ok(VMValue::Symbol(name_str));
                }
            }
        }
        Ok(VMValue::Text(obj.str()?.to_string()))
    }

    /// Convert to Python object.
    pub fn to_python(&self, py: Python<'_>) -> PyResult<PyObject> {
        match self {
            VMValue::None | VMValue::Unbound => Ok(py.None()),
            VMValue::Bool(b) => Ok((*b).into_pyobject(py)?.to_owned().into_any().unbind()),
            VMValue::Int(i) => Ok(i.into_pyobject(py)?.into_any().unbind()),
            VMValue::Float(f) => Ok(f.into_pyobject(py)?.into_any().unbind()),
            VMValue::Text(s) => Ok(s.into_pyobject(py)?.into_any().unbind()),
            VMValue::Symbol(name) => {
                let dict = PyDict::new(py);
                dict.set_item("_type", "symbol")?;
                dict.set_item("name", name)?;
                Ok(dict.into_any().unbind())
            }
            VMValue::Record { type_name, fields } => {
                let dict = PyDict::new(py);
                if let Some(tn) = type_name {
                    dict.set_item("_type", tn)?;
                }
                for (k, v) in fields {
                    dict.set_item(k, v.to_python(py)?)?;
                }
                Ok(dict.into_any().unbind())
            }
            VMValue::Variant {
                type_name,
                variant_name,
                fields,
            } => {
                let dict = PyDict::new(py);
                dict.set_item("_type", "variant")?;
                dict.set_item("type_name", type_name)?;
                dict.set_item("variant_name", variant_name)?;
                let fields_dict = PyDict::new(py);
                for (k, v) in fields {
                    fields_dict.set_item(k, v.to_python(py)?)?;
                }
                dict.set_item("fields", fields_dict)?;
                Ok(dict.into_any().unbind())
            }
            VMValue::List(items) => {
                let list = PyList::empty(py);
                for item in items {
                    list.append(item.to_python(py)?)?;
                }
                Ok(list.into_any().unbind())
            }
            VMValue::Closure { func_name, .. } => {
                Ok(format!("<closure {}>", func_name)
                    .into_pyobject(py)?
                    .into_any()
                    .unbind())
            }
        }
    }
}

impl fmt::Display for VMValue {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            VMValue::None | VMValue::Unbound => write!(f, "none"),
            VMValue::Bool(b) => write!(f, "{}", if *b { "true" } else { "false" }),
            VMValue::Int(i) => write!(f, "{}", i),
            VMValue::Float(v) => {
                if v.fract() == 0.0 {
                    write!(f, "{:.1}", v)
                } else {
                    write!(f, "{}", v)
                }
            }
            VMValue::Text(s) => write!(f, "{}", s),
            VMValue::Symbol(name) => write!(f, ":{}", name),
            VMValue::Record { type_name, fields } => {
                let tn = type_name.as_deref().unwrap_or("record");
                let inner: Vec<String> = fields
                    .iter()
                    .map(|(k, v)| format!("{}: {}", k, v))
                    .collect();
                write!(f, "{}({})", tn, inner.join(", "))
            }
            VMValue::Variant {
                type_name,
                variant_name,
                fields,
            } => {
                if fields.is_empty() {
                    write!(f, "{}.{}", type_name, variant_name)
                } else {
                    let inner: Vec<String> = fields
                        .iter()
                        .map(|(k, v)| format!("{}: {}", k, v))
                        .collect();
                    write!(f, "{}.{}({})", type_name, variant_name, inner.join(", "))
                }
            }
            VMValue::List(items) => {
                let inner: Vec<String> = items.iter().map(|v| format!("{}", v)).collect();
                write!(f, "[{}]", inner.join(", "))
            }
            VMValue::Closure { func_name, .. } => write!(f, "<closure {}>", func_name),
        }
    }
}

/// Structural equality for VMValues.
pub fn values_equal(a: &VMValue, b: &VMValue) -> bool {
    match (a, b) {
        (VMValue::None, VMValue::None) => true,
        (VMValue::Unbound, VMValue::Unbound) => true,
        (VMValue::Bool(a), VMValue::Bool(b)) => a == b,
        (VMValue::Int(a), VMValue::Int(b)) => a == b,
        (VMValue::Float(a), VMValue::Float(b)) => a == b,
        (VMValue::Int(a), VMValue::Float(b)) => (*a as f64) == *b,
        (VMValue::Float(a), VMValue::Int(b)) => *a == (*b as f64),
        (VMValue::Text(a), VMValue::Text(b)) => a == b,
        (VMValue::Symbol(a), VMValue::Symbol(b)) => a == b,
        (VMValue::List(a), VMValue::List(b)) => {
            a.len() == b.len() && a.iter().zip(b.iter()).all(|(x, y)| values_equal(x, y))
        }
        (
            VMValue::Record {
                type_name: tn_a,
                fields: fa,
            },
            VMValue::Record {
                type_name: tn_b,
                fields: fb,
            },
        ) => tn_a == tn_b && fa.len() == fb.len() && fa.iter().all(|(k, v)| fb.get(k).map_or(false, |v2| values_equal(v, v2))),
        _ => false,
    }
}

/// Value stack with fixed capacity.
pub struct ValueStack {
    data: Vec<VMValue>,
}

impl ValueStack {
    pub fn new() -> Self {
        ValueStack {
            data: Vec::with_capacity(1024),
        }
    }

    pub fn push(&mut self, value: VMValue) {
        self.data.push(value);
    }

    pub fn pop(&mut self) -> VMValue {
        self.data.pop().unwrap_or(VMValue::None)
    }

    pub fn peek(&self) -> &VMValue {
        self.data.last().unwrap_or(&VMValue::None)
    }

    pub fn len(&self) -> usize {
        self.data.len()
    }

    #[allow(dead_code)]
    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }
}
