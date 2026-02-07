---
doc_id: doc_010
title: "Coding Standards & Review Guidelines"
author: Felix Braun
source_type: notion
---

# Coding Standards & Review Guidelines

**Author:** Felix Braun (Senior Developer)
**Approved by:** Sandra Hoffmann (CTO)
**Last Updated:** September 2025
**Applies to:** All TechVision development teams

## Introduction

This document defines the coding standards, Git workflow, and code review practices for all TechVision projects. Adherence to these standards is mandatory for all developers, including contractors. Deviations require an approved Architecture Decision Record (ADR) reviewed by a senior engineer.

These standards are informed by our experience across Projekt Aurora, the FinSecure Portal, and MedTech Analytics, and complement our broader technical guidelines including the API Design Guidelines (doc_012) and Database Standards (doc_015).

---

## Git Workflow

### Trunk-Based Development

We follow a trunk-based development model. The `main` branch is the single source of truth and must always be in a deployable state. Long-lived feature branches are strongly discouraged. Branches should be short-lived (ideally less than 2 days) and merged frequently.

### Branch Naming Convention

All branches must follow this naming pattern:

```
{type}/{ticket-id}-{short-description}
```

**Types:**
- `feature/` — New features or enhancements (e.g., `feature/AUR-142-add-sensor-ingestion`)
- `bugfix/` — Bug fixes (e.g., `bugfix/FIN-87-fix-auth-token-refresh`)
- `hotfix/` — Urgent production fixes (e.g., `hotfix/MED-23-fix-dashboard-crash`)
- `chore/` — Non-functional changes like dependency updates (e.g., `chore/AUR-150-update-terraform-provider`)

The ticket ID must reference a valid Jira ticket. Branches without a ticket ID will be flagged during review.

### Commit Messages

We follow the Conventional Commits specification:

```
{type}({scope}): {description}

{optional body}

{optional footer}
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`

Examples:
- `feat(ingestion): add SAP CDC connector for Aurora pipeline`
- `fix(auth): resolve JWT token refresh race condition`
- `docs(api): update OpenAPI spec for /v2/patients endpoint`

### Merge Strategy

All pull requests are merged via **squash merge** into `main`. This keeps the main branch history clean and ensures each merge commit corresponds to exactly one feature or fix. The squash commit message should summarize the entire PR, not just the last commit.

Release branches (e.g., `release/v2.3.0`) may be created for coordinated releases. These are merged back to `main` via a regular merge commit (no squash) to preserve release history.

---

## Pull Request Requirements

### Before Opening a PR

1. Ensure all tests pass locally.
2. Run the linter and formatter (see language-specific sections below).
3. Remove all `TODO` and `FIXME` comments, or convert them to Jira tickets with a reference (e.g., `# TODO(AUR-155): optimize query after index migration`).
4. Update or add relevant tests. Untested code will not be approved.
5. Update API documentation if endpoint behavior changes (see doc_012).

### PR Description Template

Every PR must include:
- **What:** A concise summary of the change.
- **Why:** The business or technical motivation.
- **How:** Key implementation details and design decisions.
- **Testing:** How the change was tested (unit, integration, manual).
- **Related:** Links to Jira tickets and related PRs.

### Approval Requirements

- **Minimum 2 approvals** required from team members.
- At least one reviewer must be a senior developer or tech lead.
- **CI must be green.** No merging with failing checks, even for "unrelated" failures.
- Security-sensitive changes (authentication, encryption, data access) require an additional review from Tobias Fischer (Security Officer).

### PR Size Guidelines

- Target fewer than 400 lines of changed code per PR (excluding auto-generated files).
- If a feature requires more, break it into stacked PRs with clear dependency ordering.
- Large refactoring PRs should be split from behavioral changes: one PR for the refactor, another for the new feature.

---

## Python Standards

Python is our primary backend language, used across Projekt Aurora, MedTech Analytics, and internal tooling.

### Version and Tooling

- **Python 3.12+** for all new projects.
- **ruff** for linting (replaces flake8, isort, and pylint). Configuration lives in `pyproject.toml`.
- **ruff format** for code formatting (compatible with Black style). No manual formatting debates.
- **mypy** in strict mode for type checking. All function signatures must have complete type annotations.

### Style Rules

- **Type hints are mandatory** for all function parameters and return types. Use `from __future__ import annotations` for forward references.
- Use `pathlib.Path` instead of `os.path` for file system operations.
- Prefer `dataclasses` or Pydantic `BaseModel` over plain dictionaries for structured data.
- Use `async/await` for I/O-bound operations. Do not mix synchronous blocking calls in async codepaths.
- Exception handling: Catch specific exceptions, never bare `except:`. Log exceptions with `logger.exception()` to preserve stack traces.
- Imports: Use absolute imports. Group as standard library, third-party, local (ruff handles ordering automatically).

