from fastapi import APIRouter, Depends
from openai import AsyncOpenAI
from app.core.dependencies import get_openai_client
from app.schemas.request import TransactionAssessmentRequest
from app.schemas.response import TransactionAssessmentResponse
from app.services.evaluator import RiskEvaluatorService

router = APIRouter()


@router.post(
    "/predictions",
    response_model=TransactionAssessmentResponse, 
    tags=["Assessment"],
    summary="Evaluate transaction risk",
)
async def evaluate_transaction_route(
    payload: TransactionAssessmentRequest,
    client: AsyncOpenAI = Depends(get_openai_client),
):
    evaluator = RiskEvaluatorService(client=client)
    return await evaluator.evaluate_transaction(payload)