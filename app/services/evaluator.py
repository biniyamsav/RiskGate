import json
import logging
from openai import AsyncOpenAI
from app.config import settings
from app.core.exceptions import LLMServiceException
from app.schemas.request import TransactionAssessmentRequest
from app.schemas.response import TransactionAssessmentResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are RiskGate Engine, an enterprise fraud detection system. 
Analyze the transaction payload and produce a strict JSON risk assessment.

Evaluation Rules:
1. Risk score range: 0 (safe) to 100 (critical risk).
2. Action thresholds:
   - 0 to 29: "ALLOW"
   - 30 to 69: "REVIEW"
   - 70 to 100: "DENY"
3. Flag high risk factors for:
   - Recent account age (< 7 days) paired with high amounts.
   - High failed login attempts in 24 hours (>= 3).
   - Past chargeback history.
   - VPN or proxy usage combined with country mismatches between billing and shipping.

Return ONLY a valid JSON object matching this structure:
{
  "transaction_id": "string",
  "risk_score": integer,
  "action": "ALLOW" | "REVIEW" | "DENY",
  "risk_factors": ["string"],
  "summary_reasoning": "string"
}
"""


class RiskEvaluatorService:

    def __init__(self, client: AsyncOpenAI):
        self.client = client

    async def evaluate_transaction(
        self, payload: TransactionAssessmentRequest
    ) -> TransactionAssessmentResponse:
        try:
            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Evaluate transaction: {payload.model_dump_json()}",
                    },
                ],
                response_format={"type": "json_object"},
            )

            raw_json = response.choices[0].message.content
            if not raw_json:
                raise LLMServiceException("Empty response received from LLM.")

            parsed_data = json.loads(raw_json)

            # Don't trust the model's self-reported action — recompute it from the
            # score, since the score/action pairing is only a prompt instruction,
            # not something the model is guaranteed to follow consistently.
            score = parsed_data.get("risk_score")
            if score is not None:
                if score <= 29:
                    expected_action = "ALLOW"
                elif score <= 69:
                    expected_action = "REVIEW"
                else:
                    expected_action = "DENY"

                if parsed_data.get("action") != expected_action:
                    logger.warning(
                        "LLM returned inconsistent action %r for score %s — correcting to %r",
                        parsed_data.get("action"), score, expected_action,
                    )
                    parsed_data["action"] = expected_action

            return TransactionAssessmentResponse(**parsed_data)

        except Exception as e:
            if isinstance(e, LLMServiceException):
                raise e
            raise LLMServiceException(f"Upstream provider error: {str(e)}")