"""
Pydantic schemas for structured output from LLM.
"""

from pydantic import BaseModel, Field


class ArticleSummary(BaseModel):
    """Structured summary of a financial article for non-experts."""
    
    overview: str = Field(
        description="A 1-2 sentence overview explaining what the article is about in simple terms"
    )
    key_points: list[str] = Field(
        description="3-5 main points explained in plain language, avoiding financial jargon"
    )
    why_it_matters: str = Field(
        description="Why this news matters to the average person, explained simply"
    )
    simple_explanation: str = Field(
        description="A complete summary in 2-3 paragraphs using everyday language, as if explaining to a friend with no financial background"
    )


class ArticleRank(BaseModel):
    """Ranking score for a financial article."""
    
    score: float = Field(
        description="Relevance and importance score from 0 to 100, where 100 is most relevant/important",
        ge=0.0,
        le=100.0
    )
