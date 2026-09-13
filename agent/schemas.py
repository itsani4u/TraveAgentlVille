"""
agent/schemas.py
-----------------
All Pydantic models for the AgentsVille Trip Planner.
Keeping every schema in one file makes it easy for a student to see the
full "shape" of the data the whole app passes around.
"""

from __future__ import annotations
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class VacationInfo(BaseModel):
    """FR-1: captures what the traveler wants."""
    destination: str = Field(default="AgentsVille")
    start_date: date
    end_date: date
    total_budget: float = Field(gt=0, description="Total trip budget in USD")
    interests: List[str] = Field(default_factory=list, description="e.g. ['art', 'food', 'hiking']")

    def num_days(self) -> int:
        return (self.end_date - self.start_date).days + 1


class Activity(BaseModel):
    """A single scheduled activity inside a day."""
    name: str
    description: str = ""
    cost: float = Field(ge=0)
    is_outdoor: bool = False
    start_time: Optional[str] = None  # e.g. "09:00"
    matched_interest: Optional[str] = None


class DayPlan(BaseModel):
    """All activities planned for one calendar date."""
    date: date
    activities: List[Activity] = Field(default_factory=list)

    def day_cost(self) -> float:
        return sum(a.cost for a in self.activities)


class TravelPlan(BaseModel):
    """FR-2: the full structured itinerary the Itinerary Agent must produce."""
    vacation_info: VacationInfo
    day_plans: List[DayPlan] = Field(default_factory=list)

    def total_cost(self) -> float:
        return sum(dp.day_cost() for dp in self.day_plans)


class CompatibilityResult(BaseModel):
    """FR-3: output of the weather/activity compatibility check."""
    activity_name: str
    date: date
    is_compatible: bool
    justification: str


class EvalResult(BaseModel):
    """Result returned by run_evals_tool (FR-4)."""
    passed: bool
    issues: List[str] = Field(default_factory=list)
