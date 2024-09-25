from utils import *
from graph_module import *
from ast import literal_eval

def compile_graph_data(json_graph, essay, prev_essay_json_graph) -> None:
    prev_essay_absolute_score_json_graph = None

    important_graph_info = {}
    full_consistency_graph = Graph(json_graph)
    print("Graph Imported")

    full_consistency_graph = initialize_scores(full_consistency_graph)

    ensure_paragraph_clusters(essay, full_consistency_graph, important_graph_info)
    print("Node-to-Paragraph breakdown complete")

    # Make sure the ADUs have context incorporated into them to improve entailment measurements
    fill_in_context(full_consistency_graph, essay)
    print("Added Context to Nodes")
    json_to_file(graph_with_context_fpath, full_consistency_graph.nx_graph_to_json())

    document_cycles(full_consistency_graph, important_graph_info)
    print("Cycles Checked")

    absolute_score_graph = copy.deepcopy(full_consistency_graph)

    full_consistency_graph.breadth_first_traversal(propagate_max_score, None)
    print("Full Consistency Graph Made")

    important_graph_info["entailment_values"] = []
    other_params = {"important_graph_info":important_graph_info}
    absolute_score_graph.breadth_first_traversal(propagate_actual_score, other_params)
    print("Absolute Score Graph Made")

    normalized_graph = copy.deepcopy(absolute_score_graph)
    normalize_graph(absolute_score_graph, full_consistency_graph, normalized_graph)
    print("Normalized Graph Made")

    important_graph_info["change_in_node_scores"] = {}
    important_graph_info["nodes_added"] = []
    important_graph_info["nodes_removed"] = []
    if prev_essay_json_graph:
        prev_essay_graph = Graph(prev_essay_absolute_score_json_graph)
        # compare the absolute scores to see if the arguments have gotten stronger or weaker.
        # the normalized graph is only useful to show how well the current graph is compared to
        # how it could be.
        compare_curr_and_prev_essays(prev_essay_graph, absolute_score_graph, important_graph_info)
        print("Compared Current and Previous Versions")

    document_thesis_nodes(normalized_graph, important_graph_info)
    print("Thesis Nodes Documented")
    document_connectivity(normalized_graph, important_graph_info)
    print("Connectivity Documented")
    document_central_nodes(normalized_graph, important_graph_info)
    print("Central Nodes Documented")
    document_richness(normalized_graph, normalized_graph.make_num_parents_list(), important_graph_info)
    print("Richness Documented")
    json_to_file(important_graph_info_fpath, important_graph_info)

    # output the graphs
    full_consistency_json_graph = full_consistency_graph.nx_graph_to_json()
    absolute_score_json_graph = absolute_score_graph.nx_graph_to_json()
    normalized_json_graph = normalized_graph.nx_graph_to_json()
    json_to_file(full_consistency_output_fpath, full_consistency_json_graph)
    json_to_file(absolute_score_output_fpath, absolute_score_json_graph)
    json_to_file(normalized_output_fpath, normalized_json_graph)
    print("Final Graphs Outputted")
    return important_graph_info

def initialize_scores(graph: Graph) -> None:
    for node_id in graph.get_node_ids():
        if node_id.startswith('E'):
            graph.set_node_score(node_id, 1)
        elif node_id.startswith('N'):
            graph.set_node_score(node_id, 0)
    return graph

def document_thesis_nodes(graph: Graph, important_graph_info: dict) -> None:
    thesis_nodes = []
    for node_id in graph.get_node_ids():
        if graph.get_successors(node_id) == []:
            thesis_nodes.append(node_id)
    important_graph_info["thesis_nodes"] = thesis_nodes

def make_paragraph_node_correspondence(essay: str, graph: Graph) -> tuple[dict, list[Node_ID]]:
    paragraphs = [remove_capitalization_and_punctuation(paragraph) for paragraph in essay.split('\n') if paragraph.strip()]
    
    paragraph_nodes_map = {}
    unable_to_find_paragraph_nodes = []
    for paragraph in paragraphs:
        paragraph_nodes_map[paragraph] = []

    for node_id in graph.get_node_ids():
        if not node_id.startswith('E'):
            node_text = remove_capitalization_and_punctuation(graph.get_node_text(node_id))
            found = False

            for paragraph in paragraphs:
                if node_text in paragraph:
                    paragraph_nodes_map[paragraph].append(node_id)
                    found = True
            if not found:
                unable_to_find_paragraph_nodes.append(node_id)
        
    all_node_ids = set()
    # Iterate through each paragraph and its node_ids
    for paragraph, node_ids in paragraph_nodes_map.items():
        # Create a new list to store non-overlapping node_ids
        unique_node_ids = []
        for node_id in node_ids:
            if node_id not in all_node_ids:
                unique_node_ids.append(node_id)
                all_node_ids.add(node_id)
        # Update the dictionary with the unique node_ids
        paragraph_nodes_map[paragraph] = unique_node_ids
    
    return (paragraph_nodes_map, unable_to_find_paragraph_nodes)

