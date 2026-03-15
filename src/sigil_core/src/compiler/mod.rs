//! Sigil AST -> bytecode compiler.
//!
//! Walks the Rust AST and emits opcodes into a Chunk for the VM.

use crate::parser::ast::*;
use crate::vm::{Chunk, FuncInfo, RuleInfo, Opcode};

#[cfg(test)]
mod tests;

// Builtin function IDs — must match vm/builtins.rs constants.
const BUILTIN_PRINT: u16 = 0;
const BUILTIN_MAX: u16 = 1;
const BUILTIN_MIN: u16 = 2;
const BUILTIN_LEN: u16 = 3;
const BUILTIN_TYPE_OF: u16 = 4;
const BUILTIN_ABS: u16 = 5;
const BUILTIN_ROUND: u16 = 6;
const BUILTIN_SQRT: u16 = 7;
const BUILTIN_FLOOR: u16 = 8;
const BUILTIN_CEIL: u16 = 9;
const BUILTIN_APPEND: u16 = 10;
const BUILTIN_RANGE: u16 = 11;
const BUILTIN_SUM: u16 = 12;
const BUILTIN_TO_TEXT: u16 = 13;
const BUILTIN_TO_NUMBER: u16 = 14;

fn builtin_id(name: &str) -> Option<u16> {
    match name {
        "print" => Some(BUILTIN_PRINT),
        "max" => Some(BUILTIN_MAX),
        "min" => Some(BUILTIN_MIN),
        "len" => Some(BUILTIN_LEN),
        "type_of" => Some(BUILTIN_TYPE_OF),
        "abs" => Some(BUILTIN_ABS),
        "round" => Some(BUILTIN_ROUND),
        "sqrt" => Some(BUILTIN_SQRT),
        "floor" => Some(BUILTIN_FLOOR),
        "ceil" => Some(BUILTIN_CEIL),
        "append" => Some(BUILTIN_APPEND),
        "range" => Some(BUILTIN_RANGE),
        "sum" => Some(BUILTIN_SUM),
        "to_text" => Some(BUILTIN_TO_TEXT),
        "to_number" => Some(BUILTIN_TO_NUMBER),
        _ => None,
    }
}

fn binop_opcode(op: &str) -> Opcode {
    match op {
        "+" => Opcode::Add,
        "-" => Opcode::Sub,
        "*" => Opcode::Mul,
        "/" => Opcode::Div,
        "%" => Opcode::Mod,
        "==" => Opcode::Eq,
        "!=" => Opcode::Neq,
        ">" => Opcode::Gt,
        "<" => Opcode::Lt,
        ">=" => Opcode::Gte,
        "<=" => Opcode::Lte,
        "and" => Opcode::And,
        "or" => Opcode::Or,
        _ => Opcode::Eq,
    }
}

fn cond_op(op: &str) -> Option<Opcode> {
    match op {
        "exceeds" | "is above" => Some(Opcode::CmpExceeds),
        "is below" | "below" => Some(Opcode::CmpBelow),
        "is at least" | "at least" => Some(Opcode::CmpAtLeast),
        "is at most" | "at most" => Some(Opcode::CmpAtMost),
        "is between" | "between" => None, // handled separately
        "is" | "equals" => Some(Opcode::CmpIs),
        "is not" => Some(Opcode::CmpIsNot),
        _ => None,
    }
}

fn string_op_id(op: &str) -> u8 {
    match op {
        "starts with" | "starts_with" => 0,
        "ends with" | "ends_with" => 1,
        "contains" => 2,
        "matches" => 3,
        _ => 2,
    }
}

/// Compile a Sigil Program AST into a bytecode Chunk.
pub fn compile(program: &Program) -> Chunk {
    let mut c = Compiler::new();
    c.compile(program);
    c.chunk
}

struct Compiler {
    chunk: Chunk,
    lambda_counter: usize,
}

impl Compiler {
    fn new() -> Self {
        Compiler {
            chunk: Chunk::new(),
            lambda_counter: 0,
        }
    }

