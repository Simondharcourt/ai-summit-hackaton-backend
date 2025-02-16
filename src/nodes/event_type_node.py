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

from src.models.overallstate import OverallState, InputState
from langchain_core.runnables import RunnableLambda
from typing import cast
from dotenv import load_dotenv

load_dotenv()
from pydantic import BaseModel, Field
from enum import Enum

# class CarbonCategory(str, Enum):
#     TRANSPORT = "transport"
#     ENERGIE = "energie"
#     ALIMENTATION = "alimentation"
#     DECHETS = "dechets"
#     AUTRE = "autre"

# class CarbonImpactItem(BaseModel):
#     nom: str = Field(..., description="Nom de l'élément")
#     categorie: CarbonCategory = Field(..., description="Catégorie de l'impact carbone")
#     impact: float = Field(ge=0, description="Impact en kg CO2e")
#     justification: str = Field(..., description="Explication du calcul")
# class CarbonImpactResponse(BaseModel):
#     items: List[CarbonImpactItem] = Field(..., description="Liste des impacts carbone")
#     total_impact: float = Field(..., description="Impact total en kg CO2e")
#     def compute_total_impact(self):
#         self.total_impact = sum(item.impact for item in self.items)


mistral = ChatMistralAI(api_key=os.environ["MISTRAL_API_KEY"])


async def get_event_type(state: InputState) -> OverallState:

    
    
    await send_message("Je suis un agent qui calcule l'impact carbone d'événements. Quel type d'événement organisez-vous ?")
    
    user_input = await wait_message()

    response = await mistral.ainvoke([
        HumanMessage(content="Je suis un agent qui calcule l'impact carbone d'événements. "
                            "L'utilisateur dit: " + user_input + 
                            ". Quel type d'événement est-ce? Répondre en un seul mot.")
    ])
    state["event_type"] = response.content
    state["current_question_index"] = 0
    state["answers"] = {}  # Initialisation du dictionnaire answers
    state["carbon_impact_detail"] = CarbonImpactResponse(items=[], total_impact=0)
    return state



async def generate_questions(state: OverallState) -> OverallState:
    prompt = f"""Pour un événement de type {state["event_type"]}, génère une liste de questions 
    pertinentes pour évaluer l'impact carbone. Il faut entre 5 et 10 questions simples.
    Format: JSON array de strings.
    
    Parmi ces questions il faut aborder au moins une fois:
    - le nombre de participants
    - le nombre de jours
    - la quantité et nature des repas
    - si l'événement est à l'extérieur ou à l'intérieur, et dans ce cas le type de climatisation ou de chauffage
    - le type de transport utilisé pour venir à l'événement par les participants
    """
    
    response = await mistral.ainvoke([
        HumanMessage(content=prompt)
    ])
    
    # S'assurer que les questions sont une liste de strings
    questions = json.loads(response.content)
    if isinstance(questions, list):
        state["questions"] = [str(q) for q in questions]
    else:
        state["questions"] = [str(questions)]
        
    state["waiting_for_human"] = False
    state["need_more_info"] = True
    return state


from src.main import wait_message, send_message, update_bilan

async def ask_next_question(state: OverallState) -> OverallState:
    if state["current_question_index"] < len(state["questions"]):
        # Afficher la question et attendre la réponse
        question = state["questions"][state["current_question_index"]]
        # answer = input(f"\n{question}\nVotre réponse: ")
        await send_message(question)

        answer = await wait_message()
        
        # Mettre à jour l'état avec la réponse
        state["answers"][question] = answer
        state["waiting_for_human"] = True
    return state


# async def insist_on_more_info(state: OverallState) -> OverallState:
#     max_follow_up_questions = 3
#     follow_up_count = 0
#     state["need_more_info"] = True

#     while follow_up_count < max_follow_up_questions:
#         # Vérifier si plus de détails sont nécessaires
#         need_more_info_prompt = f"""
#         Événement: {state["event_type"]}
#         Questions et réponses actuelles:
#         {json.dumps(state["answers"], indent=2)}
        
#         As-tu besoin de plus d'informations pour calculer l'impact carbone ?
        
#         Si tu as besoin d'informations supplémentaires sur ce sujet, quelle question poserais-tu? 
#         Si non, réponds "NON".
#         Réponds uniquement par "NON" ou uniquement par une question précise.
#         Par exemple, si tu as besoin d'informations sur les transports, tu peux poser la question "Combien de personnes vont venir en voiture?"
#         """
        
#         need_more_info_response = await mistral.ainvoke([
#             HumanMessage(content=need_more_info_prompt)
#         ])
        
#         if need_more_info_response.content.strip().upper() == "NON":
#             state["need_more_info"] = False
#             break
            
#         # Poser la question supplémentaire
#         new_question = need_more_info_response.content
#         state["answers"][new_question] = input(f"\n{new_question}\nVotre réponse: ")
#         follow_up_count += 1
    
#     return state


from openai import OpenAI


import instructor
from src.models.carbon import CarbonImpactResponse
async def compute_final_bilan(state: OverallState) -> OverallState:
    final_prompt = f"""
    Événement: {state["event_type"]}
    Questions et réponses complètes:
    {json.dumps(state["answers"], indent=2)}
    
    Calcule l'impact carbone détaillé de cet événement pour chaque catégorie avec des justifications cohérentes.
    """

    client = instructor.from_openai(OpenAI())
    carbon_impact_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": final_prompt},
            {"role": "user", "content": "Réponds uniquement par un JSON valide"}
        ],
        response_model=CarbonImpactResponse
    )
    
    state["carbon_impact_detail"] = carbon_impact_response
    await update_bilan(state["carbon_impact_detail"].compute_tuples())

    return state




async def should_continue(state: OverallState) -> bool:
    state["waiting_for_human"] = state["current_question_index"] < len(state["questions"])
    state["current_question_index"] += 1
    return state


