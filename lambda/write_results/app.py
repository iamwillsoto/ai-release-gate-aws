import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

import boto3


dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")


def build_release_gate_result(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds the final audit-ready release gate result.
    This object is written to S3 and partially indexed in DynamoDB.
    """

    timestamp = datetime.now(timezone.utc).isoformat()

    return {
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
        "contract": event.get("contract", {}),
    }


def write_to_dynamodb(result: Dict[str, Any]) -> None:
    table_name = os.environ["RESULTS_TABLE_NAME"]
    table = dynamodb.Table(table_name)

    table.put_item(
        Item={
            "test_id": result["test_id"],
            "execution_timestamp": result["execution_timestamp"],
            "test_name": result.get("test_name", ""),
            "category": result.get("category", ""),
            "severity": result.get("severity", ""),
            "model_id": result.get("model_id", ""),
            "evaluation_status": result.get("evaluation_status", ""),
            "release_decision": result.get("release_decision", ""),
            "failure_reasons": result.get("failure_reasons", []),
            "word_count": result.get("word_count", 0),
            "artifact_key": build_artifact_key(result),
        }
    )


def build_artifact_key(result: Dict[str, Any]) -> str:
    test_id = result.get("test_id", "unknown-test")
    timestamp = result.get("execution_timestamp", "").replace(":", "-")
    return f"release-gate-results/{test_id}/{timestamp}.json"


def write_to_s3(result: Dict[str, Any]) -> str:
    artifact_bucket = os.environ["ARTIFACT_BUCKET"]
    artifact_key = build_artifact_key(result)

    s3.put_object(
        Bucket=artifact_bucket,
        Key=artifact_key,
        Body=json.dumps(result, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    return artifact_key


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Persists AI release gate results to DynamoDB and S3.
    DynamoDB stores searchable decision metadata.
    S3 stores the full audit artifact.
    """

    result = build_release_gate_result(event)
    artifact_key = write_to_s3(result)
    write_to_dynamodb(result)

    return {
        **event,
        "result_write_status": "persisted",
        "artifact_bucket": os.environ["ARTIFACT_BUCKET"],
        "artifact_key": artifact_key,
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
        "word_count": 8,
        "contract": {}
    }

    print(json.dumps(build_release_gate_result(sample_event), indent=2))
