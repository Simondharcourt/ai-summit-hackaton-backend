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
		("train", "bus", "car", "plane", "bike", "public transportation", "other"),
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
	# we should ask the LLM to come up with a list of ingredients, and compute the CO2 cost according to this
	# for now, we just ask it to make up a value, which should hopefully be somewhat accurate
	# when testing, it gave relatively accurate values (7-10 kgeqCO2 for a meal based on beef, 1-2 kgeqCO2 for a vegetarian meal)

	client = Mistral(api_key = api_key)
	messages = [{"role": "system", "content": "On a single line, print the estimated CO2 cost of making the following meal for 10 persons, in equivalent kg CO2. Do not add any commentary, simply print the value on a single line.\n" + menu}]

	ans = (
		client.chat.complete(
			model=model,
			messages=messages,
		)
		.choices[0]
		.message
	)
	
	try:
		val = float(ans.content)
	except:
		val = 0.
	
	return val * n_persons / 10



def set_tspt_emissions(mode, distance, n_persons, **kw):
	# mode : train , bike , car, bus, plane
	# dist km
	if mode == "train":
		emission_factor = 10 / 1000  # Average train emissions in france
	
	elif mode == "public transportation":
		emission_factor = 3 / 1000  # Standard metro emissions in france

	elif mode == "bus":
		emission_factor = 100 / 1000  # Average diesel bus

	elif mode == "car":
		# Différents types de voitures
		emission_factor = 192 / 1000  # Average gasoline car

	elif mode == "plane":
		emission_factor = 255 / 1000  # Average plane emissions

	elif mode == "bike" or mode == "other":
		emission_factor = 0  # No CO2 emissions

	# Calcul des émissions totales
	total_emissions = emission_factor * distance * n_persons
	return total_emissions


def set_infra_emissions(is_inside, n_hours, **kw):
	if is_inside:
		return (
			n_hours * 3
		)  # emissions per hours due to heating if the party is held indoors
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
			s = "Electricity emissions: the party will be " + ["out", "in"][bool(self.argsTotal["is_inside"])] + "doors and will last {n_hours} hours."
		elif i == 2:
			s = "Food emissions: there will be {n_persons} guests, eating {menu}"
		elif i == 3:
			s = "Transport emissions: guests will be using {mode}, on an average distance of {distance} kilometers"
		elif i == 4:
			s = "Infrastructure emissions: the party will be " + ["out", "in"][bool(self.argsTotal["is_inside"])] + "doors and will last {n_hours} hours."
		else:
			s = "Other emissions: None"
		return s.format(**self.argsTotal)
	
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

		#self.messages[0]["content"] = "Tu es un chatbot chargé de calculer les émissions de CO2 liées à l'organisation d'une soirée. Commence par lui demander s'il désire que tu calcules ses émissions de CO2."
		self.messages[0]["content"] = "You are a chatbot responsible for calculating the CO2 emissions related to organizing a party. Start by asking the user if they would like you to calculate their CO2 emissions."

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

			# prompt = "Tu es un chatbot chargé de calculer les émissions de CO2 liées à l'organisation d'une soirée. Il faut que tu demandes à l'utilisateur les informations suivantes :\n"
			# for arg in argsCat[i].keys():
			# 	prompt += "- " + descr[arg][1] + "\n"
			# prompt += "Ne lui donne jamais le nom précis des paramètres (n_hours), demande à l'utilisateur dans un langage correct.\n"
			# prompt += "Si la réponse de l'utilisateur n'est pas claire, insiste pour avoir une réponse précise. N'invente jamais de valeurs."

			prompt = "You are a chatbot responsible for calculating the CO2 emissions related to organizing a party. You need to ask the user for the following information:"
			for arg in argsCat[i].keys():
				prompt += "- " + descr[arg][1] + "\n"
			prompt += "Never give the user the exact parameter names (e.g., n_hours); ask them using natural language."
			prompt += "If the user's response is unclear, insist on getting a precise answer. Never make up values."
			
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