//! AST node definitions for the Sigil language.

// ============================================================
// Program (top-level)
// ============================================================

#[derive(Debug, Clone)]
pub struct Program {
    pub module: Option<ModuleDecl>,
    pub imports: Vec<ImportDecl>,
    pub declarations: Vec<Declaration>,
}

// ============================================================
// Module & Imports
// ============================================================

#[derive(Debug, Clone)]
pub struct ModuleDecl {
    pub path: String,
}

#[derive(Debug, Clone)]
pub struct ImportDecl {
    pub source: String,
    pub kind: String, // "sigil", "python", "rust"
    pub alias: Option<String>,
    pub names: Vec<String>,
}

// ============================================================
// Declarations
// ============================================================

#[derive(Debug, Clone)]
pub enum Declaration {
    Type(TypeDecl),
    Const(ConstDecl),
    Rule(RuleDecl),
    Compute(ComputeDecl),
    Neural(NeuralDecl),
    Main(MainDecl),
    Export(ExportDecl),
}

#[derive(Debug, Clone)]
pub struct TypeDecl {
    pub name: String,
    pub params: Vec<String>,
    pub body: TypeBody,
}

#[derive(Debug, Clone)]
pub enum TypeBody {
    Record(RecordBody),
    Enum(EnumBody),
    Alias(TypeRef),
    Unit { base_type: TypeRef, unit: String },
}

#[derive(Debug, Clone)]
pub struct RecordBody {
    pub fields: Vec<FieldDef>,
}

#[derive(Debug, Clone)]
pub struct FieldDef {
    pub name: String,
    pub type_ref: TypeRef,
}

#[derive(Debug, Clone)]
pub struct EnumBody {
    pub variants: Vec<EnumVariant>,
}

#[derive(Debug, Clone)]
pub struct EnumVariant {
    pub name: String,
    pub fields: Vec<FieldDef>,
}

#[derive(Debug, Clone)]
pub enum TypeRef {
    Named { name: String, params: Vec<TypeRef> },
    List(Box<TypeRef>),
    Option(Box<TypeRef>),
    InlineRecord(Vec<FieldDef>),
}

#[derive(Debug, Clone)]
pub struct ConstDecl {
    pub name: String,
    pub value: Expression,
}

// ============================================================
// Rule Declarations
// ============================================================

#[derive(Debug, Clone)]
pub struct RuleDecl {
    pub name: String,
    pub conditions: Vec<Condition>,
    pub action: Action,
    pub priority: i64,
    pub given_clauses: Vec<GivenClause>,
    pub explain: Option<String>,
    pub trace: Vec<TraceField>,
    pub metadata: Vec<MetaField>,
    pub temporal: Option<TemporalConstraint>,
}

#[derive(Debug, Clone)]
pub struct TemporalConstraint {
    pub duration: Expression,
    pub unit: String,
}

#[derive(Debug, Clone)]
pub struct GivenClause {
    pub name: String,
    pub source: Expression,
    pub kind: String, // "from" or "as"
}

#[derive(Debug, Clone)]
pub struct TraceField {
    pub name: String,
    pub value: Expression,
}

#[derive(Debug, Clone)]
pub struct MetaField {
    pub name: String,
    pub value: Expression,
}

// ============================================================
// Conditions
// ============================================================

#[derive(Debug, Clone)]
pub enum Condition {
    Comparison {
        left: Expression,
        operator: String,
        right: Expression,
        right2: Option<Expression>, // for "is between X and Y"
    },
    Membership {
        element: Expression,
        collection: Expression,
        negated: bool,
    },
    Quantified {
        quantifier: String,
        variable: String,
        collection: Expression,
        condition: Box<Condition>,
    },
    Boolean {
        expression: Expression,
        value: bool,
    },
    Not(Box<Condition>),
    Compound {
        operator: String,
        left: Box<Condition>,
        right: Box<Condition>,
    },
    IsAssigned {
        expression: Expression,
        negated: bool,
    },
    IsEmpty {
        expression: Expression,
        negated: bool,
    },
    Contains {
        collection: Expression,
        element: Expression,
    },
    HasCount {
        collection: Expression,
        count: Expression,
    },
    StringCond {
        string: Expression,
        operator: String,
        pattern: Expression,
    },
}

// ============================================================
// Actions
// ============================================================

