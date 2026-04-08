import fastapi
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import date, datetime, timedelta
import random
import uuid
    
app = fastapi.FastAPI(
    title="payment_credit_env",
    version="0.2.0",
    description="Policy-aware payment credit decision environment"
)
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    
ActionType = Literal[
    "approve_card_1",
    "approve_card_2",
    "route_to_debit",
    "convert_to_emi",
    "delay_purchase",
    "decline",
]
    
ALL_ACTIONS = [
    "approve_card_1",
    "approve_card_2",
    "route_to_debit",
    "convert_to_emi",
    "delay_purchase",
    "decline",
]
    
    
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
    action: ActionType
    
    
class LeaderboardEntry(BaseModel):
    action: str
    reward: float
    
    
class PolicyCheck(BaseModel):
    name: str
    passed: bool
    detail: str
    
    
class StepResponse(BaseModel):
    transaction_id: str
    action: str
    reward: float
    task_id: str
    done: bool = False
    state: TransactionState
    risk_band: str
    recommended_action: str
    reasons: List[str]
    leaderboard: List[LeaderboardEntry]
    policy_checks: List[PolicyCheck]
    
    
class AuditLogEntry(BaseModel):
    timestamp: str
    transaction_id: str
    action: str
    reward: float
    risk_band: str
    recommended_action: str
    
    
class EnvStore:
    def __init__(self):
        self.current_state: Optional[TransactionState] = None
        self.audit_log: List[AuditLogEntry] = []
        self.current_task: str = "easy"
    
    def reset(self):
        self.current_state = self._sample_transaction()
        self.audit_log = []
        return self.current_state
    
    def get_state(self):
        if self.current_state is None:
            self.current_state = self._sample_transaction()
        return self.current_state
    
    def _sample_transaction(self) -> TransactionState:
        credit_score = random.randint(540, 820)
        amount = round(random.uniform(1500, 90000), 2)
        available_credit = round(random.uniform(15000, 250000), 2)
        monthly_spend = round(random.uniform(8000, 90000), 2)
        debt_to_income = round(random.uniform(15, 80), 1)
        payment_history = round(random.uniform(60, 99), 1)
        credit_utilization = round(random.uniform(10, 95), 1)
        last_payment_date = (date.today() - timedelta(days=random.randint(0, 60))).isoformat()
        account_age_months = random.randint(6, 240)
    
        return TransactionState(
            transaction_id=f"TXN{random.randint(10000, 99999)}",
            amount=amount,
            credit_score=credit_score,
            available_credit=available_credit,
            monthly_spend=monthly_spend,
            debt_to_income=debt_to_income,
            payment_history=payment_history,
            credit_utilization=credit_utilization,
            last_payment_date=last_payment_date,
            account_age_months=account_age_months,
        )
    
    
env = EnvStore()
    
    
def get_risk_band(s: TransactionState) -> str:
    score = 0
    
    if s.credit_score < 600:
        score += 3
    elif s.credit_score < 680:
        score += 2
    elif s.credit_score < 740:
        score += 1
    
    if s.debt_to_income >= 65:
        score += 3
    elif s.debt_to_income >= 50:
        score += 2
    elif s.debt_to_income >= 35:
        score += 1
    
    if s.payment_history < 75:
        score += 3
    elif s.payment_history < 85:
        score += 2
    elif s.payment_history < 92:
        score += 1
    
    if s.credit_utilization >= 80:
        score += 3
    elif s.credit_utilization >= 60:
        score += 2
    elif s.credit_utilization >= 40:
        score += 1
    
    if s.amount > s.available_credit * 0.55:
        score += 2
    elif s.amount > s.available_credit * 0.35:
        score += 1
    
    if score >= 9:
        return "high"
    if score >= 5:
        return "medium"
    return "low"
    
    
def build_reasons(s: TransactionState, risk_band: str) -> List[str]:
    reasons = []
    
    if s.credit_score < 650:
        reasons.append(f"Credit score is relatively weak at {s.credit_score}.")
    elif s.credit_score > 740:
        reasons.append(f"Credit score is strong at {s.credit_score}.")
    
    if s.debt_to_income >= 60:
        reasons.append(f"Debt-to-income is high at {s.debt_to_income}%.")
    elif s.debt_to_income <= 30:
        reasons.append(f"Debt-to-income is healthy at {s.debt_to_income}%.")
    
    if s.credit_utilization >= 60:
        reasons.append(f"Credit utilization is elevated at {s.credit_utilization}%.")
    elif s.credit_utilization <= 30:
        reasons.append(f"Credit utilization is low at {s.credit_utilization}%.")
    
    if s.payment_history < 80:
        reasons.append(f"Payment history is weak at {s.payment_history}%.")
    elif s.payment_history >= 95:
        reasons.append(f"Payment history is very strong at {s.payment_history}%.")
    
    if s.amount > s.available_credit * 0.5:
        reasons.append("Transaction amount is large relative to available credit.")
    
    if risk_band == "high" and not reasons:
        reasons.append("Multiple risk indicators suggest restrictive action.")
    if risk_band == "low" and not reasons:
        reasons.append("Profile appears stable enough for approval-oriented actions.")
    
    return reasons[:4]
    
    
