from __future__ import annotations
from utils import *
from config import *

class Graph:
    def __init__(self, json_graph: JSON_Graph) -> None:
        self.nx_graph = self.json_to_nx_graph(json_graph)
        # self.important_graph_info = {}

    def json_to_nx_graph(self, json_graph: JSON_Graph) -> nx.DiGraph:
        new_graph = nx.DiGraph()

        # make sure it is actually a graph
        if "nodes" not in json_graph or "edges" not in json_graph:
            return new_graph

        for node in json_graph["nodes"]:
            init_score = 0
            if node["id"].startswith("E"):
                init_score = 1
            new_graph.add_node(node["id"], text=node["text"], score=init_score, type=node["type"])
        for edge in json_graph["edges"]:
            new_graph.add_edge(edge["source"], edge["target"], label=edge["label"])

        return new_graph
    
    def nx_graph_to_json(self) -> JSON_Graph:
        json_graph = {"nodes":[], "edges":[]}
        for node, data in self.get_node_ids()(data=True):
            json_graph["nodes"].append({"text":data["text"], "type":data["type"], "id":node, "score":data["score"]})
        for source, target, data in self.nx_graph.edges(data=True):
            json_graph["edges"].append({"label":data["label"], "source":source, "target":target})
        return json_graph
    
    def is_connected(self) -> bool:
        return nx.is_weakly_connected(self.nx_graph)
    
    def get_components(self) -> Generator[Set[Any], None, None]:
        return nx.weakly_connected_components(self.nx_graph)
    
    def get_cycles(self) -> list[list[Node_ID]]:
        return nx.recursive_simple_cycles(self.nx_graph)

    def get_single_cycle(self) -> list[tuple[int, int]]:
        try:
            cycle = nx.find_cycle(self.nx_graph)
            return cycle
        except:
            return None
    
    def add_node(self, node_id: Node_ID, text: str, score: float, type: str) -> None:
        self.nx_graph.add_node(node_id, text=text, score=score, type=type)
    
    def remove_node(self, node_id: Node_ID) -> None:
        self.nx_graph.remove_node(node_id)
    
    def add_edge(self, source: Node_ID, target: Node_ID, label: str) -> None:
        if (source, target) not in self.get_edges():
            self.nx_graph.add_edge(source, target, label=label)

    def remove_edge(self, source: Node_ID, target: Node_ID) -> None:
        self.nx_graph.remove_edge(source, target)
    
    def get_node_ids(self) -> nx.classes.reportviews.NodeView:
        return self.nx_graph.nodes()
    
    def get_node_score(self, node_id: Node_ID) -> float:
        return self.get_node_ids()[node_id]["score"]
    
    def set_node_score(self, node_id: Node_ID, new_score: float) -> None:
        self.get_node_ids()[node_id]["score"] = new_score
    
    def get_node_text(self, node_id: Node_ID) -> str:
        return self.get_node_ids()[node_id]["text"]

    def set_node_text(self, node_id: Node_ID, new_text: str) -> None:
        self.get_node_ids()[node_id]["text"] = new_text

    def get_edges(self) -> list[tuple[Node_ID, Node_ID]]:
        return self.nx_graph.edges()
    
    def get_edge_label(self, edge: tuple[Node_ID, Node_ID]) -> str:
        (source_id, target_id) = edge
        return self.nx_graph.get_edge_data(source_id, target_id)["label"]

    def get_predecessors(self, node_id: Node_ID) -> list[Node_ID]:
        return list(self.nx_graph.predecessors(node_id))
    
    def get_successors(self, node_id: Node_ID) -> list[Node_ID]:
        return list(self.nx_graph.successors(node_id))
    
    # visit_func takes in 2 parameters - a Graph and the current node id
    def breadth_first_traversal(self, visit_func: Callable[[Graph, Node_ID, dict], None], other_params: dict) -> None:
        root_nodes = self.get_root_node_ids()
        num_parents_list = self.make_num_parents_list()

        queue = Queue()
        # starter queue
        for node in root_nodes:
            queue.put(node)

        # not keeping track of visited because allowed to visit multiple times
        # need to find way to keep track of loops
        while not queue.empty():
            curr_node_id = str(queue.get())
            num_parents_list[curr_node_id] -= 1

            # only continue on if every edge pointing to the current node has been
            # covered, meaning that the node has its final score
            if num_parents_list[curr_node_id] <= 0:
                for node_id in self.get_successors(curr_node_id):
                    queue.put(node_id)
                visit_func(self, curr_node_id, other_params)

    def get_root_node_ids(self) -> list[Node_ID]:
        return [node for node in self.get_node_ids() if self.nx_graph.in_degree(node) == 0]
    
    def make_num_parents_list(self) -> dict[Node_ID, int]:
        num_parents_list = {}
        for node_id in self.get_node_ids():
            num_parents_list[node_id] = len(self.get_predecessors(node_id))
        
        return num_parents_list
    
    # these nodes are important and (in theory) have lots of backing
    def get_in_deg_central_node_ids(self):
        top_x_percent_central = 20

        centrality = list(nx.in_degree_centrality(self.nx_graph).items())
        centrality.sort(key=(lambda x: x[1]))
        most_central = centrality[round((100 - top_x_percent_central) / 100 * len(centrality)):]
        most_central = [(x[0], round(x[1], 2)) for x in most_central]
        return most_central
    
    # these nodes are important for proving lots of other nodes
    def get_out_deg_central_node_ids(self):
        top_x_percent_central = 20

        centrality = list(nx.out_degree_centrality(self.nx_graph).items())
        centrality.sort(key=(lambda x: x[1]))
        most_central = centrality[round((100 - top_x_percent_central) / 100 * len(centrality)):]
        most_central = [(x[0], round(x[1], 2)) for x in most_central]
        return most_central