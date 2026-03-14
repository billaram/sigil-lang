//! Main VM dispatch loop.

use std::collections::HashMap;

use super::builtins;
use super::chunk::Chunk;
use super::frames::{CallFrame, CallStack};
use super::opcodes::Opcode;
use super::rules;
use super::stack::{values_equal, VMValue, ValueStack};

/// The VM engine — executes bytecode.
pub struct Engine {
    pub chunk: Chunk,
    pub stack: ValueStack,
    pub call_stack: CallStack,
    pub output_lines: Vec<String>,
    pub ip: usize, // instruction pointer
    pub halted: bool,
}

impl Engine {
    pub fn new(chunk: Chunk) -> Self {
        Engine {
            chunk,
            stack: ValueStack::new(),
            call_stack: CallStack::new(),
            output_lines: Vec::new(),
            ip: 0,
            halted: false,
        }
    }

    /// Load input data into global scope.
    pub fn load_inputs(&mut self, inputs: HashMap<String, VMValue>) {
        for (name, value) in inputs {
            self.call_stack.set_var(&name, value);
        }
    }

    /// Execute bytecode from the beginning.
    pub fn run(&mut self) -> Result<VMValue, String> {
        self.ip = 0;
        self.halted = false;

        // Run init block (constants) if present
        if let Some(init_offset) = self.chunk.init_offset {
            self.ip = init_offset as usize;
            self.halted = false;
            self.dispatch_loop()?;
        }

        // If there are rules, run forward chaining
        if !self.chunk.rules.is_empty() {
            self.halted = false;
            rules::run_forward_chaining(self)?;
        }

        // Then execute main block if present
        if let Some(main_offset) = self.chunk.main_offset {
            self.ip = main_offset as usize;
            self.halted = false;
            self.dispatch_loop()?;
        }

        // Return top of stack or None
        if self.stack.len() > 0 {
            Ok(self.stack.pop())
        } else {
            Ok(VMValue::None)
        }
    }

    /// Execute bytecode from a given offset, return whether top of stack is truthy.
    pub fn execute_from(&mut self, offset: u32) -> Result<bool, String> {
        let saved_ip = self.ip;
        let saved_halted = self.halted;
        self.ip = offset as usize;
        self.halted = false;
        self.dispatch_loop()?;
        self.ip = saved_ip;
        self.halted = saved_halted;
        let result = self.stack.pop();
        Ok(result.is_truthy())
    }

    /// Execute bytecode from a given offset, discard result.
    pub fn execute_from_void(&mut self, offset: u32) -> Result<(), String> {
        let saved_ip = self.ip;
        let saved_halted = self.halted;
        self.ip = offset as usize;
        self.halted = false;
        self.dispatch_loop()?;
        self.ip = saved_ip;
        self.halted = saved_halted;
        Ok(())
    }

