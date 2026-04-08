# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# """
# Data models for the Payment Credit Env Environment.

# The payment_credit_env environment is a simple test environment that echoes back messages.
# """

# from openenv.core.env_server.types import Action, Observation
# from pydantic import Field


# class PaymentCreditAction(Action):
#     """Action for the Payment Credit Env environment - just a message to echo."""

#     message: str = Field(..., description="Message to echo back")


# class PaymentCreditObservation(Observation):
#     """Observation from the Payment Credit Env environment - the echoed message."""

#     echoed_message: str = Field(default="", description="The echoed message")
#     message_length: int = Field(default=0, description="Length of the echoed message")

from enum import Enum
from pydantic import BaseModel, Field


class PaymentDecision(str, Enum):
    approve_card_1 = "approve_card_1"
    approve_card_2 = "approve_card_2"
    route_to_debit = "route_to_debit"
    convert_to_emi = "convert_to_emi"
    delay_purchase = "delay_purchase"
    decline = "decline"


class PaymentCreditAction(BaseModel):
    decision: PaymentDecision = Field(..., description="Action chosen by the agent")


class PaymentCreditObservation(BaseModel):
    monthly_income: float = Field(..., description="User monthly income")
    monthly_expenses: float = Field(..., description="User monthly fixed expenses")
    bank_balance: float = Field(..., description="Available bank balance")
    card_1_limit: float = Field(..., description="Credit limit of card 1")
    card_1_used: float = Field(..., description="Used amount on card 1")
    card_2_limit: float = Field(..., description="Credit limit of card 2")
    card_2_used: float = Field(..., description="Used amount on card 2")
    credit_score: int = Field(..., description="Current credit score")
    purchase_amount: float = Field(..., description="Current transaction amount")
    purchase_category: str = Field(..., description="Category of the purchase")
    due_in_days: int = Field(..., description="Days remaining to payment due date")
    emi_allowed: bool = Field(..., description="Whether EMI option is available")
    step_count: int = Field(..., description="Current step in episode")