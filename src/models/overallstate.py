
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from typing import Optional
from typing import List, Dict, Any
from src.models.carbon import CarbonImpactResponse
class OutputState(TypedDict):
    reponse: Optional[str]

class InputState(TypedDict):
    user_input: Optional[str]



class OverallState(InputState, OutputState):
    event_type: Optional[str]
    questions: Optional[List[str]]
    answers: Optional[Dict[str, str]]
    recommendations: Optional[List[str]]
    waiting_for_human: bool = False
    current_question_index: int = 0
    carbon_impact_detail: Optional[CarbonImpactResponse]
    need_more_info: bool = True


