---
name: code-review
description: Review code changes for architecture, tests, types and project conventions. Use before merging or after non-trivial implementation.
---

# Code Review Skill

## Assumptions / Verify first

Before following examples below, verify the expected project paths exist in the current repository:

```bash
rg --files | head -n 50
for p in app tests alembic; do
  if [ -d "$p" ]; then
    echo "OK: $p/"
  else
    echo "MISSING: $p/ (examples below may be pseudocode)"
  fi
done
```

If those directories are missing, treat path-based examples as **pseudocode** and adapt commands to real repo paths.

## Purpose

Ensure code quality, architectural compliance, type safety, and maintainability before merging changes.

## Workflow

### Phase 1: Explore

1. Read the diff/changed files.
2. Understand the feature or fix being implemented.
3. Check related tests.
4. Verify type annotations are present.

### Phase 2: Review Checklist

#### Architecture Compliance

- [ ] No direct DB access from controllers/endpoints.
- [ ] Business logic is in services, not endpoints.
- [ ] Repository pattern is used for data access.
- [ ] No circular imports between layers.
- [ ] Dependencies point inward (domain ← application ← infrastructure).

#### Type Safety

- [ ] All function parameters have type hints.
- [ ] All return types are annotated.
- [ ] Pydantic models are used for validation.
- [ ] No `Any` types without justification.
- [ ] Union types are specific, not overly broad.

#### Testing

- [ ] New functionality has tests.
- [ ] Edge cases are covered.
- [ ] Error conditions are tested.
- [ ] Tests follow AAA pattern (Arrange-Act-Assert).
- [ ] No test interdependencies.

#### Code Quality

- [ ] Functions are small (<50 lines ideally).
- [ ] Single Responsibility Principle followed.
- [ ] DRY: no unnecessary duplication.
- [ ] Variable names are descriptive.
- [ ] No magic numbers (use constants).

#### Comments

- [ ] Comments explain "why", not "what".
- [ ] Workarounds are documented.
- [ ] TODO comments have issue references.
- [ ] No commented-out code.

#### Security

- [ ] User input is validated (Pydantic).
- [ ] SQL injection prevented (ORM usage).
- [ ] No secrets in code.
- [ ] Error messages don't leak sensitive info.

#### Performance

- [ ] N+1 queries avoided.
- [ ] Database indexes considered.
- [ ] Async I/O used where appropriate.
- [ ] No unnecessary synchronous blocking.

### Phase 3: Provide Feedback

Structure feedback as:

```markdown
## Critical Issues (must fix)

1. **Architecture violation**: Endpoint directly accesses database.
   - Location: `app/api/endpoints/bookings.py:45`
   - Fix: Move logic to `BookingService`.

2. **Missing type annotations**: Function `process_booking` lacks return type.
   - Location: `app/services/booking_service.py:23`
   - Fix: Add `-> BookingResponse`.

## Suggestions (should fix)

1. Consider extracting validation logic into separate function.
2. Add test for edge case: booking at slot boundary.

## Nitpicks (optional)

1. Variable name `data` could be more descriptive.
```

### Phase 4: Verify Fixes

After author addresses feedback:

1. Re-review changed files.
2. Ensure no new issues introduced.
3. Confirm tests still pass.
4. Approve when all critical issues resolved.

## What NOT to Do

- ❌ Do NOT nitpick on style if linter passes.
- ❌ Do NOT request changes without explaining why.
- ❌ Do NOT approve code you don't understand.
- ❌ Do NOT ignore architecture violations.
- ❌ Do NOT skip review for "small" changes.

## Review Templates

### Positive Review

```markdown
✅ Approved

The implementation follows our architecture patterns:
- Clean separation between endpoint and service layer.
- Comprehensive test coverage.
- Proper type annotations throughout.

Minor suggestion: consider adding docstring to `calculate_availability`.
```

### Request Changes Review

```markdown
❌ Changes Requested

**Critical:**
1. Direct repository usage in endpoint violates architecture.
2. Missing error handling for database failures.

**Before re-submitting:**
- Move data access to service layer.
- Add try/except with proper error responses.
- Add tests for error scenarios.
```

## Reference Files

- `/docs/architecture-boundaries.md` — Architecture rules.
- `/AGENTS.md` — Project conventions.
- `/tests/` — Test patterns.

## Required Checks

- [ ] Architecture boundaries respected.
- [ ] Types are complete and correct.
- [ ] Tests cover main scenarios.
- [ ] No security issues.
- [ ] Code is maintainable.

## Definition of Done (DoD)

- [ ] Scope of change is implemented and matches the agreed plan for this skill task.
- [ ] Tests for new/changed behavior are added or updated (happy path, edge cases, and error conditions as applicable).
- [ ] `make test`, `make lint`, and `make typecheck` have been run, and failures are resolved or explicitly documented.
- [ ] Documentation is added/updated when behavior, API contracts, or operational workflow changed.
- [ ] Layered architecture remains valid: Endpoint → Service → Repository (no bypassing service layer).
- [ ] Type annotations and validation are present for new/changed public interfaces.
- [ ] Final diff is reviewed for unintended changes (no dead code, commented-out debug code, or unrelated edits).
