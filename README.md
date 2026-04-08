---
title: Payment Credit Decisioning Environment
emoji: 💳
colorFrom: gray
colorTo: blue
sdk: docker
pinned: false
app_port: 7860
tags:
  - openenv
  - fintech
  - reinforcement-learning
  - credit-scoring
  - payment-routing
---

# Payment Credit Env — RL Environment for Payment Decisioning

A Reinforcement Learning environment built with OpenEnv for simulating and training AI agents on real-time payment credit decisioning tasks.

Built for the **Meta PyTorch OpenEnv Hackathon x Scaler School of Technology** — Round 1 Submission.

[![Open in HF Spaces](https://huggingface.co/datasets/huggingface/badges/resolve/main/open-in-hf-spaces-sm.svg)](https://huggingface.co/spaces/Anirudhreddy19/payment-credit-openenv)
[![Documentation](https://img.shields.io/badge/API-Docs-blue)](https://anirudhreddy19-payment-credit-openenv.hf.space/docs)

## Overview

**Payment Credit Env** is a Mini-RL environment that simulates a credit decisioning system used by banks and FinTech companies. When a customer makes a transaction, the system must decide the optimal action among multiple choices:

- **Approve Card 1** — Approve the transaction on the primary credit card
- **Approve Card 2** — Approve on the secondary/fallback credit card
- **Route to Debit** — Route the payment through the customer's debit account
- **Convert to EMI** — Convert the transaction into an EMI (Equated Monthly Installment) plan
- **Delay Purchase** — Defer the transaction to a later date
- **Decline** — Reject the transaction entirely

The environment generates randomized but realistic transaction profiles and evaluates each action based on risk assessment, providing rewards and policy compliance checks.

## Quick Start

```python
from payment_credit_env import PaymentCreditEnv, PaymentCreditAction

# Connect to the deployed environment
env = PaymentCreditEnv(base_url="https://anirudhreddy19-payment-credit-openenv.hf.space")

# Reset to get a new transaction
state = env.reset()
print(f"Transaction: {state.observation.transaction_id}")
print(f"Amount: ₹{state.observation.amount}")
print(f"Risk Band: {state.observation.risk_band}")

# Evaluate actions
for action in ["approve_card_1", "route_to_debit", "convert_to_emi"]:
    result = env.step(PaymentCreditAction(action=action))
    print(f"{action}: reward={result.reward}, recommended={result.recommended_action}")

env.close()
```

## Environment Architecture

### State

Each transaction includes:
- `transaction_id` — Unique identifier (TXN-YYYYMMDD-XXX)
- `amount` — Transaction amount (₹5,000 – ₹50,000)
- `credit_score` — Credit score (580 – 850)
- `available_credit` — Available credit limit
- `monthly_spend` — Average monthly spending
- `debt_to_income` — DTI ratio (%)
- `payment_history` — Payment history score (%)
- `credit_utilization` — Credit utilization ratio (%)
- `last_payment_date` — Date of last payment
- `account_age_months` — Account age in months

### Risk Bands

Transactions are classified into three risk categories:

| Band | Credit Score | DTI | Utilization |
|------|-------------|-----|-------------|
| **Low** | ≥ 750 | ≤ 25% | ≤ 35% |
| **Medium** | ≥ 680 | ≤ 40% | ≤ 55% |
| **High** | < 680 | > 40% | > 55% |

### Policy Checks

Every transaction is validated against:
- **Credit Score Threshold** — Minimum 650
- **Debt-to-Income Policy** — Maximum 40%
- **Credit Utilization Policy** — Maximum 60%

### Reward System

Actions are scored based on risk band:
- **Low Risk** → Approve actions get high rewards (~0.9)
- **Medium Risk** → Route/EMI actions get high rewards (~0.8)
- **High Risk** → Delay/Decline actions get high rewards (~0.8)

### Audit Logging

Every action taken is logged with:
- Timestamp
- Transaction ID
- Action taken
- Reward score
- Risk band
- Recommended action

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Interactive dashboard |
| `/state` | GET | Get current transaction state |
| `/reset` | POST | Generate a new random transaction |
| `/step` | POST | Evaluate an action on the current state |
| `/audit-log` | GET | Retrieve the audit log |
| `/docs` | GET | OpenAPI/Swagger documentation |
| `/health` | GET | Health check |

## Live Demo

- **Dashboard**: https://anirudhreddy19-payment-credit-openenv.hf.space
- **API Docs**: https://anirudhreddy19-payment-credit-openenv.hf.space/docs

## Project Structure

```
payment-credit-openenv/
├── README.md
├── openenv.yaml
├── pyproject.toml
├── client.py
├── models.py
├── index.html              # Interactive dashboard
└── server/
    ├── app.py              # FastAPI server
    ├── payment_credit_env_environment.py
    └── Dockerfile
```

## Technologies Used

- **Python 3.11+**
- **FastAPI** — REST API server
- **Pydantic** — Data validation and models
- **Docker** — Containerization
- **OpenEnv** — RL environment framework
- **Hugging Face Spaces** — Deployment

## Hackathon Submission

This project was submitted to the **Meta PyTorch OpenEnv Hackathon x Scaler School of Technology** — Round 1.

**Theme**: FinTech / Financial Services — Payment Credit Decisioning

**What it solves**: Helps banks and FinTech companies train AI agents to make optimal payment routing decisions, reducing fraud risk while maximizing customer approval rates.

## Author

**Anirudh Reddy** | BTech CSE, Matrusri Engineering College

## License

MIT License
