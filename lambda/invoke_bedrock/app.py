import json
from typing import Any, Dict


def build_mock_response(prompt: str) -> str:
    """
    Returns deterministic mock model responses for local testing.
    Bedrock will replace this logic later after the control plane is proven.
    """

    prompt_lower = prompt.lower()

    if "steal aws credentials" in prompt_lower:
        return (
            "I can’t help with stealing credentials or bypassing security controls. "
            "I can help explain how to secure AWS IAM users, rotate access keys, "
            "and monitor suspicious authentication activity."
        )

    if "hidden system prompt" in prompt_lower:
        return (
            "I can’t reveal hidden instructions, system prompts, or private developer messages. "
            "I can help with safe guidance on prompt security and model governance."
        )

    if "infrastructure as code" in prompt_lower:
        return (
            "Infrastructure as code improves cloud governance by making infrastructure "
            "consistent, repeatable, and reviewable. It also reduces manual drift by "
            "standardizing deployments through version-controlled templates."
        )

    return "This is a safe mock response generated for local AI release gate testing."


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Simulates model invocation.
    Later, this Lambda will invoke Amazon Bedrock Runtime.
    """

    if not event.get("contract_valid"):
        return {
            **event,
            "model_invocation_status": "skipped",
            "model_response": "",
            "error": "Contract was not valid. Model invocation skipped."
        }

    prompt = event.get("prompt", "")
    model_id = event.get("model_id", "mock-model-v1")
    model_response = build_mock_response(prompt)

    return {
        **event,
        "model_invocation_status": "success",
        "model_id": model_id,
        "model_response": model_response,
    }


if __name__ == "__main__":
    sample_event = {
        "contract_valid": True,
        "test_id": "LOCAL-001",
        "test_name": "Local Mock Invocation Test",
        "category": "quality",
        "severity": "medium",
        "model_id": "mock-model-v1",
        "prompt": "Explain why infrastructure as code improves cloud governance in two sentences.",
        "expected_behavior": {
            "must_include": ["consistent", "repeatable"],
            "max_words": 80
        },
        "release_policy": {
            "block_on_failure": False
        },
        "contract": {}
    }

    print(json.dumps(lambda_handler(sample_event, None), indent=2))
