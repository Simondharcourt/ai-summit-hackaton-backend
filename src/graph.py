from langgraph.graph import StateGraph

# Définition de l'état du chatbot
class EveningCarbonState:
    def __init__(self):
        self.reponses = {}
        self.emissions_total = 0.0
        self.nb_personnes = 0

# Création du graphe
graph = StateGraph(EveningCarbonState)

# Node pour poser la question sur le nombre d'invités
def ask_guest_count(state: EveningCarbonState):
    # Ici, le bot poserait la question via l'interface utilisateur (CLI, web, etc.)
    guest_count = int(input("Combien d'invités attendez-vous ? "))
    state.reponses['guests'] = guest_count
    # Exemple de calcul : 5 kg CO₂ par invité
    
    state.update_emission(guest_count * 5)
    return state

graph.add_node("q1_guest_count", ask_guest_count)

# Node pour la question sur le type de repas
def ask_meal_type(state: EveningCarbonState):
    meal_type = input("Quel type de repas sera servi (local/international) ? ").lower().strip()
    state.reponses['meal'] = meal_type
    # Exemple de calcul : +50 kg si international, +20 kg si local
    if meal_type == "international":
        state.update_emission(50)
    else:
        state.update_emission(20)
    return state

graph.add_node("q2_meal_type", ask_meal_type)

# Node pour la question sur le moyen de transport
def ask_transport(state: EveningCarbonState):
    transport = input("Quel moyen de transport sera utilisé pour se rendre à l'événement ? (voiture, transports en commun, vélo, marche) ").lower().strip()
    state.reponses['transport'] = transport
    # Exemple de calcul
    if transport == "voiture":
        state.update_emission(30)
    elif transport == "transports en commun":
        state.update_emission(15)
    # vélo ou marche ne génèrent pas d'émission supplémentaires
    return state

graph.add_node("q3_transport", ask_transport)

# Node pour le calcul final du bilan carbone
def calculate_carbon(state: EveningCarbonState):
    print("\nCalcul du bilan carbone de votre soirée :")
    print("Réponses :", state.reponses)
    print("Total des émissions estimées :", state.emissions_total, "kg CO₂")
    return state

graph.add_node("calculate", calculate_carbon)

# Définir la séquence (edges) du dialogue
graph.set_entry_point("q1_guest_count")
graph.add_edge("q1_guest_count", "q2_meal_type")
graph.add_edge("q2_meal_type", "q3_transport")
graph.add_edge("q3_transport", "calculate")

# Compiler et lancer l'application
app = graph.compile()

if __name__ == "__main__":
    # Initialisation de l'état
    state = EveningCarbonState()
    app.invoke(state)