    fn compile(&mut self, program: &Program) {
        // Phase 1: Constants
        let has_consts = program.declarations.iter().any(|d| matches!(d, Declaration::Const(_)));
        if has_consts {
            self.chunk.init_offset = Some(0);
            for decl in &program.declarations {
                if let Declaration::Const(c) = decl {
                    self.compile_const(c);
                }
            }
            self.chunk.emit(Opcode::Halt);
        }

        // Phase 2: Compute functions
        for decl in &program.declarations {
            if let Declaration::Compute(c) = decl {
                self.compile_compute(c);
            }
        }

        // Phase 3: Rules
        for decl in &program.declarations {
            if let Declaration::Rule(r) = decl {
                self.compile_rule(r);
            }
        }

        // Phase 4: Main block
        for decl in &program.declarations {
            if let Declaration::Main(m) = decl {
                self.chunk.main_offset = Some(self.chunk.current_offset());
                self.compile_main(m);
            }
        }

        self.chunk.emit(Opcode::Halt);
    }

    // --- Constants ---

    fn compile_const(&mut self, decl: &ConstDecl) {
        self.compile_expr(&decl.value);
        let idx = self.chunk.intern_string(&decl.name);
        self.chunk.emit(Opcode::Store(idx));
    }

    // --- Compute Functions ---

    fn compile_compute(&mut self, decl: &ComputeDecl) {
        let jump_offset = self.chunk.emit(Opcode::Jump(0));
        let func_offset = self.chunk.current_offset();
        let param_names: Vec<String> = decl.params.iter().map(|p| p.name.clone()).collect();

        for stmt in &decl.body {
            self.compile_statement(stmt);
        }
        self.chunk.emit(Opcode::PushNone);
        self.chunk.emit(Opcode::Return);

        self.chunk.patch_jump(jump_offset, self.chunk.current_offset());

        self.chunk.functions.insert(
            decl.name.clone(),
            FuncInfo {
                offset: func_offset,
                param_count: decl.params.len() as u8,
                param_names,
            },
        );
    }

    // --- Rules ---

    fn compile_rule(&mut self, rule: &RuleDecl) {
        let jump_offset = self.chunk.emit(Opcode::Jump(0));

        // Condition block
        let cond_offset = self.chunk.current_offset();
        self.compile_rule_conditions(&rule.conditions);
        self.chunk.emit(Opcode::Halt);

        // Action block
        let action_offset = self.chunk.current_offset();
        self.compile_action(&rule.action);
        self.chunk.emit(Opcode::Halt);

        self.chunk.patch_jump(jump_offset, self.chunk.current_offset());

        let explain_idx = rule.explain.as_ref().map(|s| self.chunk.intern_string(s));

        self.chunk.rules.push(RuleInfo {
            name: rule.name.clone(),
            priority: rule.priority,
            cond_offset,
            action_offset,
            explain_idx,
        });
    }

    fn compile_rule_conditions(&mut self, conditions: &[Condition]) {
        if conditions.is_empty() {
            self.chunk.emit(Opcode::PushBool(true));
            return;
        }

        let flat = self.flatten_conditions(conditions);
        let mut false_jumps = Vec::new();
        for cond in &flat {
            self.compile_condition(cond);
            false_jumps.push(self.chunk.emit(Opcode::JumpIfFalse(0)));
        }

        // All passed
        self.chunk.emit(Opcode::PushBool(true));
        let end_jump = self.chunk.emit(Opcode::Jump(0));

        // Any failed
        for j in false_jumps {
            self.chunk.patch_jump(j, self.chunk.current_offset());
        }
        self.chunk.emit(Opcode::PushBool(false));

        self.chunk.patch_jump(end_jump, self.chunk.current_offset());
    }

