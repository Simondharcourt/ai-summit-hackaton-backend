from langgraph.graph import StateGraph
from langchain.schema import AIMessage, HumanMessage

# Définition d'un état simple (une liste de messages)
class ChatState:
    def __init__(self, messages=None):
        self.messages = messages or []

# Fonction qui ajoute un message humain
def add_human_message(state: ChatState) -> ChatState:
    state.messages.append(HumanMessage(content="Bonjour, comment vas-tu ?"))
    return state

# Fonction qui génère une réponse IA (simulation)
def generate_ai_response(state: ChatState) -> ChatState:
    state.messages.append(AIMessage(content="Je vais bien, merci !"))
    return state

# Création du graphe
workflow = StateGraph(ChatState)
workflow.add_node("add_human", add_human_message)
workflow.add_node("generate_ai", generate_ai_response)

# Connexion des nœuds
workflow.set_entry_point("add_human")
workflow.add_edge("add_human", "generate_ai")

# Compilation
app = workflow.compile()

# Exécution
state = app.invoke(ChatState())
for msg in state.messages:
    print(f"{msg.type}: {msg.content}")