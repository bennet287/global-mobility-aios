from fastapi import APIRouter

from app.schemas import EducationProfile, RecommendationResponse
from app.services.recommendation_service import RecommendationService

router = APIRouter()


@router.post("/education/recommend", response_model=RecommendationResponse)
def recommend_education(payload: EducationProfile) -> RecommendationResponse:
    return RecommendationService().recommend_education(payload)
