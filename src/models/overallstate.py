
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from typing import Optional
from typing import List, Dict, Any

class OutputState(TypedDict):
    reponse: Optional[str]

class InputState(TypedDict):
    user_input: Optional[str]



class OverallState(InputState, OutputState):
    event_type: Optional[str]
    questions: Optional[List[str]]
    answers: Optional[Dict[str, str]]
    carbon_impact: Optional[Dict[str, float]]
    recommendations: Optional[List[str]]
    waiting_for_human: bool = False
    current_question_index: int = 0
    carbon_impact_detail: Optional[Dict[str, float]]