    fn flatten_conditions(&self, conditions: &[Condition]) -> Vec<Condition> {
        let mut result = Vec::new();
        for cond in conditions {
            if let Condition::Compound { operator, left, right } = cond {
                if operator == "and" {
                    result.extend(self.flatten_conditions(&[*left.clone()]));
                    result.extend(self.flatten_conditions(&[*right.clone()]));
                } else {
                    result.push(cond.clone());
                }
            } else {
                result.push(cond.clone());
            }
        }
        result
    }

    // --- Conditions ---

    fn compile_condition(&mut self, cond: &Condition) {
        match cond {
            Condition::Comparison { left, operator, right, right2 } => {
                self.compile_comparison_cond(left, operator, right, right2.as_ref());
            }
            Condition::Compound { operator, left, right } => {
                self.compile_compound_cond(operator, left, right);
            }
            Condition::Boolean { expression, value } => {
                self.compile_expr(expression);
                if !value {
                    self.chunk.emit(Opcode::Not);
                }
            }
            Condition::Not(inner) => {
                self.compile_condition(inner);
                self.chunk.emit(Opcode::Not);
            }
            Condition::Membership { element, collection, negated } => {
                self.compile_expr(element);
                self.compile_expr(collection);
                self.chunk.emit(Opcode::InList);
                if *negated {
                    self.chunk.emit(Opcode::Not);
                }
            }
            Condition::IsAssigned { expression, negated } => {
                self.compile_expr(expression);
                self.chunk.emit(Opcode::IsAssigned);
                if *negated {
                    self.chunk.emit(Opcode::Not);
                }
            }
            Condition::IsEmpty { expression, negated } => {
                self.compile_expr(expression);
                self.chunk.emit(Opcode::IsEmpty);
                if *negated {
                    self.chunk.emit(Opcode::Not);
                }
            }
            Condition::Contains { collection, element } => {
                self.compile_expr(collection);
                self.compile_expr(element);
                self.chunk.emit(Opcode::Contains);
            }
            Condition::HasCount { collection, count } => {
                self.compile_expr(collection);
                self.compile_expr(count);
                self.chunk.emit(Opcode::HasCount);
            }
            Condition::StringCond { string, operator, pattern } => {
                self.compile_expr(string);
                self.compile_expr(pattern);
                let id = string_op_id(operator);
                self.chunk.emit(Opcode::StringOp(id));
            }
            Condition::Quantified { quantifier, collection, .. } => {
                // Simplified: push default value
                self.compile_expr(collection);
                self.chunk.emit(Opcode::Pop);
                self.chunk.emit(Opcode::PushBool(quantifier != "none"));
            }
        }
    }

    fn compile_comparison_cond(
        &mut self,
        left: &Expression,
        operator: &str,
        right: &Expression,
        right2: Option<&Expression>,
    ) {
        if operator == "is between" || operator == "between" {
            self.compile_expr(left);
            self.compile_expr(right);
            if let Some(r2) = right2 {
                self.compile_expr(r2);
            } else {
                self.chunk.emit(Opcode::PushNone);
            }
            self.chunk.emit(Opcode::CmpBetween);
        } else if let Some(op) = cond_op(operator) {
            self.compile_expr(left);
            self.compile_expr(right);
            self.chunk.emit(op);
        } else {
            self.compile_expr(left);
            self.compile_expr(right);
            self.chunk.emit(Opcode::Eq);
        }
    }

    fn compile_compound_cond(&mut self, operator: &str, left: &Condition, right: &Condition) {
        self.compile_condition(left);
        if operator == "and" {
            let jump_false = self.chunk.emit(Opcode::JumpIfFalse(0));
            self.compile_condition(right);
            let end_jump = self.chunk.emit(Opcode::Jump(0));
            self.chunk.patch_jump(jump_false, self.chunk.current_offset());
            self.chunk.emit(Opcode::PushBool(false));
            self.chunk.patch_jump(end_jump, self.chunk.current_offset());
        } else if operator == "or" {
            let jump_true = self.chunk.emit(Opcode::JumpIfTrue(0));
            self.compile_condition(right);
            let end_jump = self.chunk.emit(Opcode::Jump(0));
            self.chunk.patch_jump(jump_true, self.chunk.current_offset());
            self.chunk.emit(Opcode::PushBool(true));
            self.chunk.patch_jump(end_jump, self.chunk.current_offset());
        }
    }

