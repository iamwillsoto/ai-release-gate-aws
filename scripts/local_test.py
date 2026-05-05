import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_lambda_handler(relative_path):
    module_path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location("lambda_module", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.lambda_handler


validate_contract = load_lambda_handler("lambda/validate_contract/app.py")
invoke_bedrock = load_lambda_handler("lambda/invoke_bedrock/app.py")
evaluate_response = load_lambda_handler("lambda/evaluate_response/app.py")
write_results = load_lambda_handler("lambda/write_results/app.py")


def run_contract(contract_file):
    contract_path = ROOT / contract_file

    with contract_path.open("r", encoding="utf-8") as file:
        contract = json.load(file)

    event = {"contract": contract}

    validated = validate_contract(event, None)
    invoked = invoke_bedrock(validated, None)
    evaluated = evaluate_response(invoked, None)
    final_result = write_results(evaluated, None)

    print("\n" + "=" * 80)
    print(f"Contract: {contract_file}")
    print("=" * 80)
    print(json.dumps(final_result["release_gate_result"], indent=2))


if __name__ == "__main__":
    contracts = [
        "contracts/prompt_injection_contract.json",
        "contracts/refusal_behavior_contract.json",
        "contracts/safe_release_contract.json",
    ]

    for contract in contracts:
        run_contract(contract)
