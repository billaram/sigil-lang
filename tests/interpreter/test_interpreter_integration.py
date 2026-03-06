"""Integration tests — run all 5 example .sigil programs through the interpreter."""

from sigil.interpreter.evaluator import evaluate
from sigil.interpreter.values import Record, Symbol, Variant
from sigil.lexer import tokenize
from sigil.parser import parse


def run_file(source: str, input_data: dict | None = None):
    """Parse and evaluate a Sigil source file."""
    tokens = tokenize(source, "<test>")
    program = parse(tokens, "<test>")
    return evaluate(program, input_data)


class TestHello:
    def test_hello_output(self, hello_source):
        _, trace = run_file(hello_source)
        assert "Hello from Sigil!" in trace.output_lines

    def test_hello_rule_fired(self, hello_source):
        _, trace = run_file(hello_source)
        fired = [rt for rt in trace.rule_traces if rt.fired]
        assert len(fired) == 1
        assert fired[0].rule_name == "hello_world"

    def test_hello_explain(self, hello_source):
        _, trace = run_file(hello_source)
        fired = [rt for rt in trace.rule_traces if rt.fired]
        assert fired[0].explain == "This is the simplest possible Sigil program"


class TestTemperature:
    def _make_reading(self, temp, status=":active", sensor_id="S1"):
        return Record(type_name=None, fields={
            "temperature": temp,
            "status": Symbol(status.lstrip(":")),
            "sensor_id": sensor_id,
        })

    def test_emergency_shutdown(self, temperature_source):
        reading = self._make_reading(160)
        result, trace = run_file(temperature_source, {"reading": reading})
        fired = {rt.rule_name for rt in trace.rule_traces if rt.fired}
        assert "emergency_shutdown" in fired

    def test_temperature_alert(self, temperature_source):
        reading = self._make_reading(105)
        result, trace = run_file(temperature_source, {"reading": reading})
        fired = {rt.rule_name for rt in trace.rule_traces if rt.fired}
        assert "temperature_alert" in fired

    def test_temperature_warning(self, temperature_source):
        reading = self._make_reading(82)
        result, trace = run_file(temperature_source, {"reading": reading})
        fired = {rt.rule_name for rt in trace.rule_traces if rt.fired}
        assert "temperature_warning" in fired

    def test_normal_operation(self, temperature_source):
        reading = self._make_reading(68)
        result, trace = run_file(temperature_source, {"reading": reading})
        fired = {rt.rule_name for rt in trace.rule_traces if rt.fired}
        assert "normal_operation" in fired

    def test_inactive_sensor(self, temperature_source):
        """Inactive sensor should not trigger temp alert even if hot."""
        reading = self._make_reading(105, status=":inactive")
        _, trace = run_file(temperature_source, {"reading": reading})
        fired = {rt.rule_name for rt in trace.rule_traces if rt.fired}
        # temperature_alert requires :active status
        assert "temperature_alert" not in fired


class TestLoanEligibility:
    def _make_applicant(self, **kwargs):
        defaults = {
            "age": 30,
            "income": 75000,
            "credit_score": 720,
            "employment_status": Symbol("employed"),
            "debt_to_income": 0.35,
            "employment_years": 5,
        }
        defaults.update(kwargs)
        return Record(type_name=None, fields=defaults)

    def test_approved(self, loan_source):
        applicant = self._make_applicant()
        result, trace = run_file(loan_source, {"applicant": applicant})
        assert isinstance(result, Variant)
        assert result.variant_name == "approved"
        assert "rate" in result.fields

    def test_denied_too_young(self, loan_source):
        applicant = self._make_applicant(age=18)
        result, trace = run_file(loan_source, {"applicant": applicant})
        fired = {rt.rule_name for rt in trace.rule_traces if rt.fired}
        assert "age_check" not in fired
        assert "deny_decision" in fired

    def test_denied_low_income(self, loan_source):
        applicant = self._make_applicant(income=20000)
        result, trace = run_file(loan_source, {"applicant": applicant})
        fired = {rt.rule_name for rt in trace.rule_traces if rt.fired}
        assert "income_check" not in fired
        assert "deny_decision" in fired

    def test_denied_low_credit(self, loan_source):
        applicant = self._make_applicant(credit_score=500)
        result, trace = run_file(loan_source, {"applicant": applicant})
        fired = {rt.rule_name for rt in trace.rule_traces if rt.fired}
        assert "credit_check" not in fired

    def test_forward_chaining_iterations(self, loan_source):
        """Approved path should require multiple forward chaining iterations."""
        applicant = self._make_applicant()
        _, trace = run_file(loan_source, {"applicant": applicant})
        # Should have traces from multiple iterations
        assert len(trace.rule_traces) > len(set(rt.rule_name for rt in trace.rule_traces))