    /// Main dispatch loop.
    pub fn dispatch_loop(&mut self) -> Result<(), String> {
        while self.ip < self.chunk.code.len() && !self.halted {
            let op = self.chunk.code[self.ip].clone();
            self.ip += 1;

            match op {
                // --- Stack ---
                Opcode::PushInt(v) => self.stack.push(VMValue::Int(v)),
                Opcode::PushFloat(v) => self.stack.push(VMValue::Float(v)),
                Opcode::PushBool(v) => self.stack.push(VMValue::Bool(v)),
                Opcode::PushNone => self.stack.push(VMValue::None),
                Opcode::PushUnbound => self.stack.push(VMValue::Unbound),
                Opcode::PushString(idx) => {
                    let s = self.get_string(idx);
                    self.stack.push(VMValue::Text(s));
                }
                Opcode::PushSymbol(idx) => {
                    let s = self.get_string(idx);
                    self.stack.push(VMValue::Symbol(s));
                }
                Opcode::PushList(count) => {
                    let mut items = Vec::with_capacity(count as usize);
                    for _ in 0..count {
                        items.push(self.stack.pop());
                    }
                    items.reverse();
                    self.stack.push(VMValue::List(items));
                }
                Opcode::PushRecord(count) => {
                    let mut fields = HashMap::new();
                    for _ in 0..count {
                        let value = self.stack.pop();
                        let key = self.stack.pop();
                        if let VMValue::Text(k) = key {
                            fields.insert(k, value);
                        }
                    }
                    self.stack.push(VMValue::Record {
                        type_name: None,
                        fields,
                    });
                }
                Opcode::PushVariant(type_idx, count) => {
                    let type_name = self.get_string(type_idx);
                    let variant_name = match self.stack.pop() {
                        VMValue::Text(s) => s,
                        _ => String::new(),
                    };
                    let mut fields = HashMap::new();
                    for _ in 0..count {
                        let value = self.stack.pop();
                        let key = self.stack.pop();
                        if let VMValue::Text(k) = key {
                            fields.insert(k, value);
                        }
                    }
                    self.stack.push(VMValue::Variant {
                        type_name,
                        variant_name,
                        fields,
                    });
                }
                Opcode::Pop => {
                    self.stack.pop();
                }
                Opcode::Dup => {
                    let v = self.stack.peek().clone();
                    self.stack.push(v);
                }

                // --- Arithmetic ---
                Opcode::Add => self.op_add()?,
                Opcode::Sub => self.op_sub()?,
                Opcode::Mul => self.op_mul()?,
                Opcode::Div => self.op_div()?,
                Opcode::Neg => self.op_neg()?,
                Opcode::Mod => self.op_mod()?,

                // --- Comparison ---
                Opcode::Eq => self.op_eq(),
                Opcode::Neq => self.op_neq(),
                Opcode::Gt => self.op_cmp(|a, b| a > b),
                Opcode::Lt => self.op_cmp(|a, b| a < b),
                Opcode::Gte => self.op_cmp(|a, b| a >= b),
                Opcode::Lte => self.op_cmp(|a, b| a <= b),

                // --- Logic ---
                Opcode::Not => {
                    let v = self.stack.pop();
                    self.stack.push(VMValue::Bool(!v.is_truthy()));
                }
                Opcode::And => {
                    let b = self.stack.pop();
                    let a = self.stack.pop();
                    self.stack
                        .push(VMValue::Bool(a.is_truthy() && b.is_truthy()));
                }
                Opcode::Or => {
                    let b = self.stack.pop();
                    let a = self.stack.pop();
                    self.stack
                        .push(VMValue::Bool(a.is_truthy() || b.is_truthy()));
                }

                // --- Variables ---
                Opcode::Load(idx) => {
                    let name = self.get_string(idx);
                    let val = self.call_stack.get_var(&name);
                    self.stack.push(val);
                }
                Opcode::Store(idx) => {
                    let name = self.get_string(idx);
                    let val = self.stack.pop();
                    self.call_stack.set_var_scoped(&name, val);
                }
                Opcode::LoadField(idx) => {
                    let field_name = self.get_string(idx);
                    let obj = self.stack.pop();
                    match obj {
                        VMValue::Record { fields, .. } => {
                            let val = fields.get(&field_name).cloned().unwrap_or(VMValue::Unbound);
                            self.stack.push(val);
                        }
                        VMValue::Variant { fields, .. } => {
                            let val = fields.get(&field_name).cloned().unwrap_or(VMValue::Unbound);
                            self.stack.push(val);
                        }
                        _ => self.stack.push(VMValue::Unbound),
                    }
                }
                Opcode::StoreField(idx) => {
                    let field_name = self.get_string(idx);
                    let value = self.stack.pop();
                    let obj = self.stack.pop();
                    match obj {
                        VMValue::Record {
                            type_name,
                            mut fields,
                        } => {
                            fields.insert(field_name, value);
                            self.stack.push(VMValue::Record { type_name, fields });
                        }
                        _ => self.stack.push(VMValue::Unbound),
                    }
                }
                Opcode::Mutate(idx) => {
                    let name = self.get_string(idx);
                    let val = self.stack.pop();
                    self.call_stack.set_var_scoped(&name, val);
                }

                // --- Control Flow ---
                Opcode::Jump(target) => {
                    self.ip = target as usize;
                }
                Opcode::JumpIfFalse(target) => {
                    let v = self.stack.pop();
                    if !v.is_truthy() {
                        self.ip = target as usize;
                    }
                }
                Opcode::JumpIfTrue(target) => {
                    let v = self.stack.pop();
                    if v.is_truthy() {
                        self.ip = target as usize;
                    }
                }
                Opcode::JumpIfUnbound(target) => {
                    let v = self.stack.pop();
                    if v.is_unbound() {
                        self.ip = target as usize;
                    }
                }

                // --- Functions ---
                Opcode::Call(name_idx, arg_count) => {
                    let func_name = self.get_string(name_idx);
                    self.call_function(&func_name, arg_count)?;
                }
                Opcode::Return => {
                    if let Some(frame) = self.call_stack.pop() {
                        self.ip = frame.return_addr as usize;
                        // Return value is already on stack
                    } else {
                        self.halted = true;
                    }
                }
                Opcode::CallBuiltin(id, arg_count) => {
                    self.call_builtin(id, arg_count)?;
                }
                Opcode::MakeClosure(name_idx, capture_count) => {
                    let func_name = self.get_string(name_idx);
                    let mut captures = Vec::new();
                    for _ in 0..capture_count {
                        let val = self.stack.pop();
                        let cap_name = match self.stack.pop() {
                            VMValue::Text(s) => s,
                            _ => String::new(),
                        };
                        captures.push((cap_name, val));
                    }
                    captures.reverse();
                    let param_count = self
                        .chunk
                        .functions
                        .get(&func_name)
                        .map(|f| f.param_count)
                        .unwrap_or(0);
                    self.stack.push(VMValue::Closure {
                        func_name,
                        param_count,
                        captures,
                    });
                }

                // --- Sigil Conditions ---
                Opcode::CmpExceeds => {
                    let b = self.stack.pop();
                    let a = self.stack.pop();
                    self.stack.push(self.cmp_numeric(&a, &b, |x, y| x > y));
                }
                Opcode::CmpBelow => {
                    let b = self.stack.pop();
                    let a = self.stack.pop();
                    self.stack.push(self.cmp_numeric(&a, &b, |x, y| x < y));
                }
                Opcode::CmpAtLeast => {
                    let b = self.stack.pop();
                    let a = self.stack.pop();
                    self.stack.push(self.cmp_numeric(&a, &b, |x, y| x >= y));
                }
                Opcode::CmpAtMost => {
                    let b = self.stack.pop();
                    let a = self.stack.pop();
                    self.stack.push(self.cmp_numeric(&a, &b, |x, y| x <= y));
                }
                Opcode::CmpBetween => {
                    let high = self.stack.pop();
                    let low = self.stack.pop();
                    let a = self.stack.pop();
                    self.stack.push(self.cmp_between(&a, &low, &high));
                }
                Opcode::CmpIs => self.op_eq(),
                Opcode::CmpIsNot => self.op_neq(),
                Opcode::IsAssigned => {
                    let v = self.stack.pop();
                    self.stack.push(VMValue::Bool(!v.is_unbound()));
                }
                Opcode::IsEmpty => {
                    let v = self.stack.pop();
                    self.stack.push(VMValue::Bool(v.is_empty()));
                }
                Opcode::Contains => {
                    let element = self.stack.pop();
                    let collection = self.stack.pop();
                    self.stack
                        .push(VMValue::Bool(collection.list_contains(&element)));
                }
                Opcode::InList => {
                    let list = self.stack.pop();
                    let element = self.stack.pop();
                    self.stack.push(VMValue::Bool(list.list_contains(&element)));
                }
                Opcode::HasCount => {
                    let count = self.stack.pop();
                    let collection = self.stack.pop();
                    let expected = count.as_int().unwrap_or(0) as usize;
                    let actual = collection.list_len().unwrap_or(0);
                    self.stack.push(VMValue::Bool(actual == expected));
                }
                Opcode::StringOp(op_type) => {
                    let pattern = self.stack.pop();
                    let string = self.stack.pop();
                    self.stack.push(self.string_op(op_type, &string, &pattern));
                }

                // --- Rule Engine ---
                Opcode::BeginRule(_) | Opcode::EndRule => {
                    // Trace bookkeeping — handled in forward chaining loop
                }
                Opcode::FireRule(_) | Opcode::CheckFired(_) => {
                    // Handled in forward chaining loop
                }
                Opcode::SetExplain(_) => {
                    // Handled in forward chaining loop
                }

                // --- Output ---
                Opcode::Print => {
                    let v = self.stack.pop();
                    self.output_lines.push(format!("{}", v));
                }

                // --- Index Access ---
                Opcode::IndexAccess => {
                    let index = self.stack.pop();
                    let obj = self.stack.pop();
                    self.stack.push(self.index_access(&obj, &index));
                }

                // --- Special ---
                Opcode::Halt => {
                    self.halted = true;
                }
            }
        }

        Ok(())
    }