def ensure_paragraph_clusters(essay: str, graph: Graph, important_graph_info: dict) -> None:
    (paragraph_nodes_map, unable_to_find_paragraph_nodes) = make_paragraph_node_correspondence(essay, graph)
    for paragraph, curr_node_ids_list in paragraph_nodes_map.items():
        curr_paragraph_breakdown = []
        while len(curr_node_ids_list) != 0:
            curr_section_of_paragraph = []
            to_visit = [curr_node_ids_list.pop()]
            while len(to_visit) != 0:
                curr_node_id = to_visit.pop()
                curr_section_of_paragraph.append(curr_node_id)
                for child_id in graph.get_successors(curr_node_id):
                    if child_id in curr_node_ids_list:
                        curr_node_ids_list.remove(child_id)
                        to_visit.append(child_id)
                for parent_id in graph.get_predecessors(curr_node_id):
                    if parent_id in curr_node_ids_list:
                        curr_node_ids_list.remove(parent_id)
                        to_visit.append(parent_id)
            curr_paragraph_breakdown.append(curr_section_of_paragraph)
        paragraph_nodes_map[paragraph] = curr_paragraph_breakdown
    
    important_graph_info["paragraph_nodes_map"] = paragraph_nodes_map
    important_graph_info["unable_to_find_paragraph_nodes"] = unable_to_find_paragraph_nodes

def compare_curr_and_prev_essays(prev_essay_graph: Graph, curr_essay_graph: Graph, important_graph_info: dict) -> None:
    change_in_node_scores = {}
    nodes_removed = []
    nodes_added = []
    for prev_essay_node_id in prev_essay_graph.get_node_ids():
        matching_node = False
        prev_essay_node_text = prev_essay_graph.get_node_text(prev_essay_node_id)
        for curr_essay_node_id in curr_essay_graph.get_node_ids():
            curr_essay_node_text = curr_essay_graph.get_node_text(curr_essay_node_id)
            if text_matches(prev_essay_node_text, curr_essay_node_text):
                score_change = curr_essay_graph.get_node_score(curr_essay_node_id) - prev_essay_graph.get_node_score(prev_essay_node_id)
                change_to_add_to_dict = {"node_id_in_prev_essay_graph":prev_essay_node_id, "score_change":score_change}
                change_in_node_scores[curr_essay_node_id] = change_to_add_to_dict
                matching_node = True
                break
        if not matching_node:
            nodes_removed.append(prev_essay_node_id)
    
    for curr_essay_node_id in curr_essay_graph.get_node_ids():
        matching_node = False
        curr_essay_node_text = curr_essay_graph.get_node_text(curr_essay_node_id)
        for prev_essay_node_id in prev_essay_graph.get_node_ids():
            prev_essay_node_text = prev_essay_graph.get_node_text(prev_essay_node_id)
            if text_matches(prev_essay_node_text, curr_essay_node_text):
                matching_node = True
                break
        if not matching_node:
            nodes_added.append(curr_essay_node_id)
    important_graph_info["change_in_node_scores"] = change_in_node_scores
    important_graph_info["nodes_added"] = nodes_added
    important_graph_info["nodes_removed"] = nodes_removed
        
def document_connectivity(graph: Graph, important_graph_info: dict) -> None:
    if graph.is_connected():
        important_graph_info["connected"] = True
        important_graph_info["components"] = graph.nx_graph_to_json()
    else:
        important_graph_info["connected"] = False
        important_graph_info["components"] = []
        for component in graph.get_components():
            subgraph = Graph({"nodes":[], "edges":[]})
            subgraph.nx_graph = graph.nx_graph.subgraph(component)
            important_graph_info["components"].append(subgraph.nx_graph_to_json())

# the strategy used to deal with cycles essentially combines the cycle nodes
# into one big blob of a node. This allows for propagation to not be looped.
# it adds all incoming and outgoing edges to/from that single cycle node.
# this runs into the issue of, if some of those edges are support and some are
# attack, only the first one seen will be chosen (because it is not allowed
# for there to be a support and attack edge with the same source and target
# since that makes no sense)
def document_cycles(graph: Graph, important_graph_info: dict) -> None:
    curr_cycle = graph.get_single_cycle()

    if curr_cycle:
        cycle_list = graph.get_cycles()
        important_graph_info["cycles"] = cycle_list
    else:
        important_graph_info["cycles"] = []

    score = 0
    ADU_type = "N/A"
    id = 0

    while curr_cycle != None:
        edges_to_add = set()
        edges_to_remove = set()
        id += 1
        new_id = "C" + str(id)
        text = ""
        for (node_id, _) in curr_cycle:
            text += (graph.get_node_text(node_id) + "\n")
            for parent in graph.get_predecessors(node_id):
                if node_in_cycle(curr_cycle, parent):
                    edges_to_remove.add((parent, node_id))
                else:
                    edge_label = graph.get_edge_label((parent, node_id))
                    edges_to_add.add((parent, new_id, edge_label))
            for child in graph.get_successors(node_id):
                if node_in_cycle(curr_cycle, child):
                    edges_to_remove.add((node_id, child))
                else:
                    edge_label = graph.get_edge_label((node_id, child))
                    edges_to_add.add((new_id, child, edge_label))
        
        for (source, target) in edges_to_remove:
            graph.remove_edge(source, target)

        for (node_id, _) in curr_cycle:
            graph.remove_node(node_id)
        
        graph.add_node(new_id, text, score, ADU_type)

        for (source, target, edge_label) in edges_to_add:
            graph.add_edge(source, target, edge_label)

        curr_cycle = graph.get_single_cycle()

