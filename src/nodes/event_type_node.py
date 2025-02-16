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

from src.graph import OverallState

from dotenv import load_dotenv

load_dotenv()

mistral = ChatMistralAI(api_key=os.environ["MISTRAL_API_KEY"])

def get_event_type(state: OverallState) -> OverallState:
    response = mistral.invoke([
        HumanMessage(content="Je suis un agent qui calcule l'impact carbone d'événements. "
                            "L'utilisateur dit: " + state["user_input"] + 
                            ". Quel type d'événement est-ce? Répondre en un seul mot.")
    ])
    state["event_type"] = response.content
    state["current_question_index"] = 0
    state["answers"] = {}  # Initialisation du dictionnaire answers
    state["carbon_impact_detail"] = {}
    return state

def generate_questions(state: OverallState) -> OverallState:
    prompt = f"""Pour un événement de type {state["event_type"]}, génère une liste de 5 à 10 questions 
    pertinentes pour évaluer l'impact carbone. Format: JSON array de strings.
    
    Parmi ces questions il faut aborder au moins une fois:
    - le nombre de participants
    - le nombre de jours
    - la quantité et nature des repas
    - si l'événement est à l'extérieur ou à l'intérieur, et dans ce cas le type de climatisation ou de chauffage
    - le type de transport utilisé pour venir à l'événement par les participants
    """
    
    response = mistral.invoke([
        HumanMessage(content=prompt)
    ])
    state["questions"] = json.loads(response.content)
    state["waiting_for_human"] = False
    return state


def ask_next_question(state: OverallState) -> OverallState:
    if state["current_question_index"] < len(state["questions"]):
        # Afficher la question et attendre la réponse
        question = state["questions"][state["current_question_index"]]
        answer = input(f"\n{question}\nVotre réponse: ")
        
        # Mettre à jour l'état avec la réponse
        state["answers"][question] = answer
        state["waiting_for_human"] = True
    return state


# def compute_carbon_impact(state: OverallState) -> OverallState:
#     prompt = f"""
#     Événement: {state["event_type"]}
#     Questions et réponses:
#     {json.dumps(state["answers"], indent=2)}
    
#     Calcule l'impact carbone détaillé de cet élèment de l'événement. 
#     Retourne UNIQUEMENT un JSON valide avec les catégories comme clés et les impacts en kg CO2e comme valeurs.
#     Format attendu: {{"categorie1": valeur1, "categorie2": valeur2}}
#     Base toi sur des moyennes réalistes.
#     """
#     question = state["questions"][state["current_question_index"]]
#     response = mistral.invoke([
#         HumanMessage(content=prompt)
#     ])
    
#     try:
#         impact_data = json.loads(response.content)
#     except json.JSONDecodeError:
#         # En cas d'échec, on retourne un dictionnaire vide ou une valeur par défaut
#         impact_data = {"erreur": 0}
        
#     state["carbon_impact_detail"][question] = impact_data
#     return state


def compute_carbon_impact(state: OverallState) -> OverallState:
    max_follow_up_questions = 3
    follow_up_count = 0
    
    while follow_up_count < max_follow_up_questions:
        # Vérifier si plus de détails sont nécessaires
        need_more_info_prompt = f"""
        Événement: {state["event_type"]}
        Questions et réponses actuelles:
        {json.dumps(state["answers"], indent=2)}
        
        As-tu besoin de plus d'informations pour calculer l'impact carbone précisément?
        Si oui, quelle question poserais-tu? Si non, réponds "NON".
        Réponds uniquement par "NON" ou par une question précise.
        """
        
        need_more_info_response = mistral.invoke([
            HumanMessage(content=need_more_info_prompt)
        ])
        
        if need_more_info_response.content.strip().upper() == "NON":
            break
            
        # Poser la question supplémentaire
        new_question = need_more_info_response.content
        state["answers"][new_question] = input(f"\n{new_question}\nVotre réponse: ")
        follow_up_count += 1
    
    # Calculer l'impact final
    final_prompt = f"""
    Événement: {state["event_type"]}
    Questions et réponses complètes:
    {json.dumps(state["answers"], indent=2)}
    
    Calcule l'impact carbone détaillé de cet événement. 
    Retourne un JSON avec les catégories comme clés et les impacts en kg CO2e comme valeurs.
    Base toi sur des moyennes réalistes.
    """
    
    response = mistral.invoke([
        HumanMessage(content=final_prompt)
    ])
    state["carbon_impact_detail"] = json.loads(response.content)
    return state


def should_continue(state: OverallState) -> bool:
    state["waiting_for_human"] = state["current_question_index"] < len(state["questions"])
    state["current_question_index"] += 1
    return state


