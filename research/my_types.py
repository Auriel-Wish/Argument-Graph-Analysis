from typing import TypedDict, List, NewType, Callable, Generator, Set, Any

Node_ID = NewType('Node_ID', str)

class Node(TypedDict):
    id: Node_ID
    text: str
    type: str
    score: float

class Edge(TypedDict):
    label: str
    source: Node_ID
    target: Node_ID

class JSON_Graph(TypedDict):
    nodes: List[Node]
    edges: List[Edge]