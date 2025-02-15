from typing import Annotated, Dict, TypedDict
from langgraph.graph import Graph
from langchain.schema import BaseMessage, HumanMessage
from langchain_core.messages import AIMessage

def create_chat_graph() -> Graph:
    # Définition du type d'état
    class ChatState(TypedDict):
        messages: list[BaseMessage]

    # Fonctions du graphe
    def user_input(state: ChatState) -> ChatState:
        return state
    
    def llm_response(state: ChatState) -> ChatState:
        messages = state.get("messages", [])
        response = "Example response"
        messages.append(AIMessage(content=response))
        return {"messages": messages}
    
    def print_message(state: ChatState) -> ChatState:
        if state["messages"]:
            print("Message reçu:", state["messages"][-1].content)
        return state

    # Construction du graphe
    workflow = Graph()
    
    workflow.add_node("user_input", user_input)
    workflow.add_node("llm_response", llm_response)
    workflow.add_node("print", print_message)
    
    workflow.set_entry_point("user_input")
    workflow.add_edge("user_input", "llm_response")
    workflow.add_edge("llm_response", "print")
    
    return workflow

# Création et compilation
graph = create_chat_graph()
app = graph.compile()
print("Graph LangGraph prêt à l'emploi !")