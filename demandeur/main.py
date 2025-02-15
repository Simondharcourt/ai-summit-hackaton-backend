import os, json
from mistralai import Mistral

api_key = "29NL9Foa83Niu5QLidPK4JMMEwjB7OCx"
model = "mistral-large-latest"

categories = ("Base", "Electricity", "Food", "Transport", "Infrastructure", "Other")
args_cat = ({"n_persons": "integer"}, {"is_inside": "boolean", "n_hours": "integer"}, {"menu": "string"}, {"mode": "string", "distance": "float"}, {}, {})

descr = {"n_persons": ("Set the number of guests attending the party", "Number of guests attending the party"),
		 "is_inside": ("Set whether the party is taking place indoors or outdoors", "A boolean that is true if the party is indoors, false if the party is outdoors"),
		 "n_hours": ("Set the estimated length of the party", "An integer giving the length of the party, in hours"),
		 "menu": ("Set the menu of the party", "A string describing the menu"),
		 "mode": ("Set the main transportation mode of the guests", "A string representing the transportation mode of the guests", ("car", "train", "other")),
		 "distance": ("Set the distance the guests will have to travel", "A floating-points value giving the distance the guests will have to travel, in kilometers"),
		 }

argsTotal = {key: None for dico in args_cat for key in dico}
dicoEmissions = [None] * len(categories)

tools = []

def build_tools():
	for i in range(len(categories)):
		for arg in args_cat[i]:
			d = {
					"type": "function",
					"function": {
						"name": "set_" + arg,
						"description": descr[arg][0],
						"parameters": {
							"type": "object",
							"properties": {
								arg: {
									"type": args_cat[i][arg],
									"description": descr[arg]. If it is not explicitly given, ask the user.",
								},
								"is_veggie": {
									"type": "boolean",
									"description": "A boolean representing whether the meal is vegetarian. If it is not explicitly given, ask the user."
								}
							},
							"required": ["n_guests", "is_veggie"]
						}
			}

def mainloop():
	messages = []
	client = Mistral(api_key = api_key)

