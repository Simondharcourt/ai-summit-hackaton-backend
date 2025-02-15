from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from src.graph import EveningCarbonState, app as graph_app

class UserInput(BaseModel):
    guests: int
    meal_type: str
    transport: str

class CarbonResponse(BaseModel):
    responses: Dict
    total_emissions: float
    message: str

app = FastAPI(
    title="Calculateur de Bilan Carbone",
    description="API pour calculer l'empreinte carbone d'une soirée"
)

@app.post("/calculate_carbon", response_model=CarbonResponse)
async def calculate_carbon(input_data: UserInput):
    try:
        # Initialiser l'état
        state = EveningCarbonState()
        
        # Mettre à jour l'état avec les entrées utilisateur
        state.reponses['guests'] = input_data.guests
        state.update_emission(input_data.guests * 5)  # 5 kg CO₂ par invité
        
        state.reponses['meal'] = input_data.meal_type
        if input_data.meal_type == "international":
            state.update_emission(50)
        else:
            state.update_emission(20)
            
        state.reponses['transport'] = input_data.transport
        if input_data.transport == "voiture":
            state.update_emission(30)
        elif input_data.transport == "transports en commun":
            state.update_emission(15)
        
        # Exécuter le graphe
        final_state = graph_app.invoke(state)
        
        return CarbonResponse(
            responses=final_state.reponses,
            total_emissions=final_state.emissions_total,
            message=f"Le bilan carbone estimé de votre soirée est de {final_state.emissions_total} kg CO₂"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
async def root():
    return {
        "message": "Bienvenue sur l'API du Calculateur de Bilan Carbone",
        "usage": "Utilisez POST /calculate_carbon pour calculer l'empreinte carbone de votre soirée"
    } 