    // --- Helper methods ---

    fn get_string(&self, idx: u32) -> String {
        self.chunk
            .strings
            .get(idx as usize)
            .cloned()
            .unwrap_or_default()
    }

    fn op_add(&mut self) -> Result<(), String> {
        let b = self.stack.pop();
        let a = self.stack.pop();
        let result = match (&a, &b) {
            (VMValue::Int(x), VMValue::Int(y)) => VMValue::Int(x + y),
            (VMValue::Float(x), VMValue::Float(y)) => VMValue::Float(x + y),
            (VMValue::Int(x), VMValue::Float(y)) => VMValue::Float(*x as f64 + y),
            (VMValue::Float(x), VMValue::Int(y)) => VMValue::Float(x + *y as f64),
            (VMValue::Text(x), VMValue::Text(y)) => VMValue::Text(format!("{}{}", x, y)),
            (VMValue::Text(x), _) => VMValue::Text(format!("{}{}", x, b)),
            (_, VMValue::Text(y)) => VMValue::Text(format!("{}{}", a, y)),
            (VMValue::List(x), VMValue::List(y)) => {
                let mut combined = x.clone();
                combined.extend(y.iter().cloned());
                VMValue::List(combined)
            }
            _ => VMValue::None,
        };
        self.stack.push(result);
        Ok(())
    }

