import json
from graph_module import Graph
from utils import *

def generate_comments(graph: Graph, important_graph_info: dict):
    comments = {"Low": [], "Medium": [], "High": []}
    entailment_comments(important_graph_info, comments)
    paragraph_nodes_map_comments(important_graph_info, comments)
    cycle_comments(important_graph_info, comments)
    change_in_node_scores_comments(important_graph_info, comments)
    thesis_node_comments(important_graph_info, comments)
    disconnected_graph_comments(important_graph_info, comments)
    return comments

def entailment_comments(important_graph_info: dict, comments: dict):
    for entailment_component in important_graph_info['entailment_values']:
        relation = entailment_component[4]
        entailment = entailment_component[2]
        source = entailment_component[0]
        target = entailment_component[1]
        comment = entailment_component[3]
        comment.replace("ADU 1", source)
        comment.replace("ADU 2", target)
        if "support" in relation.lower():
            if entailment < 0:
                comments["High"].append(comment)
            elif entailment < 0.5:
                comments["Medium"].append(comment)
            else:
                comments["Low"].append(comment)
        elif "attack" in relation.lower():
            if entailment > 0:
                comments["High"].append(comment)
            elif entailment > -0.5:
                comments["Medium"].append(comment)
            else:
                comments["Low"].append(comment)

def paragraph_nodes_map_comments(important_graph_info: dict, comments: dict):
    for i, paragraph_breakdown in enumerate(important_graph_info['paragraphs']):
        if len(paragraph_breakdown) > 1:
            curr_prompt = paragraph_nodes_map_prompt
            curr_prompt.replace("-(1)-", str(i + 1))
            messages = [
                {"role": "system", "content": curr_prompt}
            ]
            comment = query_gpt(messages, client, gpt4o_mini_model)
            comment += "ADU groupings: " + str(paragraph_breakdown)
            comments["High"].append(comment)

def cycle_comments(important_graph_info: dict, comments: dict):
    for cycle in important_graph_info['cycles']:
        comment = "The essay contains circular logic through the following nodes: " + str(cycle)
        comments["Medium"].append(comment)

def change_in_node_scores_comments(important_graph_info: dict, comments: dict):
    change_in_node_scores = important_graph_info['change_in_node_scores']
    for node_id, score_tuple in change_in_node_scores.items():
        if score_tuple[1] > 0.1:
            comment = f"The score for {node_id} has improved."
            comments["Medium"].append(comment)
        elif score_tuple[1] < -0.1:
            comment = f"The score for {node_id} has decreased."
            comments["Medium"].append(comment)
        else:
            comment = f"The score for {node_id} has remained the same."
            comments["Low"].append(comment)

def thesis_node_comments(important_graph_info: dict, comments: dict):
    thesis_nodes = important_graph_info['thesis_nodes']
    comment = f'''{thesis_nodes} are the ADUs that do not support or attack any other ADUs,
     meaning they are the main points you are making. Typically, this should be your thesis.
     Are these nodes your thesis?'''
    if len(thesis_nodes) > 1:
        comments["High"].append(comment)
    else:
        comments["Medium"].append(comment)

def disconnected_graph_comments(important_graph_info: dict, comments: dict):
    if not important_graph_info['connected']:
        nodes_list = []
        for graph in important_graph_info['components']:
            curr_list = []
            for node in graph['nodes']:
                curr_list.append(node['id'])
            nodes_list.append(curr_list)
        
        nodes_list.sort(key=len)

        comment = '''Parts of the essay are not connected.
        This means that some ADUs are not linked to the rest of the essay.
        The groups of linked ADUs are: ''' + str(nodes_list)
        comments["High"].append(comment)

def central_node_comments(important_graph_info: dict, comments: dict):
    in_deg_central_nodes = important_graph_info['in_deg_central_nodes']
    

# Read in the JSON file
with open('output/important_graph_info.json', 'r') as file:
    important_graph_info = json.load(file)

# Call the generate_comments function
generate_comments(important_graph_info)