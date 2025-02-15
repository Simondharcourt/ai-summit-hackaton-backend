import os, json
from mistralai import Mistral

api_key = "29NL9Foa83Niu5QLidPK4JMMEwjB7OCx"
model = "mistral-large-latest"

categories = ("Base", "Electricity", "Food", "Transport", "Infrastructure", "Other")
argsCat = ({"n_persons": "integer"}, {"is_inside": "boolean", "n_hours": "integer"}, {"menu": "string"}, {"mode": "string", "distance": "float"}, {}, {})

descr = {"n_persons": ("Set the number of guests attending the party", "Number of guests attending the party"),
		 "is_inside": ("Set whether the party is taking place indoors or outdoors", "A boolean that is true if the party is indoors, false if the party is outdoors"),
		 "n_hours": ("Set the estimated length of the party", "An integer giving the length of the party, in hours"),
		 "menu": ("Set the menu of the party", "A string describing the menu"),
		 "mode": ("Set the main transportation mode of the guests", "A string representing the transportation mode of the guests", ("car", "train", "other")),
		 "distance": ("Set the distance the guests will have to travel", "A floating-points value giving the distance the guests will have to travel, in kilometers"),
		 }

argsTotal = {key: None for dico in argsCat for key in dico}
dicoEmissions = [None] * len(categories)

tools = []

def build_tools():
	for i in range(len(categories)):
		for arg in argsCat[i]:
			d = {
					"type": "function",
					"function": {
						"name": "set_" + arg,
						"description": descr[arg][0],
						"parameters": {
							"type": "object",
							"properties": {
								arg: {
									"type": argsCat[i][arg],
									"description": descr[arg][1] + ".If it is not explicitly given, ask the user; never try to make up a value.",
								},
							},
							"required": [arg]
						}
					}
			}
			tools.append(d)

def mainloop():
	messages = []
	client = Mistral(api_key = api_key)

	build_tools()

	# if context:
	# 	messages.append({"role": "system", "content": context})

	while None in dicoEmissions:
		i = dicoEmissions.index(None)

		messages.append({"role": ""})

		while None in argsTotal[i].values():
			message = input()
		
			messages.append({"role": "user", "content": message})

			print ("User: ", message, '\n')

			ans = client.chat.complete(model = model, messages = messages, tools = tools, tool_choice = "auto").choices[0].message
			#print (ans)
			messages.append(ans)

			while ans.tool_calls:
				for call in ans.tool_calls:
					function_name = call.function.name
					function_params = json.loads(call.function.arguments)
					print ("System: bot made function call to", function_name, "with parameters", function_params)
					
					argsTotal[function_params.k]
					print ("System: result is", res, '\n')

					messages.append({"role":"tool", "name":function_name, "content":str(res), "tool_call_id":call.id})

				ans = client.chat.complete(model = model, messages = messages, tools = tools, tool_choice = "auto").choices[0].message
				messages.append(ans)
			
			if ans.content:
				print ("Bot: ", ans.content, '\n', flush = True)
			else:
				print ("Bot: (silence)\n", flush = True)
	return
	

def set_elec_emissions(is_inside, n_hours, **kw):
	if (is_inside):
		return n_hours*3
	else:
		return 0

def set_food_emissions(menu, nbPers, **kw):
	# Fonction très simple pour le moment
	# A long terme, il faut convertir le menu en CO2 à partir d'Agribalise et de Reasoning AI puis faire le pduit
	return 3*nbPers

def set_tspt_emissions(mode, dist, nbPers, **kw):
	return mode[0]*dist*nbPers


def set_infra_emissions(is_inside, n_hours, **kw):
	if(is_inside):
		return n_hours*3         # 3 correspond aux émissions de CO2 par heure dues au chauffage en intérieur
	else:
		return 0

def set_other_emissions(**kw):
	return 0
	

listFunc = [set_elec_emissions, set_food_emissions, set_tspt_emissions, set_infra_emissions, set_other_emissions]


def update_emissions(i):
	dicoEmissions[i] = listFunc[i](argsTotal)
	return








# def to_text(category, tabArgs, value):
#     text = ""
#     if(category==0):
		

#     return text
