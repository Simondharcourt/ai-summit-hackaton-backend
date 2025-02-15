import os, json
from mistralai import Mistral

api_key = "29NL9Foa83Niu5QLidPK4JMMEwjB7OCx"
model = "mistral-large-latest"

categories = ("Base", "Electricity", "Food", "Transport", "Infrastructure", "Other")
args_cat = ({"n_persons": "integer"}, {"is_inside": "boolean", "n_hours": "integer"}, {"menu": "string"}, {"mode": "string", "distance": "float"}, {})

argsTotal = {key: None for dico in args_cat for key in dico}
dicoEmissions = [None] * len(categories)