    // --- Actions ---

    fn compile_action(&mut self, action: &Action) {
        match action {
            Action::Set { target, value } => {
                self.compile_expr(value);
                match target {
                    Expression::Identifier(name) => {
                        let idx = self.chunk.intern_string(name);
                        self.chunk.emit(Opcode::Store(idx));
                    }
                    Expression::FieldAccess { object, field } => {
                        self.compile_expr(object);
                        let idx = self.chunk.intern_string(field);
                        self.chunk.emit(Opcode::StoreField(idx));
                    }
                    _ => {}
                }
            }
            Action::Simple { name, target, params } => {
                self.compile_simple_action(name, target.as_deref(), params);
            }
            Action::Block { body } => {
                for stmt in body {
                    self.compile_statement(stmt);
                }
            }
        }
    }

    fn compile_simple_action(&mut self, name: &str, target: Option<&str>, params: &[ActionParam]) {
        if let Some(bid) = builtin_id(name) {
            for p in params {
                self.compile_expr(&p.value);
            }
            self.chunk.emit(Opcode::CallBuiltin(bid, params.len() as u8));
        } else {
            let name_idx = self.chunk.intern_string(name);
            self.chunk.emit(Opcode::PushSymbol(name_idx));
            if let Some(t) = target {
                let target_idx = self.chunk.intern_string(t);
                self.chunk.emit(Opcode::Store(target_idx));
            }
        }
    }

    // --- Statements ---

    fn compile_statement(&mut self, stmt: &Statement) {
        match stmt {
            Statement::Given { name, value, kind } => {
                self.compile_given(name, value, kind);
            }
            Statement::Return(expr) => {
                self.compile_expr(expr);
                self.chunk.emit(Opcode::Return);
            }
            Statement::If { condition, body, elif_clauses, else_body } => {
                self.compile_if(condition, body, elif_clauses, else_body);
            }
            Statement::For { variable, iterable, body } => {
                self.compile_for(variable, iterable, body);
            }
            Statement::Become { target, value } => {
                self.compile_expr(value);
                if let Expression::Identifier(name) = target {
                    let idx = self.chunk.intern_string(name);
                    self.chunk.emit(Opcode::Mutate(idx));
                }
            }
            Statement::Expr(expr) => {
                self.compile_expr_stmt(expr);
            }
            Statement::Evaluate { .. } | Statement::Query { .. } => {
                // No-op in VM
            }
        }
    }

    fn compile_expr_stmt(&mut self, expr: &Expression) {
        if let Expression::FuncCall { function, args } = expr {
            if let Expression::Identifier(name) = function.as_ref() {
                if let Some(bid) = builtin_id(name) {
                    for arg in args {
                        self.compile_expr(arg);
                    }
                    self.chunk.emit(Opcode::CallBuiltin(bid, args.len() as u8));
                    return;
                } else {
                    for arg in args {
                        self.compile_expr(arg);
                    }
                    let idx = self.chunk.intern_string(name);
                    self.chunk.emit(Opcode::Call(idx, args.len() as u8));
                    return;
                }
            }
        }
        self.compile_expr(expr);
        self.chunk.emit(Opcode::Pop);
    }

    fn compile_given(&mut self, name: &str, value: &Expression, kind: &str) {
        let name_idx = self.chunk.intern_string(name);
        if kind == "from" {
            self.chunk.emit(Opcode::Load(name_idx));
            let jump_bound = self.chunk.emit(Opcode::JumpIfUnbound(0));
            self.chunk.emit(Opcode::Pop);
            let end_jump = self.chunk.emit(Opcode::Jump(0));
            self.chunk.patch_jump(jump_bound, self.chunk.current_offset());
            self.chunk.emit(Opcode::Pop);
            self.chunk.patch_jump(end_jump, self.chunk.current_offset());
        } else {
            self.compile_expr(value);
            self.chunk.emit(Opcode::Store(name_idx));
        }
    }

