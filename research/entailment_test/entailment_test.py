from graph_data import compile_graph_data
from config import *
import os
import json

def main():
    entailments = {}
    all_files = process_files('../../graph-building-dev/datasets/Synthetic_v2/Annotated_Data/Raw-Text', '../../graph-building-dev/datasets/Synthetic_v2/Annotated_Data/JSON', '../../graph-building-dev/datasets/Synthetic_v2/Generated_Data/JSON')
    for i, (base_filename, gen_data, json_graph, essay) in enumerate(all_files):
        print(base_filename)
        if i >= 10:
            break
        
        important_graph_info = compile_graph_data(json_graph, essay, None)
        entailment_values = [value for (_, _, value) in important_graph_info["entailment_values"]]
        entailment_average = sum(entailment_values) / len(entailment_values) if len(entailment_values) > 0 else 0
        entailments[base_filename] = (gen_data["quality"], entailment_average, important_graph_info["entailment_values"])
    with open('entailments_test_with_added_context.json', 'w') as f:
        json.dump(entailments, f, indent=2)


def process_files(essay_dir, json_graph_dir, gen_data_dir):
    ret = []
    for txt_filename in os.listdir(essay_dir):
        if txt_filename.endswith('.txt'):
            base_filename = os.path.splitext(txt_filename)[0]
            json_filename = base_filename + '.json'
            
            txt_file_path = os.path.join(essay_dir, txt_filename)
            json_graph_file_path = os.path.join(json_graph_dir, json_filename)
            gen_data_file_path = os.path.join(gen_data_dir, json_filename)
            
            with open(txt_file_path, 'r') as txt_file, open(json_graph_file_path, 'r') as json_graph_file, open(gen_data_file_path, 'r') as gen_data_file:
                essay = txt_file.read()
                json_graph = json.load(json_graph_file)
                gen_data = json.load(gen_data_file)

                ret.append((base_filename, gen_data, json_graph, essay))
    return ret

main()