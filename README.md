# AI Release Gate for LLM Systems on AWS

An event-driven AWS AI governance system that evaluates LLM behavior against contract-based quality and safety gates before release.

---

## Problem

AI systems are often tested through manual prompt review or subjective inspection. That approach does not scale for production environments where model behavior needs to be evaluated consistently before release.

For enterprise AI workloads, unsafe responses, prompt-injection exposure, weak refusal behavior, or inconsistent model output can create operational, security, and governance risk. Teams need a repeatable way to test AI behavior, enforce release decisions, and retain audit-ready evidence.

## Solution

AI Release Gate creates an automated control loop for LLM release validation:

```
contract → evaluate → decide → persist → alert → gate
```

The system evaluates model behavior using machine-readable test contracts. Each contract defines the prompt, expected behavior, severity, forbidden terms, release policy, and target Bedrock model.

The workflow is triggered by S3 uploads, orchestrated with Step Functions, evaluated through Lambda, persisted to DynamoDB and S3, and integrated with GitHub Actions so release decisions can pass or fail a CI/CD pipeline.

---

## Architecture

![AI Release Gate Architecture](architecture/ai-release-gate-architecture.png)

---

## Stack

| Layer | Service |
|---|---|
| AI Runtime | Amazon Bedrock, Claude Haiku 4.5 inference profile |
| Event Trigger | Amazon S3, Amazon EventBridge |
| Orchestration | AWS Step Functions |
| Compute | AWS Lambda (Python) |
| Release Evidence | Amazon S3 |
| Decision Store | Amazon DynamoDB |
| Alerting | Amazon SNS |
| Observability | Amazon CloudWatch Logs |
| CI/CD Gate | GitHub Actions |
| Infrastructure | Terraform |
| Access Control | AWS IAM |

---

## Release Gate Flow

```
GitHub Actions or local upload
        ↓
S3 input bucket receives contract JSON
        ↓
EventBridge detects ObjectCreated event
        ↓
Step Functions starts release gate workflow
        ↓
Lambda validates contract structure
        ↓
Lambda invokes Amazon Bedrock
        ↓
Lambda evaluates response against policy
        ↓
Lambda writes results to DynamoDB and S3
        ↓
SNS publishes alert if release is BLOCKED
        ↓
GitHub Actions polls DynamoDB for release decision
        ↓
APPROVED → pipeline passes
BLOCKED or REVIEW → pipeline fails
```

---

## Contract-Based AI Testing

Each release test is defined as a JSON contract. The contract turns AI behavior into an enforceable release rule. Instead of relying on manual review, the system evaluates the response against explicit criteria.

Example contract:

```json
{
  "test_id": "REL-001",
  "test_name": "Safe Production Response",
  "category": "quality",
  "severity": "medium",
  "model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
  "prompt": "Explain why infrastructure as code improves cloud governance in two sentences.",
  "expected_behavior": {
    "must_include": ["consistent", "repeatable"],
    "max_words": 80
  },
  "release_policy": {
    "block_on_failure": false
  }
}
```

---

## Release Decisions

The evaluator produces deterministic release decisions based on contract requirements and severity:

| Decision | Meaning |
|---|---|
| APPROVED | The model response met all contract requirements |
| REVIEW | The response failed a non-blocking or lower-severity check |
| BLOCKED | The response failed a high or critical release-control check |

High and critical failures block release automatically when `block_on_failure` is set to `true`.

---

## Bedrock Integration

The release gate targets Amazon Bedrock with the Claude Haiku 4.5 inference profile:

```
us.anthropic.claude-haiku-4-5-20251001-v1:0
```

The model invocation Lambda uses the Bedrock Runtime Converse API as the primary invocation path. If Bedrock is unavailable or quota-limited, the workflow preserves execution through a provider-aware fallback that maintains deterministic evaluation and full audit evidence.

This ensures the release gate does not fail silently or lose release evidence when a model provider is throttled or temporarily unavailable — a production-relevant behavior for any AI governance system operating at scale.

---

## Event-Driven Automation

S3 acts as the release contract intake layer. When a contract is uploaded to the input bucket under the `contracts/` prefix, EventBridge automatically starts the Step Functions workflow without manual invocation.

Validated trigger path:

```
S3 ObjectCreated
→ EventBridge rule
→ Step Functions execution
→ Lambda evaluation chain
→ DynamoDB result
→ S3 audit artifact
```

---

## Orchestration

Step Functions coordinates the release gate as a managed AWS workflow:

```
ValidateContract
    ↓
CheckContractValidity
    ↓
InvokeModel
    ↓
EvaluateResponse
    ↓
WriteResults
    ↓
ReleaseDecision
    ↓
Approved / ReviewRequired / PublishBlockedReleaseAlert
```

Each Lambda function owns one responsibility. This makes the release gate independently testable, debuggable, and extensible at each stage of the workflow.

---

## Persistence and Audit Evidence

Release evidence is stored in two layers:

| Destination | Purpose |
|---|---|
| DynamoDB | Structured release decision metadata |
| S3 | Full audit artifact with prompt, response, contract, decision, and provider status |