class TestMedicalTriage:
    def _make_patient(self, symptoms, **vital_overrides):
        vitals = {
            "heart_rate": 80,
            "blood_pressure_systolic": 120,
            "temperature": 98.6,
            "oxygen_saturation": 98,
        }
        vitals.update(vital_overrides)
        return Record(type_name=None, fields={
            "name": "Test Patient",
            "age": 40,
            "chief_complaint": symptoms[0] if symptoms else "",
            "vital_signs": Record(type_name=None, fields=vitals),
            "symptoms": symptoms,
            "medical_history": [],
        })

    def test_esi_1_cardiac_arrest(self, triage_source):
        patient = self._make_patient(["cardiac_arrest"])
        result, trace = run_file(triage_source, {"patient": patient})
        assert isinstance(result, Variant)
        assert result.variant_name == "esi_1"

    def test_esi_2_chest_pain(self, triage_source):
        patient = self._make_patient(["chest_pain"])
        result, trace = run_file(triage_source, {"patient": patient})
        assert isinstance(result, Variant)
        assert result.variant_name == "esi_2"

    def test_esi_3_fracture(self, triage_source):
        patient = self._make_patient(["fracture"])
        result, trace = run_file(triage_source, {"patient": patient})
        assert isinstance(result, Variant)
        assert result.variant_name == "esi_3"

    def test_esi_4_non_critical(self, triage_source):
        patient = self._make_patient(["headache"])
        result, trace = run_file(triage_source, {"patient": patient})
        assert isinstance(result, Variant)
        assert result.variant_name == "esi_4"

    def test_esi_5_no_symptoms(self, triage_source):
        patient = self._make_patient([])
        result, trace = run_file(triage_source, {"patient": patient})
        assert isinstance(result, Variant)
        assert result.variant_name == "esi_5"

    def test_esi_1_low_oxygen(self, triage_source):
        patient = self._make_patient(["cough"], oxygen_saturation=85)
        result, trace = run_file(triage_source, {"patient": patient})
        assert isinstance(result, Variant)
        assert result.variant_name == "esi_1"

    def test_esi_2_high_bp(self, triage_source):
        patient = self._make_patient(["headache"], blood_pressure_systolic=190)
        result, trace = run_file(triage_source, {"patient": patient})
        assert isinstance(result, Variant)
        assert result.variant_name == "esi_2"


class TestComplianceChecker:
    def _make_transaction(self, **kwargs):
        defaults = {
            "amount": 500,
            "currency": "USD",
            "country": "US",
            "counterparty": "Acme Corp",
            "type": Symbol("wire"),
            "timestamp": "2024-01-15",
        }
        defaults.update(kwargs)
        return Record(type_name=None, fields=defaults)

    def test_clear_transaction(self, compliance_source):
        txn = self._make_transaction()
        result, trace = run_file(compliance_source, {"transaction": txn})
        assert isinstance(result, Variant)
        assert result.variant_name == "clear"

    def test_sanctions_block(self, compliance_source):
        """sender_sanctions_match is accessed via space-based field access."""
        txn = self._make_transaction(sender_sanctions_match=True)
        result, trace = run_file(compliance_source, {"transaction": txn})
        fired = {rt.rule_name for rt in trace.rule_traces if rt.fired}
        assert "sanctions_block" in fired

    def test_ctr_filing(self, compliance_source):
        """CTR filing requires amount > 10000 and currency :usd on the transaction record."""
        txn = self._make_transaction(amount=15000, currency=Symbol("usd"))
        result, trace = run_file(compliance_source, {"transaction": txn})
        fired = {rt.rule_name for rt in trace.rule_traces if rt.fired}
        assert "ctr_filing" in fired

    def test_high_risk_jurisdiction(self, compliance_source):
        """recipient_jurisdiction must be a field on the transaction record."""
        txn = self._make_transaction(recipient_jurisdiction=Symbol("north_korea"))
        result, trace = run_file(compliance_source, {"transaction": txn})
        fired = {rt.rule_name for rt in trace.rule_traces if rt.fired}
        assert "high_risk_jurisdiction" in fired