### Testing

- **pytest** is the test framework. No unittest-style classes.
- Minimum 80% code coverage for new code. Use `pytest-cov` to measure.
- Use `pytest-asyncio` for async test functions.
- Fixtures should be in `conftest.py`, scoped appropriately (`function`, `module`, `session`).
- Mock external services (databases, APIs) in unit tests. Integration tests may use Testcontainers.

### Project Structure

```
backend/
  app/
    api/          # FastAPI route handlers
    models/       # SQLAlchemy models
    schemas/      # Pydantic request/response models
    services/     # Business logic
    jobs/         # Background job handlers
    processing/   # Data processing pipeline
    config.py     # Pydantic Settings
  tests/
    unit/
    integration/
  pyproject.toml  # ruff, mypy, pytest config
  requirements.txt
  requirements-dev.txt
```

---

## TypeScript Standards

TypeScript is used for all frontend applications (React) and any Node.js-based services.

### Version and Tooling

- **TypeScript 5.x** with `strict: true` in `tsconfig.json`. No exceptions.
- **ESLint** with our shared config (`@techvision/eslint-config`) for linting.
- **Prettier** for formatting (integrated with ESLint via `eslint-plugin-prettier`).
- **Vite** as the build tool for React applications.

### Style Rules

- Prefer `interface` over `type` for object shapes (interfaces are more extensible and produce better error messages).
- Use `const` by default. Use `let` only when reassignment is necessary. Never use `var`.
- Avoid `any`. If a type is truly unknown, use `unknown` and narrow it with type guards.
- Use named exports. Default exports are discouraged except for React page components.
- Prefer `async/await` over `.then()` chains.
- Error handling: Always type-narrow caught errors (`if (error instanceof SpecificError)`).

### React-Specific Rules

- Functional components only. No class components.
- Use React hooks. Custom hooks should be prefixed with `use` and placed in a `hooks/` directory.
- State management: Zustand for global state, React Query (TanStack Query) for server state. Avoid Redux in new projects.
- Component files: one component per file, named to match the component (`UserProfile.tsx` exports `UserProfile`).

### Testing

- **Vitest** for unit tests (Jest-compatible API with Vite integration).
- **React Testing Library** for component tests. Test behavior, not implementation.
- **Playwright** for end-to-end tests.
- Minimum 70% coverage for new frontend code.

---

## Code Review Checklist

Reviewers should evaluate each PR against these criteria:

### Correctness
- [ ] Does the code do what the PR description says?
- [ ] Are edge cases handled (null values, empty collections, concurrent access)?
- [ ] Are error paths handled gracefully with appropriate user-facing messages?

### Security
- [ ] No secrets or credentials in code (use environment variables or Key Vault).
- [ ] Input validation on all external data (API requests, file uploads, query parameters).
- [ ] SQL injection prevention (parameterized queries, ORM usage).
- [ ] Authentication and authorization checks on all endpoints.

### Performance
- [ ] No N+1 query patterns (use eager loading or batch queries).
- [ ] Database queries use appropriate indexes (check with `EXPLAIN ANALYZE`, see doc_015).
- [ ] No unnecessary data fetching (select only needed columns, use pagination).

### Maintainability
- [ ] Code is self-documenting. Comments explain "why", not "what".
- [ ] No dead code or commented-out blocks.
- [ ] Functions and methods are focused (single responsibility).
- [ ] No magic numbers or strings — use named constants.

### Testing
- [ ] New code has corresponding tests.
- [ ] Tests are meaningful (not just testing mocks).
- [ ] Test names describe the expected behavior (`test_expired_token_returns_401`).

---

## Enforcement

These standards are enforced through multiple mechanisms:

1. **Pre-commit hooks** — ruff, prettier, and type checking run before each commit.
2. **CI pipeline** — Linting, formatting, and tests run on every PR (see doc_013).
3. **Code review** — Reviewers verify adherence as part of the review checklist.
4. **Quarterly audits** — The Architecture Guild reviews a sample of merged PRs each quarter.

Violations found during review should be addressed before merging. Repeated violations will be discussed in 1:1s with the team lead. The goal is not punishment but continuous improvement.

Questions or suggestions for updating these standards should be raised in the `#engineering` Slack channel or discussed at the bi-weekly Engineering All-Hands.