    fn compile_if(
        &mut self,
        condition: &Condition,
        body: &[Statement],
        elif_clauses: &[ElifClause],
        else_body: &[Statement],
    ) {
        self.compile_condition(condition);
        let jump_false = self.chunk.emit(Opcode::JumpIfFalse(0));

        for s in body {
            self.compile_statement(s);
        }
        let jump_end = self.chunk.emit(Opcode::Jump(0));

        let mut elif_end_jumps = Vec::new();
        self.chunk.patch_jump(jump_false, self.chunk.current_offset());

        for elif in elif_clauses {
            self.compile_condition(&elif.condition);
            let elif_false = self.chunk.emit(Opcode::JumpIfFalse(0));
            for s in &elif.body {
                self.compile_statement(s);
            }
            elif_end_jumps.push(self.chunk.emit(Opcode::Jump(0)));
            self.chunk.patch_jump(elif_false, self.chunk.current_offset());
        }

        for s in else_body {
            self.compile_statement(s);
        }

        self.chunk.patch_jump(jump_end, self.chunk.current_offset());
        for j in elif_end_jumps {
            self.chunk.patch_jump(j, self.chunk.current_offset());
        }
    }

    fn compile_for(&mut self, variable: &str, iterable: &Expression, body: &[Statement]) {
        self.compile_expr(iterable);

        let var_idx = self.chunk.intern_string(variable);
        let list_name = format!("__for_list_{}", variable);
        let list_idx = self.chunk.intern_string(&list_name);
        self.chunk.emit(Opcode::Store(list_idx));

        let counter_name = format!("__for_i_{}", variable);
        let counter_idx = self.chunk.intern_string(&counter_name);
        self.chunk.emit(Opcode::PushInt(0));
        self.chunk.emit(Opcode::Store(counter_idx));

        let loop_start = self.chunk.current_offset();

        // counter >= len(list) → exit
        self.chunk.emit(Opcode::Load(counter_idx));
        self.chunk.emit(Opcode::Load(list_idx));
        self.chunk.emit(Opcode::CallBuiltin(BUILTIN_LEN, 1));
        self.chunk.emit(Opcode::Gte);
        let jump_end = self.chunk.emit(Opcode::JumpIfTrue(0));

        // element = list[counter]
        self.chunk.emit(Opcode::Load(list_idx));
        self.chunk.emit(Opcode::Load(counter_idx));
        self.chunk.emit(Opcode::IndexAccess);
        self.chunk.emit(Opcode::Store(var_idx));

        for s in body {
            self.compile_statement(s);
        }

        // counter += 1
        self.chunk.emit(Opcode::Load(counter_idx));
        self.chunk.emit(Opcode::PushInt(1));
        self.chunk.emit(Opcode::Add);
        self.chunk.emit(Opcode::Store(counter_idx));

        self.chunk.emit(Opcode::Jump(loop_start));
        self.chunk.patch_jump(jump_end, self.chunk.current_offset());
    }

    // --- Main Block ---

    fn compile_main(&mut self, decl: &MainDecl) {
        for stmt in &decl.body {
            self.compile_statement(stmt);
        }
    }

    // --- Expressions ---

