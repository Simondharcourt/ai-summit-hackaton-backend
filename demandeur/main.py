import os, json
from mistralai import Mistral

api_key = open("demandeur/api_key.txt").read()

model = "mistral-large-latest"

categories = ("Base", "Electricity", "Food", "Transport", "Infrastructure", "Other")
argsCat = ({"n_persons": "integer"}, {"is_inside": "boolean", "n_hours": "integer"}, {"menu": "string"}, {"mode": "string", "distance": "number"}, {}, {})

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
	# mode: "train", "bus", "car", "avion", "bike"
	# dist: km / personne
	# nb personne
	if mode ==  "train":
		return dist * nbPers * 1.73e-3


def set_infra_emissions(is_inside, n_hours):
	if(is_inside):
		return n_hours*3         # 3 correspond aux émissions de CO2 par heure dues au chauffage en intérieur
	else:
		return 0

def set_other_emissions():
	return 0
	

listFunc = [set_elec_emissions, set_food_emissions, set_tspt_emissions, set_infra_emissions]

def update_emissions(i):

	dicoEmissions[i] = 1
	return


def is_category_complete(i):
	return all(argsTotal[key] != None for key in argsCat[i])



# def to_text(category, tabArgs, value):
#     text = ""
#     if(category==0):
		

#     return text

def mainloop():
	messages = []
	client = Mistral(api_key = api_key)

	messages.append({"role": "system", "content": ""})

	build_tools()

	# if context:
	# 	messages.append({"role": "system", "content": context})

	while None in dicoEmissions:
		i = dicoEmissions.index(None)

		if not argsCat[i]:
			dicoEmissions[i] = 0
			continue

		messages[0]["content"] = "Il faut que tu demandes à l'utilisateur les valeurs des paramètres " + ", ".join(argsCat[i].keys())

		ans = client.chat.complete(model = model, messages = messages, tools = tools, tool_choice = "auto").choices[0].message
		messages.append(ans)

		print ("Bot:", ans.content, '\n')

		while not is_category_complete(i):
			message = input()
		
			messages.append({"role": "user", "content": message})

			print ("User:", message, '\n')

			ans = client.chat.complete(model = model, messages = messages, tools = tools, tool_choice = "auto").choices[0].message
			#print (ans)
			messages.append(ans)

			while ans.tool_calls:
				for call in ans.tool_calls:
					function_name = call.function.name
					function_params = json.loads(call.function.arguments)
					# print ("System: bot made function call to", function_name, "with parameters", function_params)
					
					arg, val = list(function_params.items())[0]

					print ("System: bot updated variable", arg, "with value", val, "(type:", type(val), ")\n")
					argsTotal[arg] = val

					messages.append({"role":"tool", "name":function_name, "content":"", "tool_call_id":call.id})

				ans = client.chat.complete(model = model, messages = messages, tools = tools, tool_choice = "auto").choices[0].message
				messages.append(ans)
			
			if isinstance(ans.content, str):
				print ("Bot:", ans.content, '\n', flush = True)

			print (messages)

		print ("finished category", i)

		for j in range(len(categories)):
			if is_category_complete(j):
				update_emissions(j)

mainloop()

print (argsTotal)
print (dicoEmissions)

# La fête est en extérieur ; elle durera 6 heures ; 50 personnes viendront, et parcourront 20 km en train ; nous mangerons du pain et du vin