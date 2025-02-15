import os, json
from mistralai import Mistral

api_key = "29NL9Foa83Niu5QLidPK4JMMEwjB7OCx"
model = "mistral-large-latest"

categories = ("Base", "Electricity", "Food", "Transport", "Infrastructure", "Other")
args_cat = ({"n_persons": "integer"}, {"is_inside": "boolean", "n_hours": "integer"}, {"menu": "string"}, {"mode": "string", "distance": "float"}, {})

argsTotal = {key: None for dico in args_cat for key in dico}
dicoEmissions = [None] * len(categories)



tabEmissions = [(),(),(),(),()]
argsTotal = []

def set_elec_emissions(is_inside, n_hours):
    if (is_inside):
        return n_hours*3
    else:
        return 0

def set_food_emissions(menu, nbPers):
    # Fonction très simple pour le moment
    # A long terme, il faut convertir le menu en CO2 à partir d'Agribalise et de Reasoning AI puis faire le pduit
    return 3*nbPers

def set_tspt_emissions(mode, dist, nbPers):
    return mode[0]*dist*nbPers


def set_infra_emissions(is_inside, n_hours):
    if(is_inside):
        return n_hours*3         # 3 correspond aux émissions de CO2 par heure dues au chauffage en intérieur
    else:
        return 0

def set_other_emissions():
    return 0






# def to_text(category, tabArgs, value):
#     text = ""
#     if(category==0):
        

#     return text
