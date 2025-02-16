import instructor
from pydantic import BaseModel
from enum import Enum
from pydantic import Field
from typing import List


class CarbonCategory(str, Enum):
    2 = "transport"
    0 = "electricité"
    1 = "alimentation"
    3 = "dechets"
    4 = "autre"

class CarbonImpactItem(BaseModel):
    categorie: CarbonCategory = Field(..., description="Catégorie de l'impact carbone")
    impact: float = Field(ge=0, description="Impact en kg CO2e")
    justification: str = Field(..., description="Explication du calcul")

class CarbonImpactResponse(BaseModel):
    items: List[CarbonImpactItem] = Field(..., description="Liste des impacts carbone")
    total_impact: float = Field(..., description="Impact total en kg CO2e")
    
    def compute_tuples(self):
        return [(item.categorie, item.impact, item.justification) for item in self.items]
