import requests

BASE_URL = "https://anirudhreddy19-payment-credit-openenv.hf.space"

TASKS = ["easy", "medium", "hard"]
ACTIONS = [
    "approve_card_1",
    "approve_card_2",
    "route_to_debit",
    "convert_to_emi",
    "delay_purchase",
    "decline"
]

def normalize_check(reward):
    return 0.0 <= reward <= 1.0

for task in TASKS:
    print(f"\n===== TESTING TASK: {task.upper()} =====")

    # RESET
    reset_res = requests.post(f"{BASE_URL}/reset", json={"task_id": task})
    reset_data = reset_res.json()
    print("RESET:", reset_data)

    # Basic validation
    assert "task_id" in reset_data, "Missing task_id in reset response"

    # STEP through all actions
    for action in ACTIONS:
        step_res = requests.post(
            f"{BASE_URL}/step",
            json={"action": action}
        )
        step_data = step_res.json()

        print(f"STEP ({action}):", step_data)

        # VALIDATIONS (VERY IMPORTANT)
        assert "reward" in step_data, "Missing reward"
        assert normalize_check(step_data["reward"]), "Reward out of range [0,1]"
        assert "task_id" in step_data, "Missing task_id"
        assert step_data["task_id"] == task, "Task mismatch"
        assert "risk_band" in step_data, "Missing risk_band"
        assert "recommended_action" in step_data, "Missing recommended_action"

print("\n✅ ALL TESTS PASSED SUCCESSFULLY")
