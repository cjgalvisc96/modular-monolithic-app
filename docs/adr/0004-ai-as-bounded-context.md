# ADR-0004: AI as its own bounded context behind a port

## Status

Accepted

## Context

The product needs AI features — for example, generating task suggestions from a user's existing
tasks — backed by Amazon Bedrock. The tempting shortcut is to add a Bedrock call directly inside the
`tasks` context, since that is where the feature is surfaced.

Doing so would drag LLM and AWS/`boto3` concerns into `tasks`: its domain and application layers
would gain an awareness of Bedrock, its tests would need to mock AWS, and swapping the model or
provider would mean editing core task code. It would also blur the responsibility of `tasks`, whose
job is the TODO domain, not LLM orchestration.

## Decision

Model **AI as its own bounded context** (`ai`), a peer to `users` and `tasks`:

- **Domain** defines an `LlmClient` **port** (interface) at `ai/domain/ports/llm_client.py`, with no
  awareness that Bedrock or AWS is the implementation. `AiSuggestion` models the AI interaction.
- **Application** holds use cases (e.g. `GenerateTaskSuggestionCommand`) that call the port.
- **Infrastructure** holds a single Bedrock adapter (`ai/infrastructure/bedrock/bedrock_client.py`,
  via `boto3`) implementing the port, scoped to `BEDROCK_MODEL_ID`.
- When a use case needs task context, the `ai` context receives a **read-only** dependency on
  `tasks`, wired explicitly at the root `ApplicationContainer` — the same pattern as `tasks → users`.

## Consequences

- **Positive — `tasks` and `users` stay clean.** No LLM or AWS concern leaks into them; the AWS
  dependency lives in exactly one adapter (Dependency Inversion, single responsibility).
- **Positive — swappable and testable.** Bedrock can be swapped or mocked behind the port; unit and
  integration tiers use a fake `LlmClient` with no live Bedrock calls.
- **Positive — independent IAM and scaling.** The `ai` workload runs as its own pod with a
  dedicated IRSA role scoped to `bedrock:InvokeModel` (see
  [ADR-0006](0006-least-privilege-iam-irsa.md)).
- **Negative — more structure.** AI is a full context (domain/application/infrastructure/container)
  rather than a function call, which is more scaffolding for a small feature — accepted because it
  contains the AWS blast radius and keeps the other contexts pure.
- **Open question.** Whether suggestions are persisted (adding a tenant-isolated `AiSuggestionModel`
  + RLS policy) or ephemeral, and whether generation runs inline or via background dispatch, are
  tracked as open questions in the root planning docs (`copier-plan.md`).