    fn op_sub(&mut self) -> Result<(), String> {
        let b = self.stack.pop();
        let a = self.stack.pop();
        let result = match (&a, &b) {
            (VMValue::Int(x), VMValue::Int(y)) => VMValue::Int(x - y),
            (VMValue::Float(x), VMValue::Float(y)) => VMValue::Float(x - y),
            (VMValue::Int(x), VMValue::Float(y)) => VMValue::Float(*x as f64 - y),
            (VMValue::Float(x), VMValue::Int(y)) => VMValue::Float(x - *y as f64),
            _ => VMValue::None,
        };
        self.stack.push(result);
        Ok(())
    }

    fn op_mul(&mut self) -> Result<(), String> {
        let b = self.stack.pop();
        let a = self.stack.pop();
        let result = match (&a, &b) {
            (VMValue::Int(x), VMValue::Int(y)) => VMValue::Int(x * y),
            (VMValue::Float(x), VMValue::Float(y)) => VMValue::Float(x * y),
            (VMValue::Int(x), VMValue::Float(y)) => VMValue::Float(*x as f64 * y),
            (VMValue::Float(x), VMValue::Int(y)) => VMValue::Float(x * *y as f64),
            _ => VMValue::None,
        };
        self.stack.push(result);
        Ok(())
    }

    fn op_div(&mut self) -> Result<(), String> {
        let b = self.stack.pop();
        let a = self.stack.pop();
        let result = match (&a, &b) {
            (VMValue::Int(x), VMValue::Int(y)) => {
                if *y == 0 {
                    return Err("Division by zero".to_string());
                }
                if x % y == 0 {
                    VMValue::Int(x / y)
                } else {
                    VMValue::Float(*x as f64 / *y as f64)
                }
            }
            (VMValue::Float(x), VMValue::Float(y)) => {
                if *y == 0.0 {
                    return Err("Division by zero".to_string());
                }
                VMValue::Float(x / y)
            }
            (VMValue::Int(x), VMValue::Float(y)) => {
                if *y == 0.0 {
                    return Err("Division by zero".to_string());
                }
                VMValue::Float(*x as f64 / y)
            }
            (VMValue::Float(x), VMValue::Int(y)) => {
                if *y == 0 {
                    return Err("Division by zero".to_string());
                }
                VMValue::Float(x / *y as f64)
            }
            _ => VMValue::None,
        };
        self.stack.push(result);
        Ok(())
    }

