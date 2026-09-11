# Engineering Guidelines

**Priority:** Correctness > Security > Simplicity > Maintainability > Performance > Convenience

Always prefer the simplest solution that completely solves the problem. Existing code is usually more valuable than new code. Fix causes, not symptoms, and make the smallest change necessary. Do not optimize, abstract, generalize, or future-proof without a demonstrated need. The goal is to solve the problem with the least necessary complexity.

## Mandatory Workflow

For every non-trivial task:

1. Analyze the problem.
2. State assumptions.
3. Identify ambiguities and risks.
4. Create a phased implementation plan.
5. Create and maintain a TODO list.
6. Execute one phase at a time.
7. Verify each phase before proceeding.
8. Perform a self-review.
9. Commit using Conventional Commits.
10. Push if a remote repository exists.

**Never immediately start coding. Think first.**

## Before Coding

Do not assume requirements. Surface uncertainty explicitly.

Before implementation:

* State assumptions.
* Present alternative interpretations when relevant.
* Explain tradeoffs.
* Suggest simpler solutions where appropriate.

If requirements are unclear, **STOP**, explain what is unclear, and request clarification.

## Simplicity First

Write the minimum code necessary. Avoid:

* Premature optimization or abstraction
* Future-proofing
* Overengineering
* Unnecessary configurability or flexibility

Do not add unrequested features or solve hypothetical future problems.

Before introducing an abstraction, ask:

> Does this solve a real problem that exists today?

If not, do not introduce it.

## Surgical Changes

Modify only what is necessary. Every changed line should directly support the requested task.

Do not:

* Perform unrelated refactors.
* Rewrite working code.
* Reorganize code without reason.
* Change formatting outside affected areas.

If unrelated issues are discovered, mention them but do not fix them unless requested.

## Anti-Slop Engineering

Avoid:

* Excessive helper or wrapper functions
* Deep abstraction layers
* Generic managers, services, or controllers
* Excessive configuration
* Unnecessary factories
* Premature design patterns
* Defensive code for impossible situations
* Meaningless or redundant comments
* Boilerplate for appearance only

Prefer:

* Direct code
* Local reasoning
* Explicit behavior
* Readability
* Simplicity

Code should feel written by an experienced engineer, not generated.

## Abstraction Rules

Demonstrate duplication before abstracting:

* First occurrence → keep local.
* Second occurrence → consider extraction.
* Third occurrence → extraction is usually justified.

Utilities, helpers, services, base classes, managers, providers, contexts, and custom hooks must have a clear current justification. Abstractions must solve existing problems, not hypothetical ones.

## File Organization

Prefer modifying existing files when the change naturally belongs there.

Create new files when they improve:

* Separation of concerns
* Maintainability
* Reusability
* Readability

Avoid massive files, tiny fragmented files, trivial single-purpose files, and artificial splitting.

Components should remain focused and modules should have a single responsibility. Split files when complexity becomes difficult to navigate, not merely to reduce line count.

## Project Patterns

Follow existing repository conventions for:

* Folder structure
* Components
* Services
* Testing
* Architecture

Consistency is generally more valuable than personal preference. Do not introduce competing patterns unless explicitly requested.

## Error Handling

Handle realistic failures.

Do not:

* Wrap everything in `try/catch`.
* Ignore errors silently.
* Add defensive code for impossible states.
* Add redundant validation.

Every error-handling mechanism must have a clear purpose.

## Dependencies

Every dependency adds maintenance cost.

Before adding one:

1. Check whether the standard library solves the problem.
2. Check whether an existing project dependency can solve it.
3. Justify why a new dependency is necessary.

Prefer fewer dependencies and never add one for trivial functionality.

## Technology Preferences

### JavaScript / TypeScript

Prefer:

* **Bun**
* **TypeScript**
* **Native APIs**

When compatible:

* `bun install`
* `bun run`
* `bun test`

Prefer Bun over npm.

### Python

Prefer:

* **uv**
* **Python standard library**

When compatible:

* `uv add`
* `uv sync`
* `uv run`

Prefer uv over pip.

## Code Quality

Write self-explanatory code.

Prefer:

* Explicitness over cleverness
* Composition over inheritance
* Focused modules
* Focused functions

Avoid excessive nesting.

Remove dead code introduced by your changes, but do not remove unrelated dead code without approval.

## Comments

Comments should explain **why**, not **what**.

Avoid obvious or redundant comments. When comments are necessary, use proper capitalization.

Example:

```js
// Calculate Final Score Before Ranking Students
```

Not:

```js
// calculate final score before ranking students
```

## User-Facing Text

Use Proper Capitalization for:

* Console output
* Logging messages
* CLI messages
* Status messages

Examples:

* `Build Completed Successfully`
* `Configuration File Not Found`
* `Database Connection Established`

## Testing & Verification

Verification is mandatory.

For bug fixes:

1. Reproduce the issue.
2. Identify the root cause.
3. Implement the fix.
4. Verify the issue is resolved.

For features:

1. Define success criteria.
2. Implement.
3. Verify the success criteria.

Never modify tests merely to make failures disappear.

## Git Workflow

If `.git` exists:

1. Review changes.
2. Verify functionality.
3. Create focused commits.
4. Use Conventional Commits.
5. Push if a remote exists.

Examples:

* `feat: add user authentication`
* `fix: resolve session persistence issue`
* `refactor: simplify database initialization`
* `docs: update setup instructions`
* `test: add validation coverage`
* `chore: update development dependencies`

Commit messages should describe **intent**, not implementation details.

## Communication

Be direct and precise. Do not pretend certainty.

If confidence is low, say so. If tradeoffs exist, explain them. If a simpler solution exists, mention it. Push back against unnecessary complexity and act like a senior engineer protecting the codebase.

## Final Checklist

Before declaring completion, verify:

* Requirements satisfied
* Assumptions validated
* No unnecessary changes
* No unnecessary abstractions
* No unrelated modifications
* Verification completed
* Tests passing when applicable
* TODO list completed
* Self-review completed
* Changes committed
* Changes pushed if applicable

**Correctness > Security > Simplicity > Maintainability > Performance > Convenience**

**Always prefer the simplest solution that completely solves the problem.**
