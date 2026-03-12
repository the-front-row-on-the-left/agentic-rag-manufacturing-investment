from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class StartupCandidate(BaseModel):
    startup_id: str
    name: str
    website: str | None = None
    country: str | None = None
    domain: str = "manufacturing"
    short_description: str
    source_urls: list[str] = Field(default_factory=list)


class StartupSearchResponse(BaseModel):
    candidates: list[StartupCandidate] = Field(default_factory=list)


class StartupProfile(BaseModel):
    startup_id: str
    name: str
    website: str | None = None
    country: str | None = None
    core_product: str
    target_industry: list[str] = Field(default_factory=list)
    problem_statement: str
    customer_type: list[str] = Field(default_factory=list)
    use_cases: list[str] = Field(default_factory=list)
    team_info: list[str] = Field(default_factory=list)
    business_model: str | None = None
    source_urls: list[str] = Field(default_factory=list)


class QueryPlan(BaseModel):
    queries: list[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    claim: str
    detail: str
    source_title: str | None = None
    source_url: str | None = None
    confidence: Literal["high", "medium", "low"] | None = None


class TechAnalysis(BaseModel):
    startup_id: str
    name: str
    core_technology: list[str] = Field(default_factory=list)
    required_data: list[str] = Field(default_factory=list)
    deployment_type: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    integration_constraints: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class MarketAnalysis(BaseModel):
    startup_id: str
    name: str
    target_industry: list[str] = Field(default_factory=list)
    market_size: str
    growth_rate: str
    demand_drivers: list[str] = Field(default_factory=list)
    customer_pain_points: list[str] = Field(default_factory=list)
    roi_points: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class CompetitorComparisonPoint(BaseModel):
    technology: str | None = None
    pricing: str | None = None
    deployment: str | None = None
    customers: str | None = None


class Competitor(BaseModel):
    name: str
    category: Literal["direct", "indirect", "alternative"]
    website: str | None = None
    comparison_points: CompetitorComparisonPoint = Field(
        default_factory=CompetitorComparisonPoint
    )
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)


class CompetitorAnalysis(BaseModel):
    competitors: list[Competitor] = Field(default_factory=list)
    differentiation: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class CriterionAssessment(BaseModel):
    raw_score: int = Field(ge=1, le=5)
    reason: str
    weighted_score: float | None = None


class InvestmentDecisionDraft(BaseModel):
    problem_fit: CriterionAssessment
    market_opportunity: CriterionAssessment
    technology: CriterionAssessment
    deployability: CriterionAssessment
    data_availability: CriterionAssessment
    integration: CriterionAssessment
    scalability: CriterionAssessment
    team_capability: CriterionAssessment
    risk_assessment: CriterionAssessment
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)


class InvestmentDecision(BaseModel):
    total_score: float
    score_breakdown: dict[str, CriterionAssessment]
    decision: Literal["recommend", "conditional_review", "hold"]
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
