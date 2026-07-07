from app.schemas import EducationProfile, JobProfile, RecommendationResponse


class RecommendationService:
    def recommend_education(self, profile: EducationProfile) -> RecommendationResponse:
        country = profile.target_country or "a suitable target country"
        risks = []
        next_actions = [
            "Collect passport, transcripts, CV, English test status, and budget details.",
            "Run country-specific eligibility and visa truth checks.",
            "Create a shortlist of universities/courses only after verified requirements are available.",
        ]

        if not profile.budget_eur:
            risks.append("Budget is missing; financial proof and tuition feasibility cannot be assessed.")
        if not profile.english_test_score:
            risks.append("English test status is missing; admission and visa eligibility may be affected.")

        return RecommendationResponse(
            domain="education",
            summary=f"Initial study-abroad pathway can be prepared for {country}, but official university and visa rules must be verified first.",
            confidence=0.55 if risks else 0.7,
            risks=risks,
            next_actions=next_actions,
        )

    def match_jobs(self, profile: JobProfile) -> RecommendationResponse:
        risks = []
        if not profile.skills:
            risks.append("No skills were supplied; matching quality will be low.")
        if not profile.target_country:
            risks.append("Target country is missing; visa route and employer sponsorship rules cannot be checked.")

        return RecommendationResponse(
            domain="recruitment",
            summary=f"Initial job matching can start for role '{profile.role}', but eligibility depends on skills, experience, target-country rules, and employer sponsorship.",
            confidence=0.5 if risks else 0.68,
            risks=risks,
            next_actions=[
                "Parse CV and extract structured skills.",
                "Check target-country work visa rules from official sources.",
                "Create employer shortlist and application tracker.",
            ],
        )
