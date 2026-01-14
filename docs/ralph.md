 /ralph-loop:ralph-loop PROMPT"
# 1. Setup & Criteria

**Feature Context**:
*   **Target Feature**: `005-upload-media-processing` Microservice for gallery
*   **Branch**: `git checkout 005-upload-media-processing`
*   **Note**: Use appropriate skills and claude agents where necessary.
*   **Context**: Context7 MCP

**Core Directives**:
*   Implement all pending tasks; update existing code instead of duplicating.
*   **Production Grade**: No MVPs. Elegant, simple, logical code.
*   **Environment**: Use `.env` values (do not delete).

**Completion Criteria (Definition of Done)**:
The workflow is complete ONLY when:
*   [ ] All spec requirements are met.
*   [ ] Test coverage > 90% (npm test).
*   [ ] Linting passes (npm run lint).
*   [ ] No issues reported by any Persona for 2 full cycles.
*   [ ] Output: `<promise>FEATURE_READY</promise>`

---

## 2. Incremental Execution Phases

### Phase 1: Discovery & Planning
**Goal**: Define the work and phases.
*   Read `specs/005-upload-media-processing/tasks.md.
*   Identify constraints and unchecked tasks.
*   **Plan**: Break task into clear phases if complex (e.g., Logic -> UI -> Refinement).

### Phase 2: Codebase Exploration
**Goal**: Contextual mastery.
*   Launch `code-explorer` agents to map architecture and existing patterns.
*   Identify key files to avoid duplication.
*   **Result**: Comprehensive summary of findings.

### Phase 3: The Ralph Loop (Self-Correcting)
*Run repeatedly until Completion Criteria are met.*

**Iteration Logic**:
1.  Identify Persona via `iteration % 7`.
2.  Execute Persona Task.
3.  **Self-Correction**: If a check fails, FIX IT IMMEDIATELY. Do not queue it.
4.  Commit: `[persona] description`.

#### Persons & Responsibilities

**[0] ARCHITECT (Strategy)**
*   **Task**: Design implementation approaches (Minimal, Clean, Pragmatic).
*   **Action**: Select the best approach for long-term maintainability.

**[1] CODE REVIEWER (Quality)**
*   **Task**: Enforce Simplicity, DRY, and Security.
*   **Self-Correction**: If code is complex or buggy, **refactor immediately**.
*   **Constraint**: Fix everything finding now; do not defer.

**[2] SYSTEM ARCHITECT (Structure)**
*   **Task**: Check file structure, separation of concerns, and dependencies.
*   **Action**: Refactor for structural integrity.

**[3] FRONTEND DESIGNER (UX/UI)**
*   **Task**: Polish aesthetics and responsiveness.
*   **Tools**: Use `/frontend-design` agent.
*   **Action**:Ensure UI is "wow" quality and accessible.

**[4] QA ENGINEER (Reliability)**
*   **Task**: Validation & TDD.
*   **Action**:
    1.  Run `npm test`.
    2.  **Self-Correction**: If tests fail, debug and fix loop until GREEN.
    3.  Run `npm run lint` && docker build .
    4.  Write missing tests for edge cases.

**[5] PROJECT MANAGER (Verification)**
*   **Task**: Verify acceptance criteria against `specs/005-upload-media-processing/spec.md`.
*   **Action**: Document implementation gaps and trigger fixes.

**[6] BUSINESS ANALYST (User Flow)**
*   **Task**: Validate user perspective.
*   **Action**: Identify and smooth out UX friction points.

---

## 3. Escape Hatches & Safety

**Stuck Protocol**:
If the workflow reaches 50 iterations without completion:
1.  **Stop** execution.
2.  Document exactly what is blocking progress.
3.  List attempts made.
4.  Suggest alternative approaches.

**Output Rule**:
DO NOT output `<promise>FEATURE_READY</promise>` unless **all** Completion Criteria are checked and verified. " [--max-iterations 50] [--completion-promise Done]   