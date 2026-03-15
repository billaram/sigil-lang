//! Bytecode chunk — instruction stream + constant pools.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use super::opcodes::Opcode;

/// Metadata for a compiled function.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FuncInfo {
    pub offset: u32,
    pub param_count: u8,
    pub param_names: Vec<String>,
}

/// Metadata for a compiled rule.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RuleInfo {
    pub name: String,
    pub priority: i64,
    pub cond_offset: u32,
    pub action_offset: u32,
    pub explain_idx: Option<u32>,
}

/// A compiled bytecode chunk.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Chunk {
    pub code: Vec<Opcode>,
    pub strings: Vec<String>,
    pub functions: HashMap<String, FuncInfo>,
    pub rules: Vec<RuleInfo>,
    pub main_offset: Option<u32>,
    pub init_offset: Option<u32>,
}

impl Chunk {
    pub fn new() -> Self {
        Chunk {
            code: Vec::new(),
            strings: Vec::new(),
            functions: HashMap::new(),
            rules: Vec::new(),
            main_offset: None,
            init_offset: None,
        }
    }

    /// Intern a string, returning its index.
    pub fn intern_string(&mut self, s: &str) -> u32 {
        if let Some(idx) = self.strings.iter().position(|existing| existing == s) {
            return idx as u32;
        }
        let idx = self.strings.len() as u32;
        self.strings.push(s.to_string());
        idx
    }

    /// Emit an opcode, returning its offset.
    pub fn emit(&mut self, op: Opcode) -> u32 {
        let offset = self.code.len() as u32;
        self.code.push(op);
        offset
    }

    /// Current bytecode offset (next instruction position).
    pub fn current_offset(&self) -> u32 {
        self.code.len() as u32
    }

    /// Patch a jump instruction's target.
    pub fn patch_jump(&mut self, offset: u32, target: u32) {
        let idx = offset as usize;
        match &mut self.code[idx] {
            Opcode::Jump(ref mut t) => *t = target,
            Opcode::JumpIfFalse(ref mut t) => *t = target,
            Opcode::JumpIfTrue(ref mut t) => *t = target,
            Opcode::JumpIfUnbound(ref mut t) => *t = target,
            _ => panic!("Cannot patch non-jump opcode at offset {}", offset),
        }
    }
}
