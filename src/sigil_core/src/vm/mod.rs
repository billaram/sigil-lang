//! Sigil Bytecode VM — executes compiled bytecode from the Python compiler.

mod builtins;
mod chunk;
mod engine;
mod frames;
pub mod opcodes;
mod rules;
pub mod stack;

#[cfg(feature = "pyo3-ext")]
use pyo3::prelude::*;
#[cfg(feature = "pyo3-ext")]
use pyo3::types::{PyDict, PyList, PyString};
#[cfg(feature = "pyo3-ext")]
use std::collections::HashMap;

pub use chunk::{Chunk, FuncInfo, RuleInfo};
pub use engine::Engine;
pub use opcodes::Opcode;
pub use stack::VMValue;

/// The SigilVM PyO3 class — receives compiled bytecode and executes it.
#[cfg(feature = "pyo3-ext")]
#[cfg_attr(feature = "pyo3-ext", pyclass)]
pub struct SigilVM {
    engine: Option<Engine>,
}

#[cfg(feature = "pyo3-ext")]
#[cfg_attr(feature = "pyo3-ext", pymethods)]
impl SigilVM {
    #[new]
    pub fn new() -> Self {
        SigilVM { engine: None }
    }

    /// Load a compiled chunk (from Python compiler) and execute it.
    pub fn execute(
        &mut self,
        chunk_dict: &Bound<'_, PyDict>,
        input_data: &Bound<'_, PyDict>,
        py: Python<'_>,
    ) -> PyResult<PyObject> {
        let chunk = deserialize_chunk(chunk_dict, py)?;
        let mut engine = Engine::new(chunk);

        // Load input data
        let mut inputs = HashMap::new();
        for (k, v) in input_data.iter() {
            let key: String = k.extract()?;
            let val = VMValue::from_python(&v)?;
            inputs.insert(key, val);
        }
        engine.load_inputs(inputs);

        // Execute
        let result = engine
            .run()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))?;

        // Build result dict
        let result_dict = PyDict::new(py);
        result_dict.set_item("result", result.to_python(py)?)?;

        let output_list = PyList::empty(py);
        for line in &engine.output_lines {
            output_list.append(line)?;
        }
        result_dict.set_item("output_lines", output_list)?;

        // Return all bindings for trace/inspection
        let bindings_dict = PyDict::new(py);
        for (k, v) in engine.call_stack.all_bindings() {
            bindings_dict.set_item(&k, v.to_python(py)?)?;
        }
        result_dict.set_item("bindings", bindings_dict)?;

        self.engine = Some(engine);

        Ok(result_dict.into_any().unbind())
    }
}

#[cfg(feature = "pyo3-ext")]
/// Deserialize a Python dict into a Chunk.
fn deserialize_chunk(dict: &Bound<'_, PyDict>, py: Python<'_>) -> PyResult<Chunk> {
    let mut chunk = Chunk::new();

    // Strings pool
    if let Some(strings_obj) = dict.get_item("strings")? {
        let strings_list = strings_obj.downcast::<PyList>()?;
        for s in strings_list.iter() {
            chunk.strings.push(s.extract::<String>()?);
        }
    }

    // Opcodes
    if let Some(code_obj) = dict.get_item("code")? {
        let code_list = code_obj.downcast::<PyList>()?;
        for op_obj in code_list.iter() {
            let opcode = deserialize_opcode(&op_obj, py)?;
            chunk.code.push(opcode);
        }
    }

    // Functions
    if let Some(funcs_obj) = dict.get_item("functions")? {
        let funcs_dict = funcs_obj.downcast::<PyDict>()?;
        for (name_obj, info_obj) in funcs_dict.iter() {
            let name: String = name_obj.extract()?;
            let info_dict = info_obj.downcast::<PyDict>()?;
            let offset: u32 = info_dict
                .get_item("offset")?
                .map(|v| v.extract())
                .transpose()?
                .unwrap_or(0);
            let param_count: u8 = info_dict
                .get_item("param_count")?
                .map(|v| v.extract())
                .transpose()?
                .unwrap_or(0);
            let param_names: Vec<String> = info_dict
                .get_item("param_names")?
                .map(|v| v.extract())
                .transpose()?
                .unwrap_or_default();
            chunk.functions.insert(
                name,
                FuncInfo {
                    offset,
                    param_count,
                    param_names,
                },
            );
        }
    }

    // Rules
    if let Some(rules_obj) = dict.get_item("rules")? {
        let rules_list = rules_obj.downcast::<PyList>()?;
        for rule_obj in rules_list.iter() {
            let rule_dict = rule_obj.downcast::<PyDict>()?;
            let name: String = rule_dict
                .get_item("name")?
                .map(|v| v.extract())
                .transpose()?
                .unwrap_or_default();
            let priority: i64 = rule_dict
                .get_item("priority")?
                .map(|v| v.extract())
                .transpose()?
                .unwrap_or(0);
            let cond_offset: u32 = rule_dict
                .get_item("cond_offset")?
                .map(|v| v.extract())
                .transpose()?
                .unwrap_or(0);
            let action_offset: u32 = rule_dict
                .get_item("action_offset")?
                .map(|v| v.extract())
                .transpose()?
                .unwrap_or(0);
            let explain_idx: Option<u32> = rule_dict
                .get_item("explain_idx")?
                .and_then(|v| v.extract().ok());
            chunk.rules.push(RuleInfo {
                name,
                priority,
                cond_offset,
                action_offset,
                explain_idx,
            });
        }
    }

    // Main offset
    if let Some(main_obj) = dict.get_item("main_offset")? {
        if !main_obj.is_none() {
            chunk.main_offset = Some(main_obj.extract::<u32>()?);
        }
    }

    // Init offset (constants)
    if let Some(init_obj) = dict.get_item("init_offset")? {
        if !init_obj.is_none() {
            chunk.init_offset = Some(init_obj.extract::<u32>()?);
        }
    }

    Ok(chunk)
}

