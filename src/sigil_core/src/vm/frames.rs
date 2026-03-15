//! Call frames for VM function calls.

use std::collections::HashMap;

use super::stack::VMValue;

/// A single call frame on the VM call stack.
pub struct CallFrame {
    /// Return address (instruction offset to resume at).
    pub return_addr: u32,
    /// Local variable bindings for this frame.
    pub locals: HashMap<String, VMValue>,
    /// Stack base — where this frame's stack values start.
    pub stack_base: usize,
}

impl CallFrame {
    pub fn new(return_addr: u32, stack_base: usize) -> Self {
        CallFrame {
            return_addr,
            locals: HashMap::new(),
            stack_base,
        }
    }
}

/// Call stack — manages nested function calls.
pub struct CallStack {
    frames: Vec<CallFrame>,
}

impl CallStack {
    pub fn new() -> Self {
        // Start with a global frame
        let global = CallFrame::new(0, 0);
        CallStack {
            frames: vec![global],
        }
    }

    pub fn push(&mut self, frame: CallFrame) {
        self.frames.push(frame);
    }

    pub fn pop(&mut self) -> Option<CallFrame> {
        if self.frames.len() > 1 {
            self.frames.pop()
        } else {
            Option::None // Never pop the global frame
        }
    }

    pub fn current(&self) -> &CallFrame {
        self.frames.last().unwrap()
    }

    pub fn current_mut(&mut self) -> &mut CallFrame {
        self.frames.last_mut().unwrap()
    }

    /// Look up a variable — check current frame first, then walk up.
    pub fn get_var(&self, name: &str) -> VMValue {
        for frame in self.frames.iter().rev() {
            if let Some(val) = frame.locals.get(name) {
                return val.clone();
            }
        }
        VMValue::Unbound
    }

    /// Set a variable in the current frame.
    pub fn set_var(&mut self, name: &str, value: VMValue) {
        self.current_mut().locals.insert(name.to_string(), value);
    }

    /// Set a variable — update existing binding if found, otherwise set in current frame.
    pub fn set_var_scoped(&mut self, name: &str, value: VMValue) {
        // Walk frames to find existing binding
        for frame in self.frames.iter_mut().rev() {
            if frame.locals.contains_key(name) {
                frame.locals.insert(name.to_string(), value);
                return;
            }
        }
        // Not found — set in current frame
        self.current_mut().locals.insert(name.to_string(), value);
    }

    /// Get all bindings (for trace output).
    pub fn all_bindings(&self) -> HashMap<String, VMValue> {
        let mut result = HashMap::new();
        for frame in &self.frames {
            for (k, v) in &frame.locals {
                result.insert(k.clone(), v.clone());
            }
        }
        result
    }

    pub fn depth(&self) -> usize {
        self.frames.len()
    }
}