    fn op_neg(&mut self) -> Result<(), String> {
        let v = self.stack.pop();
        let result = match v {
            VMValue::Int(i) => VMValue::Int(-i),
            VMValue::Float(f) => VMValue::Float(-f),
            _ => VMValue::None,
        };
        self.stack.push(result);
        Ok(())
    }

    fn op_mod(&mut self) -> Result<(), String> {
        let b = self.stack.pop();
        let a = self.stack.pop();
        let result = match (&a, &b) {
            (VMValue::Int(x), VMValue::Int(y)) => {
                if *y == 0 {
                    return Err("Modulo by zero".to_string());
                }
                VMValue::Int(x % y)
            }
            (VMValue::Float(x), VMValue::Float(y)) => VMValue::Float(x % y),
            (VMValue::Int(x), VMValue::Float(y)) => VMValue::Float(*x as f64 % y),
            (VMValue::Float(x), VMValue::Int(y)) => VMValue::Float(x % *y as f64),
            _ => VMValue::None,
        };
        self.stack.push(result);
        Ok(())
    }

    fn op_eq(&mut self) {
        let b = self.stack.pop();
        let a = self.stack.pop();
        // Unbound comparisons: if either side is unbound, return false
        if a.is_unbound() || b.is_unbound() {
            self.stack.push(VMValue::Bool(false));
            return;
        }
        self.stack.push(VMValue::Bool(values_equal(&a, &b)));
    }

    fn op_neq(&mut self) {
        let b = self.stack.pop();
        let a = self.stack.pop();
        // "is not" with unbound returns true
        if a.is_unbound() || b.is_unbound() {
            self.stack.push(VMValue::Bool(true));
            return;
        }
        self.stack.push(VMValue::Bool(!values_equal(&a, &b)));
    }

    fn op_cmp<F: Fn(f64, f64) -> bool>(&mut self, cmp: F) {
        let b = self.stack.pop();
        let a = self.stack.pop();
        if a.is_unbound() || b.is_unbound() {
            self.stack.push(VMValue::Bool(false));
            return;
        }
        match (a.as_float(), b.as_float()) {
            (Some(fa), Some(fb)) => self.stack.push(VMValue::Bool(cmp(fa, fb))),
            _ => self.stack.push(VMValue::Bool(false)),
        }
    }

    fn cmp_numeric<F: Fn(f64, f64) -> bool>(&self, a: &VMValue, b: &VMValue, cmp: F) -> VMValue {
        if a.is_unbound() || b.is_unbound() {
            return VMValue::Bool(false);
        }
        match (a.as_float(), b.as_float()) {
            (Some(fa), Some(fb)) => VMValue::Bool(cmp(fa, fb)),
            _ => VMValue::Bool(values_equal(a, b)),
        }
    }

    fn cmp_between(&self, a: &VMValue, low: &VMValue, high: &VMValue) -> VMValue {
        if a.is_unbound() || low.is_unbound() || high.is_unbound() {
            return VMValue::Bool(false);
        }
        match (a.as_float(), low.as_float(), high.as_float()) {
            (Some(fa), Some(fl), Some(fh)) => VMValue::Bool(fa >= fl && fa <= fh),
            _ => VMValue::Bool(false),
        }
    }

    fn string_op(&self, op_type: u8, string: &VMValue, pattern: &VMValue) -> VMValue {
        let s = match string {
            VMValue::Text(s) => s.as_str(),
            _ => return VMValue::Bool(false),
        };
        let p = match pattern {
            VMValue::Text(p) => p.as_str(),
            _ => return VMValue::Bool(false),
        };
        let result = match op_type {
            0 => s.starts_with(p),  // starts_with
            1 => s.ends_with(p),    // ends_with
            2 => s.contains(p),     // contains
            3 => s == p,            // matches
            _ => false,
        };
        VMValue::Bool(result)
    }