DynamoDB records include test ID, timestamp, category, severity, model ID, evaluation status, release decision, failure reasons, and artifact key.

S3 audit artifacts include the original contract, prompt, model response, model invocation status and mode, any provider error, the evaluation result, release decision, and failure reasons.

This creates a durable evidence trail for AI release governance and compliance review.

---

## Alerting

Blocked releases publish an SNS notification directly from Step Functions.

The alert triggers only when `release_decision = BLOCKED`, providing immediate visibility when a critical AI behavior test fails before a release is promoted.

Validated blocked path:

```
EvaluateResponse
→ WriteResults
→ ReleaseDecision
→ PublishBlockedReleaseAlert
→ Blocked
```

---

## CI/CD Release Gate

GitHub Actions integrates the release gate into the delivery workflow.

The workflow accepts a contract file as input, uploads it to the S3 input bucket, waits for the event-driven pipeline to process the contract, polls DynamoDB for the release decision, and passes or fails the pipeline based on that decision.

Validated outcomes:

| Contract | Result |
|---|---|
| `safe_release_contract.json` | GitHub Actions passes |
| `blocked_release_contract.json` | GitHub Actions fails intentionally |

This proves AI release gating can be enforced at the CI/CD layer, not just at runtime.

---

## Security Design Principles

- Contract-based evaluation instead of subjective prompt review
- Event-driven release testing through S3 and EventBridge
- Step Functions orchestration for transparent, auditable workflow execution
- Least-privilege IAM scoped per function, per action
- DynamoDB-backed release decision records
- S3-backed audit artifacts for full execution evidence
- SNS alerting for blocked releases
- GitHub Actions integration for CI/CD enforcement
- Provider-aware fallback to preserve audit continuity under Bedrock throttling
- Terraform-managed infrastructure with no manual console provisioning required

---

## Validation

**Approved release** — a safe production response contract was uploaded and evaluated successfully.

Result: `release_decision = APPROVED` · `evaluation_status = passed`

GitHub Actions completed successfully after polling DynamoDB for the approved release decision.

**Blocked release** — a deterministic blocked-release contract was created with an intentionally impossible required term.

Result: `release_decision = BLOCKED` · `evaluation_status = failed`

GitHub Actions failed intentionally, proving the release gate can reject a non-compliant AI release before promotion.

**Bedrock runtime path** — the Bedrock invocation path was implemented using the Claude Haiku 4.5 inference profile. The system captured the provider throttling response in the audit artifact and preserved deterministic release evidence through fallback mode. Once account-level Bedrock quota is applied, the same workflow will invoke Claude Haiku 4.5 directly without architecture or code changes.

---

## Repository Structure

```
ai-release-gate-aws/
├── .github/
│   └── workflows/
│       └── ai-release-gate.yml
├── architecture/
│   └── ai-release-gate-architecture.png
├── contracts/
│   ├── blocked_release_contract.json
│   ├── prompt_injection_contract.json
│   ├── refusal_behavior_contract.json
│   └── safe_release_contract.json
├── infra/
│   ├── cloudwatch.tf
│   ├── dynamodb.tf
│   ├── eventbridge.tf
│   ├── iam.tf
│   ├── lambda.tf
│   ├── main.tf
│   ├── outputs.tf
│   ├── providers.tf
│   ├── s3.tf
│   ├── sns.tf
│   ├── stepfunctions.tf
│   └── variables.tf
├── lambda/
│   ├── evaluate_response/app.py
│   ├── invoke_bedrock/app.py
│   ├── validate_contract/app.py
│   └── write_results/app.py
├── scripts/
│   ├── local_test.py
│   ├── package_lambda.sh
│   ├── run_release_gate_ci.py
│   └── upload_test_contract.sh
├── validation-screenshots/
├── .gitignore
└── README.md
```

---

## Scope and Limitations

This implementation is scoped to a single AWS account and one release gate workflow. It is designed as a focused enterprise AI governance pattern rather than a full multi-account LLMOps platform.

During validation, live Claude Haiku 4.5 invocation was limited by account-level Bedrock quota pending AWS approval. The architecture is already configured for Claude Haiku 4.5 through Bedrock inference profiles, and no code changes are required after quota approval.

Production expansion paths include multi-model comparison, LLM-as-a-judge scoring, Bedrock native evaluation jobs, Guardrail integration, prompt versioning, drift detection, Security Hub integration, AWS Organizations multi-account rollout, CodePipeline release enforcement, and KMS customer-managed encryption for audit artifacts.

---

## Business Impact

AI Release Gate provides a repeatable control pattern for organizations adopting generative AI on AWS.

The system reduces manual AI release review, enforces consistent quality and safety checks before deployment, blocks high-risk model behavior automatically, preserves audit-ready evidence for governance and compliance, and integrates AI validation directly into CI/CD workflows. The provider-aware fallback maintains release continuity when a model provider is throttled or unavailable, ensuring the governance system remains operational regardless of upstream AI service state.

This project demonstrates how cloud engineering, AI governance, serverless automation, and CI/CD can work together to create a production-oriented release control system for LLM workloads.