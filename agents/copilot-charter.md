# Copilot Charter

Purpose
- Define how we use GitHub Copilot (Chat, inline, PR suggestions) to increase velocity while maintaining code quality, security, and compliance.
- Clarify roles, responsibilities, guardrails, and workflows.

Scope
- Applies to this repository and any branches under this repo.
- Complements repository-specific behavior in agents/copilot.md (operational guidance) and does not replace code review, security review, or tests.

Principles
- Human-in-the-loop: every AI-generated change is reviewed by a responsible engineer.
- Least surprise: follow established patterns and conventions already in the codebase.
- Safety first: never introduce secrets, unsafe patterns, or license risks.
- Traceable and reversible: small, focused PRs with clear commit messages and rollbacks.

Roles and Responsibilities
- Authors: use Copilot to draft code, tests, docs; verify correctness; ensure style compliance; document assumptions and risks.
- Reviewers: verify intent, correctness, security, performance, and licensing; request tests; reject unclear AI output.
- Maintainers: ensure the charter and instructions are up to date; monitor metrics; enforce guardrails.

Allowed Use Cases
- Boilerplate, adapters, refactors, unit/integration test scaffolding.
- Docs, comments, READMEs, changelogs.
- Small fixes, code suggestions, migration helpers aligned with existing stack.

Disallowed Use Cases
- Submitting unreviewed AI code.
- Introducing or modifying cryptography, auth, or security-critical logic without explicit maintainer approval.
- Generating or pasting secrets, credentials, or proprietary third-party code.
- Copying large snippets from external sources without verifying license compatibility.

Privacy and Security
- Never input secrets, personal data, or regulated data into prompts.
- Sanitize logs and error messages; avoid printing sensitive info.
- Treat Copilot output as untrusted until reviewed; validate inputs and handle errors explicitly.
- If a potential data leak occurs, follow the Incident Response section.

Intellectual Property and Licensing
- Prefer standard library and existing dependencies over adding new ones.
- Verify license compatibility for any new third-party code; document and attribute where required.
- Avoid verbatim inclusion from unknown sources; rewrite and adapt to our patterns.

Workflow with Copilot
1) Plan
   - Write a short plan and acceptance criteria.
   - Prefer small, single-purpose PRs.

2) Generate
   - Use Copilot Chat to draft code/tests/docs.
   - Ask for explanations and alternatives; choose the minimal, clear solution.

3) Validate Locally
   - Build and test locally; run linters/formatters.
   - Add/update tests for behavioral changes.

4) Open PR
   - Use Conventional Commits; provide summary, rationale, test plan, risks, rollout/backout.
   - Include any assumptions and limitations of the AI-generated code.

5) Review
   - At least one human review; two for security-sensitive areas.
   - Block if output is unclear, lacks tests, or deviates from patterns.

6) Merge and Monitor
   - Prefer squash merges; monitor for regressions; be ready to rollback quickly.

Merge Conflict Resolution Policy
- Default: merge main into the topic branch, resolve, push.
- If linear history is required: rebase onto main; push with --force-with-lease only.
- Keep conflict resolutions minimal; prefer existing patterns; ensure tests pass post-resolution.

Prompt Hygiene
- Provide concrete context: files, functions, inputs, outputs, constraints.
- Ask for complete file diffs when large changes are proposed.
- Call out unknowns; ask for safe defaults; request test plans and risks.

Quality Gates (must pass)
- Build and tests green locally and in CI.
- Lint/format clean; imports and headers consistent.
- Backward compatible unless explicitly approved; migrations documented.
- Security implications considered; secrets handling verified.

Testing Expectations
- Cover new behavior with targeted tests.
- Keep tests deterministic and fast; minimal fixtures/mocks.
- Include reproduction steps for bug fixes; add regression tests.

Performance Considerations
- Maintain or improve asymptotic complexity in hot paths.
- Avoid unnecessary allocations and I/O; measure before heavy changes.

Governance and Versioning
- This document is owned by the maintainers; propose changes via PR titled "docs: update Copilot Charter".
- Keep agents/copilot.md aligned with this charter (operational details live there).
- CODEOWNERS should include this file to require maintainer review for changes.

Incident Response
- If a suspected leak, license issue, or harmful suggestion is merged:
  - Immediately revert the change.
  - Rotate secrets if applicable.
  - Open a post-incident PR documenting impact, root cause, and prevention steps.

Telemetry and Metrics (lightweight)
- Track: PR lead time, review cycles, defect rate post-merge, test coverage deltas.
- Use trends to refine prompts, instructions, and patterns; do not track individuals.

Onboarding Checklist
- Read this charter and agents/copilot.md.
- Set up local tooling (formatter, linter, tests).
- Review recent PRs to learn patterns.
- Do a first “low-risk” PR using Copilot with a maintainer shadow.

References
- GitHub Copilot policies and docs: https://docs.github.com/copilot
- Repository instructions: agents/copilot.md

Acknowledgement
- By contributing, you agree to follow this charter and the repository instructions.