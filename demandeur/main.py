import os, json
from mistralai import Mistral
from unidecode import unidecode
import asyncio

api_key = os.environ["MISTRAL_API_KEY"]

model = "mistral-large-latest"

categories = ("Base", "Electricity", "Food", "Transport", "Infrastructure", "Other")
argsCat = (
	{"n_persons": "integer"},
	{"is_inside": "boolean", "n_hours": "integer"},
	{"menu": "string"},
	{"mode": "string", "distance": "number"},
	{},
	{},
)

descr = {
	"n_persons": (
		"Set the number of guests attending the party",
		"Number of guests attending the party",
	),
	"is_inside": (
		"Set whether the party is taking place indoors or outdoors",
		"A boolean that is true if the party is indoors, false if the party is outdoors",
	),
	"n_hours": (
		"Set the estimated length of the party",
		"An integer giving the length of the party, in hours",
	),
	"menu": ("Set the menu of the party", "A string describing the menu. If the user says there will be no food, call this function with the argument 'None'."),
	"mode": (
		"Set the main transportation mode of the guests",
		"A string representing the transportation mode of the guests",
		("train", "bus", "car", "plane", "bike", "other"),
	),
	"distance": (
		"Set the distance the guests will have to travel",
		"A floating-points value giving the distance the guests will have to travel, in kilometers",
	),
}


def set_elec_emissions(is_inside, n_hours, **kw):
	if is_inside:
		return n_hours * 3
	else:
		return 0


def set_food_emissions(menu, n_persons, **kw):
	# Fonction très simple pour le moment
	# A long terme, il faut convertir le menu en CO2 à partir d'Agribalise et de Reasoning AI puis faire le pduit
	return 3 * n_persons


def set_tspt_emissions(mode, distance, n_persons, **kw):
	# mode : train , bike , car, bus, plane
	# dist km
	if mode == "train":
		emission_factor = 10 / 1000  # Average train emissions in france

	elif mode == "bus":
		emission_factor = 100 / 1000  # Average diesel bus

	elif mode == "car":
		# Différents types de voitures
		emission_factor = 192 / 1000  # Average gasoline car

	elif mode == "plane":
		emission_factor = 255 / 1000  # Avion court-courrier

	elif mode == "bike" or mode == "other":
		emission_factor = 0  # Vélo n'émet pas de CO₂

	# Calcul des émissions totales
	total_emissions = emission_factor * distance * n_persons
	return total_emissions


def set_infra_emissions(is_inside, n_hours, **kw):
	if is_inside:
		return (
			n_hours * 3
		)  # 3 correspond aux émissions de CO2 par heure dues au chauffage en intérieur
	else:
		return 0


def set_other_emissions(**kw):
	return 0


