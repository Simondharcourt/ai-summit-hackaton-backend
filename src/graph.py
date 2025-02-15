from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from typing import Optional

# Définition de l'état
class InputState(TypedDict):
    message: Optional[str]


class OutputState(TypedDict):
    reponse: Optional[str]
    
class OverallState(InputState, OutputState):
    event_type: Optional[str]
    event_duration: Optional[str]
    event_location: Optional[str]
    message: Optional[str]
    reponse: Optional[str]
    outside: Optional[bool]
    nb_participants: Optional[int]
    
def event_type_node(state: OverallState):
    message = "Quel est le type d'événement ?"
    state["event_type"] = input(message)
    return state

def nb_participants_node(state: OverallState):
    message = "Combien y aura-t-il de participants ?"
    state["nb_participants"] = input(message)
    return state

def event_duration_in_days_node(state: OverallState):
    message = "Combien de jours durera l'événement ?"
    state["event_duration"] = input(message)
    return state

def event_location_node(state: OverallState):
    message = "Où se situe l'événement ?"
    state["event_location"] = input(message)
    return state

def repartition_transport_node(state: OverallState):
    return state # dict

def have_facture_food_node(state: OverallState):
    return state # bool

def parse_facture_food_node(state: OverallState):
    return state # dict

def detail_food_node(state: OverallState):
    return state # dict

def outside_or_inside_event_node(state: OverallState):
    # Demander à l'utilisateur si l'événement est à l'extérieur ou à l'intérieur
    reponse = input("L'événement est-il à l'extérieur ou à l'intérieur ? (exterieur/interieur): ").lower()
    while reponse not in ["exterieur", "interieur"]:
        reponse = input("Veuillez répondre par 'exterieur' ou 'interieur': ").lower()
    state["outside"] = True if reponse == "exterieur" else False
    return "outside" if reponse == "exterieur" else "inside"

def chauffage_ou_climatisation_node(state: OverallState):
    return state # bool

def food_analyse_node(state: OverallState):
    return state

def food_sum_up_and_what_else_node(state: OverallState):
    return state # bool

def food_to_agribalyse_node(state: OverallState):
    return state




graph = StateGraph(OverallState)


graph.add_node("which_event_type", event_type_node)
graph.add_node("how_many_participants", nb_participants_node)
graph.add_node("how_long_event_in_days", event_duration_in_days_node)
graph.add_node("where_is_event", event_location_node)

graph.add_node("how_repartition_transport", repartition_transport_node)


graph.add_node("detail_food", detail_food_node)
graph.add_node("have_facture_food", have_facture_food_node)


graph.add_node("parse_facture_food", parse_facture_food_node)
graph.add_node("food_to_agribalyse", food_to_agribalyse_node)

graph.add_node("chauffage_ou_climatisation", chauffage_ou_climatisation_node)

graph.add_edge(START, "which_event_type")
graph.add_edge("which_event_type", "how_many_participants")
graph.add_edge("how_many_participants", "how_long_event_in_days")
graph.add_edge("how_long_event_in_days", "where_is_event")
graph.add_edge("where_is_event", "how_repartition_transport")
graph.add_conditional_edges(
    "how_repartition_transport",
    outside_or_inside_event_node,
    {
        "outside": "chauffage_ou_climatisation",
        "inside": "have_facture_food"
    }
)
graph.add_edge("chauffage_ou_climatisation", "have_facture_food")
graph.add_conditional_edges(
    "have_facture_food",
    have_facture_food_node,
    {
        "have_facture_food": "parse_facture_food",
        "no_facture_food": "detail_food",
    },
)
graph.add_edge("detail_food", "food_to_agribalyse")
graph.add_edge("parse_facture_food", "food_to_agribalyse")
graph.add_edge("food_to_agribalyse", END)
graph.compile()