#[derive(Debug, Clone)]
pub enum Action {
    Simple {
        name: String,
        target: Option<String>,
        params: Vec<ActionParam>,
    },
    Set {
        target: Expression,
        value: Expression,
    },
    Block {
        body: Vec<Statement>,
    },
}

#[derive(Debug, Clone)]
pub struct ActionParam {
    pub name: String,
    pub value: Expression,
}

// ============================================================
// Compute Declarations
// ============================================================

#[derive(Debug, Clone)]
pub struct ComputeDecl {
    pub name: String,
    pub params: Vec<Param>,
    pub body: Vec<Statement>,
    pub return_type: Option<TypeRef>,
}

#[derive(Debug, Clone)]
pub struct Param {
    pub name: String,
    pub type_ref: Option<TypeRef>,
}

// ============================================================
// Neural Declarations
// ============================================================

#[derive(Debug, Clone)]
pub struct NeuralDecl {
    pub name: String,
    pub param_name: String,
    pub param_type: TypeRef,
    pub fields: Vec<NeuralField>,
}

#[derive(Debug, Clone)]
pub struct NeuralField {
    pub name: String,
    pub value: NeuralFieldValue,
}

#[derive(Debug, Clone)]
pub enum NeuralFieldValue {
    Expr(Expression),
    Type(TypeRef),
}

// ============================================================
// Main Declaration
// ============================================================

#[derive(Debug, Clone)]
pub struct MainDecl {
    pub body: Vec<Statement>,
    pub trace: Vec<TraceField>,
}

// ============================================================
// Statements
// ============================================================

#[derive(Debug, Clone)]
pub enum Statement {
    Given {
        name: String,
        value: Expression,
        kind: String, // "as" or "from"
    },
    Return(Expression),
    If {
        condition: Condition,
        body: Vec<Statement>,
        elif_clauses: Vec<ElifClause>,
        else_body: Vec<Statement>,
    },
    For {
        variable: String,
        iterable: Expression,
        body: Vec<Statement>,
    },
    Evaluate {
        target: String,
        argument: Expression,
    },
    Become {
        target: Expression,
        value: Expression,
    },
    Expr(Expression),
    Query {
        goal: String,
        argument: Option<Expression>,
    },
}

#[derive(Debug, Clone)]
pub struct ElifClause {
    pub condition: Condition,
    pub body: Vec<Statement>,
}

// ============================================================
// Expressions
// ============================================================

#[derive(Debug, Clone)]
pub enum Expression {
    Literal {
        value: LiteralValue,
        kind: String,
        unit: Option<String>,
    },
    Symbol(String),
    Identifier(String),
    BinaryOp {
        left: Box<Expression>,
        operator: String,
        right: Box<Expression>,
    },
    UnaryOp {
        operator: String,
        operand: Box<Expression>,
    },
    FieldAccess {
        object: Box<Expression>,
        field: String,
    },
    FuncCall {
        function: Box<Expression>,
        args: Vec<Expression>,
    },
    IndexAccess {
        object: Box<Expression>,
        index: Box<Expression>,
    },
    List(Vec<Expression>),
    Record(Vec<RecordFieldExpr>),
    Match {
        subject: Box<Expression>,
        arms: Vec<MatchArm>,
    },
    Pipeline {
        source: Box<Expression>,
        operations: Vec<PipeOp>,
    },
    Lambda {
        params: Vec<Param>,
        return_type: Option<TypeRef>,
        body: Vec<Statement>,
    },
    Constructor {
        name: String,
        fields: Vec<ActionParam>,
    },
    Empty {
        kind: String,
    },
}

#[derive(Debug, Clone)]
pub enum LiteralValue {
    Int(i64),
    Float(f64),
    Str(String),
    Bool(bool),
    None,
}

#[derive(Debug, Clone)]
pub struct RecordFieldExpr {
    pub name: String,
    pub value: Expression,
}

#[derive(Debug, Clone)]
pub struct MatchArm {
    pub pattern: Expression,
    pub body: Expression,
}

#[derive(Debug, Clone)]
pub struct PipeOp {
    pub kind: String,
    pub args: Vec<Expression>,
    pub condition: Option<Condition>,
    pub direction: Option<String>,
}

// ============================================================
// Export
// ============================================================

#[derive(Debug, Clone)]
pub struct ExportDecl {
    pub names: Vec<String>,
}