#[cfg(feature = "pyo3-ext")]
/// Deserialize a single opcode from a Python list [opname, ...args].
fn deserialize_opcode(obj: &Bound<'_, PyAny>, _py: Python<'_>) -> PyResult<Opcode> {
    let list = obj.downcast::<PyList>()?;
    let op_name: String = list.get_item(0)?.extract()?;

    let op = match op_name.as_str() {
        "PushInt" => Opcode::PushInt(list.get_item(1)?.extract()?),
        "PushFloat" => Opcode::PushFloat(list.get_item(1)?.extract()?),
        "PushBool" => Opcode::PushBool(list.get_item(1)?.extract()?),
        "PushNone" => Opcode::PushNone,
        "PushUnbound" => Opcode::PushUnbound,
        "PushString" => Opcode::PushString(list.get_item(1)?.extract()?),
        "PushSymbol" => Opcode::PushSymbol(list.get_item(1)?.extract()?),
        "PushList" => Opcode::PushList(list.get_item(1)?.extract()?),
        "PushRecord" => Opcode::PushRecord(list.get_item(1)?.extract()?),
        "PushVariant" => Opcode::PushVariant(
            list.get_item(1)?.extract()?,
            list.get_item(2)?.extract()?,
        ),
        "Pop" => Opcode::Pop,
        "Dup" => Opcode::Dup,
        "Add" => Opcode::Add,
        "Sub" => Opcode::Sub,
        "Mul" => Opcode::Mul,
        "Div" => Opcode::Div,
        "Neg" => Opcode::Neg,
        "Mod" => Opcode::Mod,
        "Eq" => Opcode::Eq,
        "Neq" => Opcode::Neq,
        "Gt" => Opcode::Gt,
        "Lt" => Opcode::Lt,
        "Gte" => Opcode::Gte,
        "Lte" => Opcode::Lte,
        "Not" => Opcode::Not,
        "And" => Opcode::And,
        "Or" => Opcode::Or,
        "Load" => Opcode::Load(list.get_item(1)?.extract()?),
        "Store" => Opcode::Store(list.get_item(1)?.extract()?),
        "LoadField" => Opcode::LoadField(list.get_item(1)?.extract()?),
        "StoreField" => Opcode::StoreField(list.get_item(1)?.extract()?),
        "Mutate" => Opcode::Mutate(list.get_item(1)?.extract()?),
        "Jump" => Opcode::Jump(list.get_item(1)?.extract()?),
        "JumpIfFalse" => Opcode::JumpIfFalse(list.get_item(1)?.extract()?),
        "JumpIfTrue" => Opcode::JumpIfTrue(list.get_item(1)?.extract()?),
        "JumpIfUnbound" => Opcode::JumpIfUnbound(list.get_item(1)?.extract()?),
        "Call" => Opcode::Call(
            list.get_item(1)?.extract()?,
            list.get_item(2)?.extract()?,
        ),
        "Return" => Opcode::Return,
        "CallBuiltin" => Opcode::CallBuiltin(
            list.get_item(1)?.extract()?,
            list.get_item(2)?.extract()?,
        ),
        "MakeClosure" => Opcode::MakeClosure(
            list.get_item(1)?.extract()?,
            list.get_item(2)?.extract()?,
        ),
        "CmpExceeds" => Opcode::CmpExceeds,
        "CmpBelow" => Opcode::CmpBelow,
        "CmpAtLeast" => Opcode::CmpAtLeast,
        "CmpAtMost" => Opcode::CmpAtMost,
        "CmpBetween" => Opcode::CmpBetween,
        "CmpIs" => Opcode::CmpIs,
        "CmpIsNot" => Opcode::CmpIsNot,
        "IsAssigned" => Opcode::IsAssigned,
        "IsEmpty" => Opcode::IsEmpty,
        "Contains" => Opcode::Contains,
        "InList" => Opcode::InList,
        "HasCount" => Opcode::HasCount,
        "StringOp" => Opcode::StringOp(list.get_item(1)?.extract()?),
        "BeginRule" => Opcode::BeginRule(list.get_item(1)?.extract()?),
        "EndRule" => Opcode::EndRule,
        "FireRule" => Opcode::FireRule(list.get_item(1)?.extract()?),
        "CheckFired" => Opcode::CheckFired(list.get_item(1)?.extract()?),
        "SetExplain" => Opcode::SetExplain(list.get_item(1)?.extract()?),
        "Print" => Opcode::Print,
        "Halt" => Opcode::Halt,
        "IndexAccess" => Opcode::IndexAccess,
        _ => {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "Unknown opcode: {}",
                op_name
            )));
        }
    };
    Ok(op)
}
