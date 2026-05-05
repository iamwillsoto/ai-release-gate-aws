import json
from typing import Any, Dict
from urllib.parse import unquote_plus

import boto3


s3 = boto3.client("s3")


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


def load_contract_from_s3_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Loads a contract JSON file from an EventBridge S3 ObjectCreated event.
    """

    detail = event.get("detail", {})
    bucket_name = detail.get("bucket", {}).get("name")
    object_key = detail.get("object", {}).get("key")

    if not bucket_name or not object_key:
        raise ValueError("S3 event did not include bucket name and object key.")

    object_key = unquote_plus(object_key)

    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    contract_body = response["Body"].read().decode("utf-8")

    contract = json.loads(contract_body)

    contract["_source"] = {
        "input_type": "s3_event",
        "bucket": bucket_name,
        "key": object_key
    }

    return contract


def resolve_contract(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolves the contract from supported input formats:
    1. {"contract": {...}}
    2. Direct contract JSON
    3. EventBridge S3 ObjectCreated event
    """

    if "contract" in event and isinstance(event["contract"], dict):
        return event["contract"]

    if "detail" in event and "bucket" in event.get("detail", {}):
        return load_contract_from_s3_event(event)

    return event


def validate_contract(contract: Dict[str, Any]) -> Dict[str, Any]:
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
        "contract_source": contract.get("_source", {"input_type": "direct"}),
        "contract": contract,
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Validates that an AI release gate contract contains the required structure.
    Supports direct contract input and S3 ObjectCreated EventBridge input.
    """

    try:
        contract = resolve_contract(event)
        return validate_contract(contract)

    except Exception as exc:
        return {
            "contract_valid": False,
            "error": "Contract resolution failed",
            "message": str(exc),
            "raw_event": event,
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
