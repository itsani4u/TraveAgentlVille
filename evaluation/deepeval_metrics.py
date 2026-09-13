"""
evaluation/deepeval_metrics.py
---------------------------------
Wraps DeepEval metrics for the trip planner. Two kinds of checks:

1. LLM-quality metrics from DeepEval (answer relevancy, faithfulness) -
   these call an LLM-as-judge under the hood.
2. Deterministic, code-only checks (schema validity, budget compliance) -
   no LLM needed, just Python, so they're fast and free to run in CI.

Run this file directly (`python -m evaluation.deepeval_metrics`) for a
quick demo against a sample itinerary.
"""

import json
from typing import Dict

from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase
from deepeval.models import DeepEvalBaseLLM
from langchain_google_genai import ChatGoogleGenerativeAI

from agent.schemas import TravelPlan, VacationInfo
import config


class GeminiJudgeModel(DeepEvalBaseLLM):
    """Points DeepEval's LLM-as-judge metrics at Gemini instead of the
    default OpenAI model, so the whole project only ever needs
    GOOGLE_API_KEY - no second API key for evaluation."""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.GEMINI_LLM_MODEL
        self.model = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=config.GOOGLE_API_KEY,
            temperature=0,
        )

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        return self.model.invoke(prompt).content

    async def a_generate(self, prompt: str) -> str:
        response = await self.model.ainvoke(prompt)
        return response.content

    def get_model_name(self) -> str:
        return f"Gemini ({self.model_name})"


# --- Deterministic checks (no LLM call needed) --------------------------

def check_schema_validity(itinerary_json: str) -> bool:
    """True if the JSON string parses into a valid TravelPlan model."""
    try:
        TravelPlan.model_validate_json(itinerary_json)
        return True
    except Exception:
        return False


def check_budget_compliance(itinerary_json: str) -> bool:
    """True if the plan's total cost is within its stated budget."""
    plan = TravelPlan.model_validate_json(itinerary_json)
    return plan.total_cost() <= plan.vacation_info.total_budget


def check_min_activities(itinerary_json: str, minimum: int = 2) -> bool:
    plan = TravelPlan.model_validate_json(itinerary_json)
    return all(len(day.activities) >= minimum for day in plan.day_plans)


# --- DeepEval LLM-judged checks -------------------------------------------

def evaluate_narrative_quality(user_input: str, actual_output: str, retrieval_context: list = None) -> Dict:
    """Scores a generated narrative summary for relevancy + faithfulness
    to the retrieved knowledge-base context (if any was used)."""
    test_case = LLMTestCase(
        input=user_input,
        actual_output=actual_output,
        retrieval_context=retrieval_context or [actual_output],
    )

    judge = GeminiJudgeModel()
    relevancy = AnswerRelevancyMetric(threshold=0.7, model=judge)
    faithfulness = FaithfulnessMetric(threshold=0.7, model=judge)

    relevancy.measure(test_case)
    faithfulness.measure(test_case)

    return {
        "answer_relevancy": {"score": relevancy.score, "passed": relevancy.is_successful()},
        "faithfulness": {"score": faithfulness.score, "passed": faithfulness.is_successful()},
    }


def run_full_eval_suite(itinerary_json: str, narrative: str, user_input: str) -> Dict:
    """Runs every check (deterministic + LLM-judged) and returns one report."""
    report = {
        "schema_validity": check_schema_validity(itinerary_json),
        "budget_compliance": check_budget_compliance(itinerary_json) if check_schema_validity(itinerary_json) else False,
        "min_activities": check_min_activities(itinerary_json) if check_schema_validity(itinerary_json) else False,
    }
    try:
        report["narrative_quality"] = evaluate_narrative_quality(user_input, narrative)
    except Exception as e:
        report["narrative_quality"] = {"error": str(e)}
    return report


def run_integrated_agent_eval(vacation_info: VacationInfo, plan_result: Dict) -> Dict:
    """The entry point agent.core_agent.plan_trip() calls after every real
    run. Unlike the __main__ smoke test below (which uses static sample
    data), this runs DeepEval + the deterministic checks directly against
    that run's actual TravelPlan and narrative."""
    itinerary_json = plan_result["travel_plan"].model_dump_json()
    narrative = plan_result["narrative"]
    user_input = (
        f"Plan a trip to {vacation_info.destination} from {vacation_info.start_date} "
        f"to {vacation_info.end_date} with interests {vacation_info.interests} "
        f"and a budget of {vacation_info.total_budget}."
    )
    return run_full_eval_suite(itinerary_json, narrative, user_input)


if __name__ == "__main__":
    # Minimal smoke test with a tiny hand-written itinerary.
    sample = {
        "vacation_info": {
            "destination": "AgentsVille",
            "start_date": "2026-06-01",
            "end_date": "2026-06-02",
            "total_budget": 500,
            "interests": ["food"],
        },
        "day_plans": [
            {
                "date": "2026-06-01",
                "activities": [
                    {"name": "Food Crawl", "description": "", "cost": 50, "is_outdoor": False},
                    {"name": "Museum", "description": "", "cost": 30, "is_outdoor": False},
                ],
            },
            {
                "date": "2026-06-02",
                "activities": [
                    {"name": "Park Picnic", "description": "", "cost": 20, "is_outdoor": True},
                    {"name": "Jazz Cellar", "description": "", "cost": 40, "is_outdoor": False},
                ],
            },
        ],
    }
    sample_json = json.dumps(sample)
    print("schema_validity:", check_schema_validity(sample_json))
    print("budget_compliance:", check_budget_compliance(sample_json))
    print("min_activities:", check_min_activities(sample_json))
