import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict

import boto3
from boto3.dynamodb.conditions import Key


POLL_INTERVAL_SECONDS = 5
MAX_WAIT_SECONDS = 180


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_contract(contract_path: str) -> Dict[str, Any]:
    path = Path(contract_path)

    if not path.exists():
        raise FileNotFoundError(f"Contract file not found: {contract_path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def upload_contract_to_s3(contract: Dict[str, Any], bucket_name: str, source_contract_path: str) -> str:
    s3 = boto3.client("s3")

    github_run_id = os.environ.get("GITHUB_RUN_ID", "local")
    unique_suffix = str(uuid.uuid4())[:8]

    original_test_id = contract.get("test_id", "UNKNOWN")
    ci_test_id = f"CI-{github_run_id}-{original_test_id}-{unique_suffix}"

    contract["test_id"] = ci_test_id
    contract["test_name"] = f"{contract.get('test_name', 'AI Release Gate Test')} - CI Run"

    object_key = f"contracts/ci/{ci_test_id}.json"

    s3.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=json.dumps(contract, indent=2).encode("utf-8"),
        ContentType="application/json",
        Metadata={
            "source_contract": source_contract_path,
            "github_run_id": github_run_id
        }
    )

    print(f"Uploaded CI contract to s3://{bucket_name}/{object_key}")
    print(f"CI test_id: {ci_test_id}")

    return ci_test_id


def wait_for_result(table_name: str, test_id: str) -> Dict[str, Any]:
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    deadline = time.time() + MAX_WAIT_SECONDS

    while time.time() < deadline:
        response = table.query(
            KeyConditionExpression=Key("test_id").eq(test_id),
            ScanIndexForward=False,
            Limit=1
        )

        items = response.get("Items", [])

        if items:
            return items[0]

        print(f"No DynamoDB result yet for {test_id}. Waiting {POLL_INTERVAL_SECONDS}s...")
        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError(f"No release gate result found for {test_id} after {MAX_WAIT_SECONDS} seconds.")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_release_gate_ci.py <contract_file>")
        return 2

    contract_path = sys.argv[1]

    input_bucket = require_env("INPUT_BUCKET_NAME")
    results_table = require_env("RESULTS_TABLE_NAME")

    print("AI Release Gate CI check started")
    print(f"Contract file: {contract_path}")
    print(f"Input bucket: {input_bucket}")
    print(f"Results table: {results_table}")

    contract = load_contract(contract_path)
    test_id = upload_contract_to_s3(contract, input_bucket, contract_path)

    print("Waiting for EventBridge → Step Functions → DynamoDB result...")
    result = wait_for_result(results_table, test_id)

    print("Release gate result:")
    print(json.dumps(result, indent=2, default=str))

    release_decision = result.get("release_decision")
    evaluation_status = result.get("evaluation_status")

    print(f"Final release decision: {release_decision}")
    print(f"Evaluation status: {evaluation_status}")

    if release_decision == "APPROVED":
        print("AI Release Gate passed.")
        return 0

    print("AI Release Gate failed. Release is not approved.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
