# Temperature Monitor

A temperature monitoring system with multiple rules at different priority levels.

**Source:** `examples/basics/temperature.sigil`

---

## What we're building

A system that classifies sensor readings into emergency, alert, warning, or normal — using prioritized rules and record types.

---

## Full source

```sigil
module examples.temperature

type SensorReading is record: -- (1)!
  sensor_id: Text
  temperature: Number
  status: Symbol

define SAFE_THRESHOLD as 100 -- (2)!
define WARNING_THRESHOLD as 80
define CRITICAL_THRESHOLD as 150

rule emergency_shutdown with priority 100: -- (3)!
  when reading temperature exceeds CRITICAL_THRESHOLD
  then shutdown_system
  explain "Temperature {reading.temperature} exceeds critical threshold of {CRITICAL_THRESHOLD}"

rule temperature_alert with priority 10: -- (4)!
  when reading temperature exceeds SAFE_THRESHOLD
  and reading status is :active -- (5)!
  then trigger alert with severity :high
  explain "Temperature {reading.temperature} exceeded safe threshold on sensor {reading.sensor_id}"

rule temperature_warning with priority 5:
  when reading temperature is between WARNING_THRESHOLD and SAFE_THRESHOLD -- (6)!
  and reading status is :active
  then trigger alert with severity :medium
  explain "Temperature {reading.temperature} approaching safe threshold"

rule normal_operation with priority 1:
  when reading temperature is below WARNING_THRESHOLD
  then log status :normal
  explain "Temperature {reading.temperature} within normal range"
```

1. **Record type** — `SensorReading` defines the shape of input data with typed fields.
2. **Named constants** — thresholds are defined once and referenced by name, not magic numbers.
3. **Priority 100** — emergency rules fire first. Higher priority = fires earlier during forward chaining.
4. **Priority 10** — alert rules fire after emergency rules.
5. **Symbol comparison** — `:active` is a Symbol literal. `reading status is :active` checks equality.
6. **Range check** — `is between X and Y` checks that a value falls within an inclusive range.

---

## Running it

```bash
sigil run examples/basics/temperature.sigil \
  --input '{"reading": {"sensor_id": "S1", "temperature": 120, "status": ":active"}}'
```

Try different temperatures to trigger different rules:

| Temperature | Rule that fires |
|-------------|----------------|
| 160 | `emergency_shutdown` (priority 100) |
| 120 | `temperature_alert` (priority 10) |
| 90 | `temperature_warning` (priority 5) |
| 50 | `normal_operation` (priority 1) |

---

## Key concepts

- **Record types** define structured data with named, typed fields
- **Rule priorities** control which rules fire first during forward chaining
- **`is between`** provides natural-language range checks
- **Symbols** (`:active`, `:high`) are lightweight labels compared by identity
- **String interpolation** in `explain` clauses (`{reading.temperature}`)
- **Space-based field access** — `reading temperature` is equivalent to `reading.temperature`
