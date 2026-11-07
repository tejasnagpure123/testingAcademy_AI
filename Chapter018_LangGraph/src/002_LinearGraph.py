"""Three nodes in a row, like a test's setup -> execute-> teardown.
Each node returns a partial update. Keys it does not return are left alone.
Stream_mode="updates" shows you exactly what each node changed, step by step
"""

""" 
Setup changed -> {"browser" : "Chromium"}
Execute changed ->{"Status ":"Passed"}
Teardown changed ->{"Cleaned_up": True}
"""

from typing import TypedDict
from langgraph.graph import END, START, StateGraph


class State(TypedDict, total=False):
    test_name: str
    browser: str
    status: str
    cleaned_up: bool


def setup(state: State) -> dict:
    return {"browser": "Chromium"}


def execute(state: State) -> dict:
    return {"status": "Passed"}


def teardown(state: State) -> dict:
    return {"cleaned_up": True}


builder = StateGraph(State)
builder.add_node("setup", setup)
builder.add_node("execute", execute)
builder.add_node("teardown", teardown)
builder.add_edge(START, "setup")
builder.add_edge("setup", "execute")
builder.add_edge("execute", "teardown")
builder.add_edge("teardown", END)

app = builder.compile()

if __name__ == "__main__":
    result = app.invoke({"test_name": "Linear graph"})
    print("\nFinal state:", result)
    print("\nThe graph as Mermaid (paste into mermaid.live):")
    print(app.get_graph().draw_mermaid())
