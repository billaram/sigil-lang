---
description: Create a new sprint plan from template
---

# New Sprint

Create a new sprint planning document in `PRP/`.

## Steps

1. Ask the user for:
   - Sprint name/dates (e.g., "phase3-sprint1")
   - High-level goals (2-4 bullet points)
   - Target number of tests to add

2. Read `ai_docs/STATUS.md` to understand current state

3. Read the latest sprint plan in `PRP/` for format reference

4. Read `docs/ROADMAP.md` to understand what's next in the roadmap

5. Create `PRP/<sprint-name>.md` with this structure:
   ```markdown
   # Sprint: <name>
   > Dates: <start> — <end>
   > Phase: <phase>
   > Starting state: <current test count> tests, <what works>

   ## Goals
   - [ ] Goal 1
   - [ ] Goal 2

   ## Tasks
   ### Task 1: <name>
   **Files**: list of files to create/modify
   **Tests**: what tests to add
   **Acceptance**: how to verify it works

   ## Definition of Done
   - [ ] All goals achieved
   - [ ] All tests pass
   - [ ] ruff + mypy clean
   - [ ] STATUS.md updated
   - [ ] Examples added/updated
   ```

6. Show the created plan for review