    fn compile_expr(&mut self, expr: &Expression) {
        match expr {
            Expression::Literal { value, kind, .. } => {
                self.compile_literal(value, kind);
            }
            Expression::Symbol(name) => {
                let idx = self.chunk.intern_string(name);
                self.chunk.emit(Opcode::PushSymbol(idx));
            }
            Expression::Identifier(name) => {
                let idx = self.chunk.intern_string(name);
                self.chunk.emit(Opcode::Load(idx));
            }
            Expression::BinaryOp { left, operator, right } => {
                self.compile_expr(left);
                self.compile_expr(right);
                self.chunk.emit(binop_opcode(operator));
            }
            Expression::UnaryOp { operator, operand } => {
                self.compile_expr(operand);
                match operator.as_str() {
                    "-" => { self.chunk.emit(Opcode::Neg); }
                    "not" => { self.chunk.emit(Opcode::Not); }
                    _ => {}
                }
            }
            Expression::FieldAccess { object, field } => {
                self.compile_expr(object);
                let idx = self.chunk.intern_string(field);
                self.chunk.emit(Opcode::LoadField(idx));
            }
            Expression::FuncCall { function, args } => {
                self.compile_func_call(function, args);
            }
            Expression::IndexAccess { object, index } => {
                self.compile_expr(object);
                self.compile_expr(index);
                self.chunk.emit(Opcode::IndexAccess);
            }
            Expression::List(elements) => {
                for elem in elements {
                    self.compile_expr(elem);
                }
                self.chunk.emit(Opcode::PushList(elements.len() as u16));
            }
            Expression::Record(fields) => {
                for f in fields {
                    let key_idx = self.chunk.intern_string(&f.name);
                    self.chunk.emit(Opcode::PushString(key_idx));
                    self.compile_expr(&f.value);
                }
                self.chunk.emit(Opcode::PushRecord(fields.len() as u16));
            }
            Expression::Match { subject, arms } => {
                self.compile_match(subject, arms);
            }
            Expression::Pipeline { source, operations } => {
                self.compile_pipeline(source, operations);
            }
            Expression::Lambda { params, body, .. } => {
                self.compile_lambda(params, body);
            }
            Expression::Constructor { name: _, fields } => {
                for f in fields {
                    let key_idx = self.chunk.intern_string(&f.name);
                    self.chunk.emit(Opcode::PushString(key_idx));
                    self.compile_expr(&f.value);
                }
                self.chunk.emit(Opcode::PushRecord(fields.len() as u16));
            }
            Expression::Empty { kind } => {
                if kind == "list" {
                    self.chunk.emit(Opcode::PushList(0));
                } else {
                    self.chunk.emit(Opcode::PushNone);
                }
            }
        }
    }

    fn compile_literal(&mut self, value: &LiteralValue, kind: &str) {
        match kind {
            "number" => match value {
                LiteralValue::Int(n) => { self.chunk.emit(Opcode::PushInt(*n)); }
                LiteralValue::Float(f) => { self.chunk.emit(Opcode::PushFloat(*f)); }
                _ => { self.chunk.emit(Opcode::PushNone); }
            },
            "string" => {
                if let LiteralValue::Str(s) = value {
                    let idx = self.chunk.intern_string(s);
                    self.chunk.emit(Opcode::PushString(idx));
                } else {
                    self.chunk.emit(Opcode::PushNone);
                }
            }
            "bool" => {
                if let LiteralValue::Bool(b) = value {
                    self.chunk.emit(Opcode::PushBool(*b));
                } else {
                    self.chunk.emit(Opcode::PushNone);
                }
            }
            "none" => { self.chunk.emit(Opcode::PushNone); }
            _ => { self.chunk.emit(Opcode::PushNone); }
        }
    }

    fn compile_func_call(&mut self, function: &Expression, args: &[Expression]) {
        let func_name = match function {
            Expression::Identifier(name) => Some(name.as_str()),
            Expression::FieldAccess { field, .. } => Some(field.as_str()),
            _ => None,
        };

        if let Some(name) = func_name {
            if let Some(bid) = builtin_id(name) {
                for arg in args {
                    self.compile_expr(arg);
                }
                self.chunk.emit(Opcode::CallBuiltin(bid, args.len() as u8));
            } else {
                for arg in args {
                    self.compile_expr(arg);
                }
                let idx = self.chunk.intern_string(name);
                self.chunk.emit(Opcode::Call(idx, args.len() as u8));
            }
        } else {
            self.compile_expr(function);
            for arg in args {
                self.compile_expr(arg);
            }
            self.chunk.emit(Opcode::PushNone);
        }
    }

