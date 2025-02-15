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

class Demandeur:
    def __init__(self):
        self.messages = [{"role": "system", "content": ""}]
        self.client = Mistral(api_key = api_key)
        self.argsTotal = {key: None for dico in argsCat for key in dico}
        self.dicoEmissions = [None] * len(categories)
        self.dicoEmissions[4] = 0
        self.dicoEmissions[5] = 0

        self.tools = []

        self.build_tools()

    def build_tools(self):
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
                self.tools.append(d)

    def update_emissions(self, i):
        self.dicoEmissions[i] = listFunc[i](self.argsTotal)
        return


    def is_category_complete(self, i):
        return all(self.argsTotal[key] != None for key in argsCat[i])

    def is_category_complete(self, i):
        return all(self.argsTotal[key] != None for key in argsCat[i])

    def mainloop(self, fn):
        if None in self.dicoEmissions:
            i = self.dicoEmissions.index(None)

            self.messages[0]["content"] = "Il faut que tu demandes à l'utilisateur les valeurs des paramètres " + ", ".join(argsCat[i].keys())


            ans = self.client.chat.complete(model = model, messages = self.messages, tools = self.tools, tool_choice = "auto").choices[0].message
            self.messages.append(ans)

            print ("Bot:", ans.content, '\n')

            while not self.is_category_complete(i):
                message = input()
            
                self.messages.append({"role": "user", "content": message})

                print ("User:", message, '\n')

                ans = self.client.chat.complete(model = model, messages = self.messages, tools = self.tools, tool_choice = "auto").choices[0].message
                #print (ans)
                self.messages.append(ans)

                while ans.tool_calls:
                    for call in ans.tool_calls:
                        function_name = call.function.name
                        function_params = json.loads(call.function.arguments)
                        # print ("System: bot made function call to", function_name, "with parameters", function_params)
                        
                        arg, val = list(function_params.items())[0]

                        print ("System: bot updated variable", arg, "with value", val, "(type:", type(val), ")\n")
                        self.argsTotal[arg] = val

                        self.messages.append({"role":"tool", "name":function_name, "content":"", "tool_call_id":call.id})

                    ans = self.client.chat.complete(model = model, messages = self.messages, tools = self.tools, tool_choice = "auto").choices[0].message
                    self.messages.append(ans)
                
                if isinstance(ans.content, str):
                    print ("Bot:", ans.content, '\n', flush = True)

                print (self.messages)

            print ("finished category", i)

            for j in range(len(categories)):
                if self.is_category_complete(j):
                    self.update_emissions(j)

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
	#mode : train , bike , car, bus, plane
	#dist km
	if mode == "train":
		# Différents types de train
		train_type = input("Type de train (TGV, Intercités, TER) : ").strip().lower()
		if train_type == "tgv":
			emission_factor = 1.73 / 1000  # TGV
		elif train_type == "intercités":
			emission_factor = 10 / 1000  # Intercités
		elif train_type == "ter":
			emission_factor = 30 / 1000  # TER
	  
	
	elif mode == "bus":
		# Différents types de bus
		bus_type = input("Type de bus (urbain, longue distance, électrique) : ").strip().lower()
		if bus_type == "urbain":
			emission_factor = 100 / 1000  # Bus urbain diesel
		elif bus_type == "longue distance":
			emission_factor = 70 / 1000  # Bus longue distance
		elif bus_type == "électrique":
			emission_factor = 15 / 1000  # Bus urbain électrique
	
	elif mode == "car":
		# Différents types de voitures
		car_type = input("Type de voiture (essence, diesel, électrique) : ").strip().lower()
		if car_type == "essence":
			emission_factor = 192 / 1000  # Voiture essence moyenne
		elif car_type == "diesel":
			emission_factor = 171 / 1000  # Voiture diesel
		elif car_type == "électrique":
			emission_factor = 20 / 1000  # Voiture électrique (mix électrique France)
	
	
	elif mode == "plane":
		emission_factor = 255 / 1000  # Avion court-courrier
	
	elif mode == "bike":
		emission_factor = 0  # Vélo n'émet pas de CO₂

	
	# Calcul des émissions totales
	total_emissions = emission_factor * dist * nbPers
	return total_emissions

def set_infra_emissions(is_inside, n_hours, **kw):
    if(is_inside):
        return n_hours*3         # 3 correspond aux émissions de CO2 par heure dues au chauffage en intérieur
    else:
        return 0

def set_other_emissions(**kw):
    return 0
    

listFunc = [lambda **kwargs: 0, set_elec_emissions, set_food_emissions, set_tspt_emissions, set_infra_emissions, set_other_emissions]


def update_emissions(i):
	dicoEmissions[i] = listFunc[i](argsTotal)
	return


def is_category_complete(i):
	return all(argsTotal[key] != None for key in argsCat[i])

def is_category_complete(i):
	return all(argsTotal[key] != None for key in argsCat[i])



# def to_text(category, tabArgs, value):
#     text = ""
#     if(category==0):
        

#     return text

# def mainloop():
#     messages = []
#     client = Mistral(api_key = api_key)

#     messages.append({"role": "system", "content": ""})

#     build_tools()

#     # if context:
#     # 	messages.append({"role": "system", "content": context})

#     while None in dicoEmissions:
#         i = dicoEmissions.index(None)

		if not argsCat[i]:
			dicoEmissions[i] = 0
			continue
		
		prompt = "Tu es un chatbot chargé de calculer les émissions de CO2 liées à l'organisation d'une soirée. Il faut que tu demandes à l'utilisateur les valeurs des paramètres suivants :\n"
		for arg in argsCat[i].keys():
			prompt += arg + ' : ' + descr[arg][1]
		messages[0]["content"] = prompt

		print ("prompt", prompt)

#         ans = client.chat.complete(model = model, messages = messages, tools = tools, tool_choice = "auto").choices[0].message
#         messages.append(ans)

#         print ("Bot:", ans.content, '\n')

#         while not is_category_complete(i):
#             message = input()
        
#             messages.append({"role": "user", "content": message})

#             print ("User:", message, '\n')

#             ans = client.chat.complete(model = model, messages = messages, tools = tools, tool_choice = "auto").choices[0].message
#             #print (ans)
#             messages.append(ans)

#             while ans.tool_calls:
#                 for call in ans.tool_calls:
#                     function_name = call.function.name
#                     function_params = json.loads(call.function.arguments)
#                     # print ("System: bot made function call to", function_name, "with parameters", function_params)
                    
#                     arg, val = list(function_params.items())[0]

#                     print ("System: bot updated variable", arg, "with value", val, "(type:", type(val), ")\n")
#                     argsTotal[arg] = val

#                     messages.append({"role":"tool", "name":function_name, "content":"", "tool_call_id":call.id})

#                 ans = client.chat.complete(model = model, messages = messages, tools = tools, tool_choice = "auto").choices[0].message
#                 messages.append(ans)
            
#             if isinstance(ans.content, str):
#                 print ("Bot:", ans.content, '\n', flush = True)

#             print (messages)

#         print ("finished category", i)

#         for j in range(len(categories)):
#             if is_category_complete(j):
#                 update_emissions(j)

# # mainloop()

# print (argsTotal)
# print (dicoEmissions)

# La fête est en extérieur ; elle durera 6 heures ; 50 personnes viendront, et parcourront 20 km en train ; nous mangerons du pain et du vin