def recommended_action_for_band(s: TransactionState, risk_band: str) -> str:
    if risk_band == "high":
        if s.debt_to_income >= 70 or s.payment_history < 75:
            return "decline"
        return "delay_purchase"
    if risk_band == "medium":
        if s.amount > 30000:
            return "convert_to_emi"
        if s.credit_utilization > 60:
            return "route_to_debit"
        return "delay_purchase"
    if s.amount < 15000 and s.credit_score >= 720:
        return "approve_card_1"
    return "approve_card_2"
    
    
def policy_checks(s: TransactionState, action: str) -> List[PolicyCheck]:
    checks = []
    
    checks.append(
        PolicyCheck(
            name="minimum_credit_quality",
            passed=not (action in ["approve_card_1", "approve_card_2"] and s.credit_score < 620),
            detail=f"Approvals below credit score 620 are restricted; current score is {s.credit_score}.",
        )
    )
    
    checks.append(
        PolicyCheck(
            name="high_dti_guardrail",
            passed=not (action in ["approve_card_1", "approve_card_2"] and s.debt_to_income >= 65),
            detail=f"Approvals with DTI >= 65% are discouraged; current DTI is {s.debt_to_income}%.",
        )
    )
    
    checks.append(
        PolicyCheck(
            name="high_utilization_guardrail",
            passed=not (action == "approve_card_1" and s.credit_utilization >= 70),
            detail=f"Premium approval at utilization >= 70% is discouraged; current utilization is {s.credit_utilization}%.",
        )
    )
    
    checks.append(
        PolicyCheck(
            name="amount_vs_credit",
            passed=not (action in ["approve_card_1", "approve_card_2"] and s.amount > s.available_credit * 0.7),
            detail="High transaction amount relative to available credit is checked before approval.",
        )
    )
    
    return checks
    
    
def score_action(s: TransactionState, action: str) -> float:
    task = env.current_task

    # -------- EASY TASK --------
    if task == "easy":
        if s.credit_score > 700 and action in ["approve_card_1", "approve_card_2"]:
            return 1.0
        elif s.credit_score <= 700 and action == "decline":
            return 1.0
        return -1.0

    # -------- MEDIUM TASK --------
    elif task == "medium":
        risk_band = get_risk_band(s)

        if risk_band == "low" and action in ["approve_card_1", "approve_card_2"]:
            return 1.0
        elif risk_band == "medium" and action in ["route_to_debit", "convert_to_emi"]:
            return 0.8
        elif risk_band == "high" and action == "decline":
            return 1.0
        return -0.5

    # -------- HARD TASK (YOUR ORIGINAL LOGIC SIMPLIFIED BUT SAFE) --------
    risk_band = get_risk_band(s)
    rec = recommended_action_for_band(s, risk_band)

    base = {
        "approve_card_1": 0.15,
        "approve_card_2": 0.20,
        "route_to_debit": 0.35,
        "convert_to_emi": 0.40,
        "delay_purchase": 0.45,
        "decline": 0.50,
    }[action]

    # smarter band adjustment (keeps your idea but safer)
    if risk_band == "low":
        band_adjust = 0.5 if action in ["approve_card_1", "approve_card_2"] else -0.2
    elif risk_band == "medium":
        band_adjust = 0.2 if action in ["route_to_debit", "convert_to_emi"] else -0.1
    else:  # high risk
        band_adjust = 0.4 if action == "decline" else -0.8

    recommendation_bonus = 0.2 if action == rec else 0.0

    reward = base + band_adjust + recommendation_bonus

    return max(-1.0, min(1.0, round(reward, 4)))
    
    
def build_leaderboard(s: TransactionState) -> List[LeaderboardEntry]:
    ranked = [
        LeaderboardEntry(
            action=a,
            reward=max(0.0, min(1.0, (score_action(s, a) + 1) / 2))
)
        for a in ALL_ACTIONS
    ]
    ranked.sort(key=lambda x: x.reward, reverse=True)
    return ranked
    
    
@app.get("/")
def root():
    return {"message": "payment_credit_env is running", "version": "0.2.0"}
    
    
class ResetRequest(BaseModel):
    task_id: str


@app.post("/reset", response_model=TransactionState)
def reset(req: ResetRequest):
    if req.task_id not in ["easy", "medium", "hard"]:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Invalid task_id")

    env.current_task = req.task_id
    return env.reset()
    
    
@app.get("/state", response_model=TransactionState)
def state():
    return env.get_state()
    
    
@app.post("/step", response_model=StepResponse)
def step(req: StepRequest):
    s = env.get_state()
    risk_band = get_risk_band(s)
    recommended_action = recommended_action_for_band(s, risk_band)
    reasons = build_reasons(s, risk_band)
    leaderboard = build_leaderboard(s)
    checks = policy_checks(s, req.action)
    raw_reward = score_action(s, req.action)
    reward = max(0.0, min(1.0, (raw_reward + 1) / 2))
    
    env.audit_log.append(
        AuditLogEntry(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            transaction_id=s.transaction_id,
            action=req.action,
            reward=reward,
            risk_band=risk_band,
            recommended_action=recommended_action,
        )
    )
    
    return StepResponse(
        transaction_id=s.transaction_id,
        action=req.action,
        reward=reward,
        task_id=env.current_task,
        state=s,
        risk_band=risk_band,
        recommended_action=recommended_action,
        reasons=reasons,
        leaderboard=leaderboard,
        policy_checks=checks,
    )
    
    
@app.get("/audit-log", response_model=List[AuditLogEntry])
def get_audit_log():
    return env.audit_log