    fn compile_match(&mut self, subject: &Expression, arms: &[MatchArm]) {
        self.compile_expr(subject);
        let subject_idx = self.chunk.intern_string("__match_subject");
        self.chunk.emit(Opcode::Store(subject_idx));

        let mut end_jumps = Vec::new();
        for arm in arms {
            let is_wildcard = matches!(&arm.pattern, Expression::Identifier(n) if n == "_");

            if is_wildcard {
                self.compile_expr(&arm.body);
                end_jumps.push(self.chunk.emit(Opcode::Jump(0)));
            } else {
                self.chunk.emit(Opcode::Load(subject_idx));
                self.compile_expr(&arm.pattern);
                self.chunk.emit(Opcode::Eq);
                let jump_next = self.chunk.emit(Opcode::JumpIfFalse(0));

                self.compile_expr(&arm.body);
                end_jumps.push(self.chunk.emit(Opcode::Jump(0)));

                self.chunk.patch_jump(jump_next, self.chunk.current_offset());
            }
        }

        self.chunk.emit(Opcode::PushNone);

        for j in end_jumps {
            self.chunk.patch_jump(j, self.chunk.current_offset());
        }
    }

    fn compile_pipeline(&mut self, source: &Expression, operations: &[PipeOp]) {
        self.compile_expr(source);

        for pipe_op in operations {
            match pipe_op.kind.as_str() {
                "filter" => self.compile_pipeline_filter(pipe_op),
                "transform" => self.compile_pipeline_transform(pipe_op),
                "sort" => { /* complex — leave on stack */ }
                "count" => {
                    self.chunk.emit(Opcode::CallBuiltin(BUILTIN_LEN, 1));
                }
                "sum" => {
                    self.chunk.emit(Opcode::CallBuiltin(BUILTIN_SUM, 1));
                }
                "first" => {
                    self.chunk.emit(Opcode::PushInt(0));
                    self.chunk.emit(Opcode::IndexAccess);
                }
                "last" => {
                    self.chunk.emit(Opcode::PushInt(-1));
                    self.chunk.emit(Opcode::IndexAccess);
                }
                _ => {
                    if let Some(arg) = pipe_op.args.first() {
                        if let Expression::Identifier(fname) = arg {
                            if let Some(bid) = builtin_id(fname) {
                                self.chunk.emit(Opcode::CallBuiltin(bid, 1));
                            }
                        }
                    }
                }
            }
        }
    }

    fn compile_pipeline_filter(&mut self, pipe_op: &PipeOp) {
        let src_idx = self.chunk.intern_string("__pipe_src");
        self.chunk.emit(Opcode::Store(src_idx));

        self.chunk.emit(Opcode::PushList(0));
        let result_idx = self.chunk.intern_string("__pipe_result");
        self.chunk.emit(Opcode::Store(result_idx));

        let counter_idx = self.chunk.intern_string("__pipe_i");
        self.chunk.emit(Opcode::PushInt(0));
        self.chunk.emit(Opcode::Store(counter_idx));

        let loop_start = self.chunk.current_offset();
        self.chunk.emit(Opcode::Load(src_idx));
        self.chunk.emit(Opcode::CallBuiltin(BUILTIN_LEN, 1));
        self.chunk.emit(Opcode::Load(counter_idx));
        self.chunk.emit(Opcode::Gte);
        let jump_end = self.chunk.emit(Opcode::JumpIfTrue(0));

        let item_idx = self.chunk.intern_string("__pipe_item");
        self.chunk.emit(Opcode::Load(src_idx));
        self.chunk.emit(Opcode::Load(counter_idx));
        self.chunk.emit(Opcode::IndexAccess);
        self.chunk.emit(Opcode::Store(item_idx));

        if pipe_op.condition.is_some() {
            self.compile_condition(pipe_op.condition.as_ref().unwrap());
        } else if let Some(arg) = pipe_op.args.first() {
            self.compile_expr(arg);
        } else {
            self.chunk.emit(Opcode::PushBool(true));
        }

        let jump_skip = self.chunk.emit(Opcode::JumpIfFalse(0));

        self.chunk.emit(Opcode::Load(result_idx));
        self.chunk.emit(Opcode::Load(item_idx));
        self.chunk.emit(Opcode::CallBuiltin(BUILTIN_APPEND, 2));
        self.chunk.emit(Opcode::Store(result_idx));

        self.chunk.patch_jump(jump_skip, self.chunk.current_offset());

        self.chunk.emit(Opcode::Load(counter_idx));
        self.chunk.emit(Opcode::PushInt(1));
        self.chunk.emit(Opcode::Add);
        self.chunk.emit(Opcode::Store(counter_idx));
        self.chunk.emit(Opcode::Jump(loop_start));

        self.chunk.patch_jump(jump_end, self.chunk.current_offset());
        self.chunk.emit(Opcode::Load(result_idx));
    }