def node_in_cycle(cycle: list[tuple[int, int]], node_id: Node_ID) -> bool:
    for (source, target) in cycle:
        if source == node_id or target == node_id:
            return True
    return False

def document_central_nodes(graph: Graph, important_graph_info: dict) -> None:
    important_graph_info["in_deg_central_nodes"] = graph.get_in_deg_central_node_ids()
    important_graph_info["out_deg_central_nodes"] = graph.get_out_deg_central_node_ids()

def document_richness(graph: Graph, num_parents_list: dict[Node_ID, int], important_graph_info: dict) -> None:
    node_involvement_score = node_involvement(num_parents_list)
    edge_diversity_score = edge_diversity(graph)
    important_graph_info["node_involvement"] = round(node_involvement_score, 2)
    important_graph_info["edge_diversity"] = round(edge_diversity_score, 2)
    # important_graph_info["richness"] = round(node_involvement_score * edge_diversity_score, 2)

def node_involvement(num_parents_list: dict[Node_ID, int]) -> float:
    sum = float(0)
    num_nodes = len(num_parents_list)
    for node_id in num_parents_list:
        sum += (num_parents_list[node_id] / num_nodes)
    return sum / num_nodes

def edge_diversity(graph: Graph) -> float:
    support = 0
    attack = 0

    for edge in graph.get_edges():
        curr_label = graph.get_edge_label(edge)
        if curr_label == "support":
            support += 1
        if curr_label == "attack":
            attack += 1
    return (2 * min(support, attack)) / (support + attack)

def normalize_graph(absolute_score_graph: Graph, full_consistency_graph: Graph, normalized_graph: Graph) -> None:
    for node_id in normalized_graph.get_node_ids():
        full_consistency_node_score = full_consistency_graph.get_node_score(node_id)
        absolute_node_score = absolute_score_graph.get_node_score(node_id)   

        new_score = maintain_sign(absolute_node_score, round((absolute_node_score / full_consistency_node_score if full_consistency_node_score != 0 else 0), 3))
        normalized_graph.set_node_score(node_id, new_score)

def propagate_actual_score(absolute_score_graph: Graph, parent_id: Node_ID, other_params: dict) -> None:
    important_graph_info = other_params["important_graph_info"]
    for child_id in absolute_score_graph.get_successors(parent_id):
        relation = absolute_score_graph.get_edge_label((parent_id, child_id))
        entailment, reason = determine_entailment(absolute_score_graph, parent_id, child_id)
        if entailment < 0.1 and entailment > -0.1:
            entailment = 0
        important_graph_info["entailment_values"].append((parent_id, child_id, entailment, reason, relation))
        add_score(absolute_score_graph, parent_id, child_id, entailment)

def determine_entailment(absolute_score_graph: Graph, parent_id: Node_ID, child_id: Node_ID) -> float:
    messages = [
        {"role": "system", "content": entailment_prompt},
        {"role": "user", "content": "ADU 1: " + absolute_score_graph.get_node_text(parent_id)},
        {"role": "user", "content": "ADU 2: " + absolute_score_graph.get_node_text(child_id)}
    ]
    output = query_gpt(messages, client, gpt4o_mini_model)
    print(output)

    return literal_eval(output)

def propagate_max_score(full_consistency_graph: Graph, parent_id: Node_ID, other_params: dict) -> None:
    entailment = 1
    for child_id in full_consistency_graph.get_successors(parent_id):
        add_score(full_consistency_graph, parent_id, child_id, entailment)

def fill_in_context(full_consistency_graph: Graph, essay: str) -> None:
    messages = [
        {"role": "system", "content": fill_in_context_prompt},
        {"role": "user", "content": "Essay: " + essay}
    ]
    for node_id in full_consistency_graph.get_node_ids():
        messages.append({"role": "user", "content": node_id + ":" + full_consistency_graph.get_node_text(node_id)})
    new_ADUs = strip_json(query_gpt(messages, client, gpt4o_mini_model))
    # print(new_ADUs)
    new_ADUs = json.loads(new_ADUs)
    for node_id in new_ADUs:
        full_consistency_graph.set_node_text(node_id, new_ADUs[node_id])