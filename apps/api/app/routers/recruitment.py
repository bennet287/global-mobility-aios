from fastapi import APIRouter

from app.schemas import JobProfile, RecommendationResponse
from app.services.recommendation_service import RecommendationService

router = APIRouter()


@router.post("/recruitment/match", response_model=RecommendationResponse)
def match_jobs(payload: JobProfile) -> RecommendationResponse:
    return RecommendationService().match_jobs(payload)
