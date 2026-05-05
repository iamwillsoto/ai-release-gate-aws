import json
from typing import Any, Dict


REQUIRED_FIELDS = [
    "test_id",
    "test_name",
    "category",
    "severity",
    "model_id",
    "prompt",
    "expected_behavior",
    "release_policy",
]

VALID_SEVERITIES = ["low", "medium", "high", "critical"]


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Validates that an AI release gate contract contains the required structure.
    This Lambda is intentionally strict because bad test definitions should fail fast.
    """

    contract = event.get("contract", event)

    missing_fields = [field for field in REQUIRED_FIELDS if field not in contract]

    if missing_fields:
        return {
            "contract_valid": False,
            "error": "Missing required contract fields",
            "missing_fields": missing_fields,
            "contract": contract,
        }

    severity = str(contract["severity"]).lower()

    if severity not in VALID_SEVERITIES:
        return {
            "contract_valid": False,
            "error": "Invalid severity value",
            "valid_severities": VALID_SEVERITIES,
            "received_severity": contract["severity"],
            "contract": contract,
        }

    if not isinstance(contract["expected_behavior"], dict):
        return {
            "contract_valid": False,
            "error": "expected_behavior must be an object",
            "contract": contract,
        }

    if not isinstance(contract["release_policy"], dict):
        return {
            "contract_valid": False,
            "error": "release_policy must be an object",
            "contract": contract,
        }

    return {
        "contract_valid": True,
        "test_id": contract["test_id"],
        "test_name": contract["test_name"],
        "category": contract["category"],
        "severity": severity,
        "model_id": contract["model_id"],
        "prompt": contract["prompt"],
        "expected_behavior": contract["expected_behavior"],
        "release_policy": contract["release_policy"],
        "contract": contract,
    }


if __name__ == "__main__":
    sample_event = {
        "contract": {
            "test_id": "LOCAL-001",
            "test_name": "Local Validation Test",
            "category": "quality",
            "severity": "medium",
            "model_id": "mock-model-v1",
            "prompt": "Explain why infrastructure as code improves governance.",
            "expected_behavior": {
                "must_include": ["consistent", "repeatable"],
                "max_words": 80
            },
            "release_policy": {
                "block_on_failure": False
            }
        }
    }

    print(json.dumps(lambda_handler(sample_event, None), indent=2))
