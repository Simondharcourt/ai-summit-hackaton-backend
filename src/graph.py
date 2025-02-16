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

app = FastAPI()
mistral = ChatMistralAI(api_key=os.environ["MISTRAL_API_KEY"])
# Définition de l'état

from src.models.overallstate import OverallState

from src.nodes.event_type_node import get_event_type, generate_questions, ask_next_question, should_continue, compute_carbon_impact

graph = StateGraph(OverallState)

graph.add_node("get_event_type", get_event_type)
graph.add_node("generate_questions", generate_questions)
graph.add_node("ask_next_question", ask_next_question)
graph.add_node("should_continue", should_continue)
graph.add_node("compute_carbon_impact", compute_carbon_impact)


graph.add_edge(START, "get_event_type")
graph.add_edge("get_event_type", "generate_questions")

graph.add_edge("generate_questions", "ask_next_question")
graph.add_edge("ask_next_question", "compute_carbon_impact")
graph.add_edge("compute_carbon_impact", "should_continue")
graph.add_conditional_edges(
    "should_continue",
    lambda state: state["current_question_index"] < len(state["questions"]),
    {
        True: "ask_next_question",
        False: END
    }
)


graph.compile()






# graph.add_node("which_event_type", event_type_node)
# graph.add_node("how_many_participants", nb_participants_node)
# graph.add_node("how_long_event_in_days", event_duration_in_days_node)
# graph.add_node("where_is_event", event_location_node)
# graph.add_node("how_repartition_transport", repartition_transport_node)
# graph.add_node("detail_food", detail_food_node)
# graph.add_node("have_facture_food", have_facture_food_node)
# graph.add_node("parse_facture_food", parse_facture_food_node)
# graph.add_node("food_to_agribalyse", food_to_agribalyse_node)
# graph.add_node("chauffage_ou_climatisation", chauffage_ou_climatisation_node)

# graph.add_edge(START, "which_event_type")
# graph.add_edge("which_event_type", "how_many_participants")
# graph.add_edge("how_many_participants", "how_long_event_in_days")
# graph.add_edge("how_long_event_in_days", "where_is_event")
# graph.add_edge("where_is_event", "how_repartition_transport")
# graph.add_conditional_edges(
#     "how_repartition_transport",
#     outside_or_inside_event_node,
#     {
#         "outside": "chauffage_ou_climatisation",
#         "inside": "have_facture_food"
#     }
# )
# graph.add_edge("chauffage_ou_climatisation", "have_facture_food")
# graph.add_conditional_edges(
#     "have_facture_food",
#     have_facture_food_node,
#     {
#         "have_facture_food": "parse_facture_food",
#         "no_facture_food": "detail_food",
#     },
# )
# graph.add_edge("detail_food", "food_to_agribalyse")
# graph.add_edge("parse_facture_food", "food_to_agribalyse")
# graph.add_edge("food_to_agribalyse", END)
# graph.compile()