    fn index_access(&self, obj: &VMValue, index: &VMValue) -> VMValue {
        match (obj, index) {
            (VMValue::List(items), VMValue::Int(i)) => {
                let idx = if *i < 0 {
                    (items.len() as i64 + i) as usize
                } else {
                    *i as usize
                };
                items.get(idx).cloned().unwrap_or(VMValue::Unbound)
            }
            (VMValue::Text(s), VMValue::Int(i)) => {
                let idx = if *i < 0 {
                    (s.len() as i64 + i) as usize
                } else {
                    *i as usize
                };
                s.chars()
                    .nth(idx)
                    .map(|c| VMValue::Text(c.to_string()))
                    .unwrap_or(VMValue::Unbound)
            }
            (VMValue::Record { fields, .. }, VMValue::Text(key)) => {
                fields.get(key).cloned().unwrap_or(VMValue::Unbound)
            }
            _ => VMValue::Unbound,
        }
    }

    fn call_function(&mut self, name: &str, arg_count: u8) -> Result<(), String> {
        // Recursion limit
        if self.call_stack.depth() > 500 {
            return Err(format!("Maximum recursion depth exceeded calling '{}'", name));
        }

        // Check for closure on stack
        let closure_val = self.call_stack.get_var(name);
        if let VMValue::Closure {
            func_name,
            param_count: _,
            captures,
        } = closure_val
        {
            return self.setup_closure_call(&func_name, captures, arg_count);
        }

        let func_info = self
            .chunk
            .functions
            .get(name)
            .ok_or_else(|| format!("Undefined function: {}", name))?
            .clone();

        // Set up call frame — dispatch_loop will continue executing from new IP
        let frame = CallFrame::new(self.ip as u32, self.stack.len());
        self.call_stack.push(frame);

        // Bind arguments to parameter names (pop in reverse)
        let mut args = Vec::new();
        for _ in 0..arg_count {
            args.push(self.stack.pop());
        }
        args.reverse();

        for (i, param_name) in func_info.param_names.iter().enumerate() {
            let val = args.get(i).cloned().unwrap_or(VMValue::None);
            self.call_stack.set_var(param_name, val);
        }

        // Just change IP — the main dispatch_loop continues from here
        self.ip = func_info.offset as usize;

        Ok(())
    }

    fn setup_closure_call(
        &mut self,
        func_name: &str,
        captures: Vec<(String, VMValue)>,
        arg_count: u8,
    ) -> Result<(), String> {
        let func_info = self
            .chunk
            .functions
            .get(func_name)
            .ok_or_else(|| format!("Undefined closure function: {}", func_name))?
            .clone();

        let frame = CallFrame::new(self.ip as u32, self.stack.len());
        self.call_stack.push(frame);

        // Bind captures
        for (name, val) in &captures {
            self.call_stack.set_var(name, val.clone());
        }

        // Bind arguments
        let mut args = Vec::new();
        for _ in 0..arg_count {
            args.push(self.stack.pop());
        }
        args.reverse();

        for (i, param_name) in func_info.param_names.iter().enumerate() {
            let val = args.get(i).cloned().unwrap_or(VMValue::None);
            self.call_stack.set_var(param_name, val);
        }

        // Just change IP — the main dispatch_loop continues from here
        self.ip = func_info.offset as usize;

        Ok(())
    }

    fn call_builtin(&mut self, id: u16, arg_count: u8) -> Result<(), String> {
        // Special handling for print — it needs to capture output
        if id == builtins::BUILTIN_PRINT {
            let mut parts = Vec::new();
            for _ in 0..arg_count {
                parts.push(self.stack.pop());
            }
            parts.reverse();
            let line = parts.iter().map(|v| format!("{}", v)).collect::<Vec<_>>().join(" ");
            self.output_lines.push(line);
            self.stack.push(VMValue::None);
            return Ok(());
        }

        let mut args = Vec::new();
        for _ in 0..arg_count {
            args.push(self.stack.pop());
        }
        args.reverse();

        let result =
            builtins::call_builtin(id, args).map_err(|e| format!("Builtin error: {}", e))?;
        self.stack.push(result);
        Ok(())
    }
}
