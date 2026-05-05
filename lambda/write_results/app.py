import json
from datetime import datetime, timezone
from typing import Any, Dict


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Formats the final release gate result.
    Later, this Lambda will write to DynamoDB and S3.
    """

    timestamp = datetime.now(timezone.utc).isoformat()

    result = {
        "execution_timestamp": timestamp,
        "test_id": event.get("test_id"),
        "test_name": event.get("test_name"),
        "category": event.get("category"),
        "severity": event.get("severity"),
        "model_id": event.get("model_id"),
        "evaluation_status": event.get("evaluation_status"),
        "release_decision": event.get("release_decision"),
        "failure_reasons": event.get("failure_reasons", []),
        "word_count": event.get("word_count"),
        "prompt": event.get("prompt"),
        "model_response": event.get("model_response"),
    }

    return {
        **event,
        "result_write_status": "formatted",
        "release_gate_result": result,
    }


if __name__ == "__main__":
    sample_event = {
        "test_id": "LOCAL-001",
        "test_name": "Local Result Formatting Test",
        "category": "quality",
        "severity": "medium",
        "model_id": "mock-model-v1",
        "prompt": "Explain why infrastructure as code improves governance.",
        "model_response": "Infrastructure as code makes deployments consistent and repeatable.",
        "evaluation_status": "passed",
        "release_decision": "APPROVED",
        "failure_reasons": [],
        "word_count": 8
    }

    print(json.dumps(lambda_handler(sample_event, None), indent=2))
