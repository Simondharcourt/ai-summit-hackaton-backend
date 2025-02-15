from src.graph import app, MyState

state = MyState("Hello, LangGraph!")
app.invoke(state)