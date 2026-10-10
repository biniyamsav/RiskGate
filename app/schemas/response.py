from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class RiskAction(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    DENY = "DENY"


class TransactionAssessmentResponse(BaseModel):
    transaction_id: str = Field(..., description="The unique identifier for the transaction")
    risk_score: int = Field(..., ge=0, le=100, description="Risk score between 0 (safe) and 100 (critical risk)")
    action: RiskAction = Field(..., description="Recommended decision: ALLOW, REVIEW, or DENY")
    risk_factors: List[str] = Field(default_factory=list, description="List of detected anomalies or risk signals")
    summary_reasoning: str = Field(..., description="Brief summary explanation for the risk assessment")