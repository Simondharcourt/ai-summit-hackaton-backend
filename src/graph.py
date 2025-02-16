from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from typing import Optional

from typing import List, Dict, Any
from fastapi import FastAPI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import Graph
import json
from langchain_mistralai.chat_models import ChatMistralAI
import os
from dotenv import load_dotenv

load_dotenv()
from src.models.overallstate import OverallState, InputState

app = FastAPI()
mistral = ChatMistralAI(api_key=os.environ["MISTRAL_API_KEY"])
# Définition de l'état

from src.models.overallstate import OverallState

from src.nodes.event_type_node import get_event_type, generate_questions, ask_next_question, should_continue, insist_on_more_info, compute_final_bilan

graph = StateGraph(InputState)

graph.add_node("get_event_type", get_event_type)
graph.add_node("generate_questions", generate_questions)
graph.add_node("ask_next_question", ask_next_question)
graph.add_node("should_continue", should_continue)
# graph.add_node("insist_on_more_info", insist_on_more_info)
graph.add_node("compute_final_bilan", compute_final_bilan)
# graph.add_node("compute_final_bilan2", compute_final_bilan)

graph.add_edge(START, "get_event_type")
graph.add_edge("get_event_type", "generate_questions")

graph.add_edge("generate_questions", "ask_next_question")
graph.add_edge("ask_next_question", "compute_final_bilan")
# graph.add_edge("insist_on_more_info", "compute_final_bilan")
graph.add_edge("compute_final_bilan", "should_continue")
graph.add_conditional_edges(
    "should_continue",
    lambda state: state["current_question_index"] < len(state["questions"]),
    {
        True: "ask_next_question",
        False: END
    }
)
# graph.add_edge("insist_on_more_info", "compute_final_bilan2")
# graph.add_edge("compute_final_bilan2", END)
graph.compile()