    fn compile_pipeline_transform(&mut self, pipe_op: &PipeOp) {
        let src_idx = self.chunk.intern_string("__pipe_tsrc");
        self.chunk.emit(Opcode::Store(src_idx));

        self.chunk.emit(Opcode::PushList(0));
        let result_idx = self.chunk.intern_string("__pipe_tresult");
        self.chunk.emit(Opcode::Store(result_idx));

        let counter_idx = self.chunk.intern_string("__pipe_ti");
        self.chunk.emit(Opcode::PushInt(0));
        self.chunk.emit(Opcode::Store(counter_idx));

        let loop_start = self.chunk.current_offset();
        self.chunk.emit(Opcode::Load(src_idx));
        self.chunk.emit(Opcode::CallBuiltin(BUILTIN_LEN, 1));
        self.chunk.emit(Opcode::Load(counter_idx));
        self.chunk.emit(Opcode::Gte);
        let jump_end = self.chunk.emit(Opcode::JumpIfTrue(0));

        let item_idx = self.chunk.intern_string("__pipe_titem");
        self.chunk.emit(Opcode::Load(src_idx));
        self.chunk.emit(Opcode::Load(counter_idx));
        self.chunk.emit(Opcode::IndexAccess);
        self.chunk.emit(Opcode::Store(item_idx));

        // Apply transform
        if !pipe_op.args.is_empty() {
            self.chunk.emit(Opcode::Load(item_idx));
            for arg in &pipe_op.args {
                self.compile_expr(arg);
            }
        } else {
            self.chunk.emit(Opcode::Load(item_idx));
        }

        self.chunk.emit(Opcode::Load(result_idx));
        self.chunk.emit(Opcode::CallBuiltin(BUILTIN_APPEND, 2));
        self.chunk.emit(Opcode::Store(result_idx));

        self.chunk.emit(Opcode::Load(counter_idx));
        self.chunk.emit(Opcode::PushInt(1));
        self.chunk.emit(Opcode::Add);
        self.chunk.emit(Opcode::Store(counter_idx));
        self.chunk.emit(Opcode::Jump(loop_start));

        self.chunk.patch_jump(jump_end, self.chunk.current_offset());
        self.chunk.emit(Opcode::Load(result_idx));
    }

    fn compile_lambda(&mut self, params: &[Param], body: &[Statement]) {
        let func_name = format!("__lambda_{}", self.lambda_counter);
        self.lambda_counter += 1;

        let jump_offset = self.chunk.emit(Opcode::Jump(0));
        let func_offset = self.chunk.current_offset();
        let param_names: Vec<String> = params.iter().map(|p| p.name.clone()).collect();

        for stmt in body {
            self.compile_statement(stmt);
        }
        self.chunk.emit(Opcode::Return);
        self.chunk.patch_jump(jump_offset, self.chunk.current_offset());

        self.chunk.functions.insert(
            func_name.clone(),
            FuncInfo {
                offset: func_offset,
                param_count: params.len() as u8,
                param_names,
            },
        );

        let name_idx = self.chunk.intern_string(&func_name);
        self.chunk.emit(Opcode::MakeClosure(name_idx, 0));
    }
}
