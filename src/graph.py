from langgraph.graph import StateGraph

# Définition de l'état du graphe
class MyState:
    def __init__(self, message: str):
        self.message = message

# Création du graphe
graph = StateGraph(MyState)

# Ajout d'un nœud
def print_message(state: MyState):
    print("Message reçu:", state.message)
    return state

graph.add_node("affichage", print_message)
graph.set_entry_point("affichage")

# Compilation
app = graph.compile()
print("Graph LangGraph prêt à l'emploi !")