class Demandeur:
	def __init__(self):
		self.messages = [
			{"role": "system", "content": ""}
		]
		self.client = Mistral(api_key=api_key)
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
									"description": descr[arg][1]
									+ ".If it is not explicitly given, ask the user; never try to make up a value.",
								},
							},
							"required": [arg],
						},
					},
				}
				if len(descr[arg]) == 3:		# if there is a third value, it's a list giving the possible values for the argument
					d["function"]["parameters"]["properties"][arg]["enum"] = descr[arg][2]
				self.tools.append(d)

	def update_emissions(self, i):
		listFunc = [
			lambda **kwargs: 0,
			set_elec_emissions,
			set_food_emissions,
			set_tspt_emissions,
			set_infra_emissions,
			set_other_emissions,
		]
		self.dicoEmissions[i] = listFunc[i](**self.argsTotal)
		return

	def is_category_complete(self, i):
		return all(self.argsTotal[key] != None for key in argsCat[i])

	def is_category_complete(self, i):
		return all(self.argsTotal[key] != None for key in argsCat[i])
	
	def get_text(self, i):
		if i == 1:
			return "Electricity emissions: length: {n_hours} hours; ".format(**self.argsTotal) + ["out", "in"][self.argsTotal["is_inside"]] + "doors"
		elif i == 2:
			return "Food emissions: menu {menu}".format(**self.argsTotal)
		elif i == 3:
			return "Transport emissions: guests will be using {mode}, on an average distance of {distance} kilometers".format(**self.argsTotal)
		elif i == 4:
			return "Infrastructure emissions: None"
		else:
			return "Other emissions: None"
	
	def get_bilan(self):
		ans = []
		for i in range(1, len(categories)):
			if self.dicoEmissions[i] != None:
				ans.append((i-1, self.get_text(i), self.dicoEmissions[i]))
		
		return ans
	
	def traiter_call(self, call):
		function_name = call.function.name
		function_params = json.loads(call.function.arguments)
		# print(
		# 	"System: bot made function call to",
		# 	function_name,
		# 	"with parameters",
		# 	function_params,
		# )

		arg, val = list(function_params.items())[0]

		print(
			"System: bot updated variable",
			arg,
			"with value",
			val,
			"(type:",
			type(val),
			")\n", flush = True
		)
		self.argsTotal[arg] = val

		self.messages.append(
			{
				"role": "tool",
				"name": function_name,
				"content": "La valeur a bien été mise à jour.",
				"tool_call_id": call.id,
			}
		)

	async def mainloop(self, wait_message, send_message, update_message):
		ans = None

		# premier message pour lancer la conv

		self.messages[0]["content"] = "Tu es un chatbot chargé de calculer les émissions de CO2 liées à l'organisation d'une soirée. Commence par lui demander s'il désire que tu calcules ses émissions de CO2."
		ans = (
				self.client.chat.complete(
					model=model,
					messages=self.messages,
					tools=self.tools,
					tool_choice="auto",
				)
				.choices[0]
				.message
			)
		self.messages.append(ans)

		print ("Bot:", ans.content, '\n')
		if send_message:
			await send_message(unidecode(ans.content))

		if wait_message:
			message = await wait_message()
			print("User:", message, "\n")
		else:
			print ("User: ", end='')
			message = input()
			print()

		self.messages.append({"role": "user", "content": message})

		while None in self.dicoEmissions:
			i = self.dicoEmissions.index(None)

			prompt = "Tu es un chatbot chargé de calculer les émissions de CO2 liées à l'organisation d'une soirée. Il faut que tu demandes à l'utilisateur les informations suivantes :\n"
			for arg in argsCat[i].keys():
				prompt += "- " + descr[arg][1] + "\n"
			prompt += "Ne lui donne jamais le nom précis des paramètres (n_hours), demande à l'utilisateur dans un langage correct.\n"
			prompt += "Si la réponse de l'utilisateur n'est pas claire, insiste pour avoir une réponse précise. N'invente jamais de valeurs."

			self.messages[0]["content"] = prompt
			# print (prompt)

			ans = (
					self.client.chat.complete(
						model=model,
						messages=self.messages,
						tools=self.tools,
						tool_choice="auto",
					)
					.choices[0]
					.message
				)
			self.messages.append(ans)

			
			if ans.tool_calls:
				for call in ans.tool_calls:
					self.traiter_call(call)
			print ("Bot:", ans.content, '\n')
			if send_message:
				await send_message(unidecode(ans.content))

			while not self.is_category_complete(i):
				if ans is None or ans.content == "":
					ans = (
						self.client.chat.complete(
							model=model,
							messages=self.messages,
							tools=self.tools,
							tool_choice="auto",
						)
						.choices[0]
						.message
					)
					self.messages.append(ans)

					print("Bot:", ans.content, "\n")
					if send_message:
						await send_message(unidecode(ans.content))

				if wait_message:
					message = await wait_message()
					print("User:", message, "\n")
				else:
					print ("User: ", end='')
					message = input()
					print()

				self.messages.append({"role": "user", "content": message})

				ans = (
					self.client.chat.complete(
						model=model,
						messages=self.messages,
						tools=self.tools,
						tool_choice="auto",
					)
					.choices[0]
					.message
				)
				self.messages.append(ans)

				# ans = self.client.chat.complete(model = model, messages = self.messages, tools = self.tools, tool_choice = "auto").choices[0].message
				# self.messages.append(ans)

				if ans.tool_calls:
					for call in ans.tool_calls:
						self.traiter_call(call)
				else:
					print("Bot:", ans.content, "\n", flush=True)
					if send_message:
						await send_message(unidecode(ans.content))

				#print(self.messages)

			print("finished category", categories[i], flush = True)

			for j in range(len(categories)):
				if self.is_category_complete(j):
					self.update_emissions(j)

			bilan = self.get_bilan()
			print ("Bilan:", bilan, "\n")
			if update_message:
				await update_message(bilan)

if __name__ == "__main__":
	d = Demandeur()
	asyncio.run(d.mainloop(None, None, None))

	print(d.argsTotal, d.dicoEmissions)


# La fête est dans mon salon ; elle durera 6 heures ; 50 personnes viendront, et parcourront 20 km en train ; nous mangerons du pain et du vin
# 50 personnes viendront ; en intérieur ; elle durera 6 heures