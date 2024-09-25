import json
import graphviz
import glob
from config import output_folder

for fpath in glob.glob(output_folder + "/*"):
    fname = fpath.split('/')[-1].split('.')[0]
    if fpath.endswith('json') and "out" in fname:
        with open(fpath, 'r') as f:
            # Load the JSON data
            graph_data = json.loads(f.read())

            # Create a Graphviz Digraph
            dot = graphviz.Digraph()

            # Add nodes to the Digraph
            for node in graph_data['nodes']:
                dot.node(node["id"], label=(node["text"] + "\n" + node["type"].upper() + "\n" + str(node["score"])))

            # Add edges to the Digraph
            for edge in graph_data['edges']:
                source_id = edge["source"]
                target_id = edge["target"]
                dot.edge(source_id, target_id, label=edge["label"])

            # Render the graph to a file
            dot.render(output_folder + "/" + fname + "_visual", format='png', cleanup=True)