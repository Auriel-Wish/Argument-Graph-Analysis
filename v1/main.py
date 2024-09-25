from graph_data import compile_graph_data
from config import *
import json

# json_graph_fpath and essay_fpath are required
# prev_essay_json_graph_fpath should be included if you want to compare
# with the previous essay. Otherwise, it should be None
def main(json_graph_fpath: str, essay_fpath: str, prev_essay_json_graph_fpath: str):
    with open(json_graph_fpath, 'r') as json_graph_file, open(essay_fpath, 'r') as essay_file:
        json_graph = json.load(json_graph_file)
        prev_essay_json_graph = json.load(prev_essay_json_graph_fpath) if prev_essay_json_graph_fpath else None
        essay = essay_file.read()
        important_graph_info = compile_graph_data(json_graph, essay, prev_essay_json_graph)
        # TODO: Make comments with important graph info