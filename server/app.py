from pathlib import Path
from datetime import datetime
from typing import List, Literal
import random
import uvicorn

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_FILE = BASE_DIR / "index.html"

for folder_name in ["assets", "static"]:
    folder_path = BASE_DIR / folder_name
    if folder_path.exists() and folder_path.is_dir():
        app.mount(f"/{folder_name}", StaticFiles(directory=str(folder_path)), name=folder_name)


class TransactionState(BaseModel):
    transaction_id: str
    amount: float
    credit_score: int
    available_credit: float
    monthly_spend: float
    debt_to_income: float
    payment_history: float
    credit_utilization: float
    last_payment_date: str
    account_age_months: int


class StepRequest(BaseModel):
    action: Literal[
        "approve_card_1",
        "approve_card_2",
        "route_to_debit",
        "convert_to_emi",
        "delay_purchase",
        "decline",
    ]


class PolicyCheck(BaseModel):
    name: str
    passed: bool
    detail: str


class AuditItem(BaseModel):
    timestamp: str
    transaction_id: str
    action: str
    reward: float
    risk_band: str
    recommended_action: str


CURRENT_STATE = {
    "transaction_id": "TXN-20260408-001",
    "amount": 18499.00,
    "credit_score": 712,
    "available_credit": 65000.00,
    "monthly_spend": 38200.00,
    "debt_to_income": 31,
    "payment_history": 94,
    "credit_utilization": 42,
    "last_payment_date": "2026-04-02",
    "account_age_months": 26,
}

AUDIT_LOG: List[dict] = []


def get_risk_band(state: dict) -> str:
    if state["credit_score"] >= 750 and state["debt_to_income"] <= 25 and state["credit_utilization"] <= 35:
        return "low"
    if state["credit_score"] >= 680 and state["debt_to_income"] <= 40 and state["credit_utilization"] <= 55:
        return "medium"
    return "high"


def evaluate_action(action: str, state: dict):
    risk_band = get_risk_band(state)

    rewards = {
        "approve_card_1": 0.91 if risk_band == "low" else 0.62 if risk_band == "medium" else 0.18,
        "approve_card_2": 0.88 if risk_band == "low" else 0.66 if risk_band == "medium" else 0.22,
        "route_to_debit": 0.52 if risk_band == "low" else 0.74 if risk_band == "medium" else 0.79,
        "convert_to_emi": 0.64 if risk_band == "low" else 0.83 if risk_band == "medium" else 0.71,
        "delay_purchase": 0.20 if risk_band == "low" else 0.49 if risk_band == "medium" else 0.76,
        "decline": 0.05 if risk_band == "low" else 0.28 if risk_band == "medium" else 0.81,
    }

    reasons_map = {
        "approve_card_1": [
            "Primary card gives the fastest checkout experience.",
            "Risk is acceptable for this transaction profile.",
            "Credit utilization remains manageable after approval.",
        ],
        "approve_card_2": [
            "Fallback card is viable with similar approval behavior.",
            "Useful when the user prefers a second credit line.",
            "Slightly different reward profile than card 1.",
        ],
        "route_to_debit": [
            "Reduces lender exposure by avoiding additional credit usage.",
            "Helpful when utilization or debt pressure is rising.",
            "Good balance between approval and risk control.",
        ],
        "convert_to_emi": [
            "Can reduce immediate repayment pressure for the customer.",
            "Useful for medium-risk cases with moderate affordability concerns.",
            "Improves affordability for larger transaction values.",
        ],
        "delay_purchase": [
            "Allows more time before taking on additional obligation.",
            "May be safer when current profile shows stress signals.",
            "Useful when approval is possible but not ideal today.",
        ],
        "decline": [
            "Strongest risk-control option for weak credit scenarios.",
            "Avoids new exposure when signals are unfavorable.",
            "Best used only when safer options score poorly.",
        ],
    }

    policy_checks = [
        {
            "name": "Credit score threshold",
            "passed": state["credit_score"] >= 650,
            "detail": f"Credit score is {state['credit_score']} (minimum expected 650).",
        },
        {
            "name": "Debt-to-income policy",
            "passed": state["debt_to_income"] <= 40,
            "detail": f"Debt-to-income is {state['debt_to_income']}% (policy limit 40%).",
        },
        {
            "name": "Credit utilization policy",
            "passed": state["credit_utilization"] <= 60,
            "detail": f"Utilization is {state['credit_utilization']}% (policy limit 60%).",
        },
    ]

    leaderboard = [{"action": k, "reward": v} for k, v in sorted(rewards.items(), key=lambda x: x[1], reverse=True)]
    recommended_action = leaderboard[0]["action"]

    result = {
        "state": state,
        "action": action,
        "reward": rewards[action],
        "risk_band": risk_band,
        "recommended_action": recommended_action,
        "reasons": reasons_map[action],
        "leaderboard": leaderboard,
        "policy_checks": policy_checks,
    }

    AUDIT_LOG.append(
        {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "transaction_id": state["transaction_id"],
            "action": action,
            "reward": rewards[action],
            "risk_band": risk_band,
            "recommended_action": recommended_action,
        }
    )

    return result


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/health")
def api_health():
    return {"status": "ok"}


@app.get("/state", response_model=TransactionState)
def get_state():
    return CURRENT_STATE


@app.post("/reset", response_model=TransactionState)
def reset_environment():
    AUDIT_LOG.clear()
    today = datetime.now().strftime("%Y-%m-%d")
    return {
        "transaction_id": f"TXN-{datetime.now().strftime('%Y%m%d')}-{random.randint(1, 999):03d}",
        "amount": round(random.uniform(5000, 50000), 2),
        "credit_score": random.randint(580, 850),
        "available_credit": round(random.uniform(30000, 100000), 2),
        "monthly_spend": round(random.uniform(20000, 60000), 2),
        "debt_to_income": random.randint(15, 55),
        "payment_history": random.randint(75, 100),
        "credit_utilization": random.randint(20, 70),
        "last_payment_date": today,
        "account_age_months": random.randint(12, 84),
    }

@app.post("/step")
def step_environment(payload: StepRequest):
    return evaluate_action(payload.action, CURRENT_STATE)


@app.get("/audit-log", response_model=List[AuditItem])
def get_audit_log():
    return AUDIT_LOG


@app.get("/")
def root():
    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE), media_type="text/html")
    return JSONResponse(
        {"message": "index.html not found in project root"},
        status_code=404,
    )


def main():
    # This is the entry point for the OpenEnv validator
    print("Environment Server is ready.")
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
