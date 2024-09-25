from config import *
import graph_module
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize 
import string

# entailment [-1, 1]
    # the more positive, the more correct the assigned relation is.
    # ex - if the assigned relation is supports and the entailment is 1, then
    # parent clearly supports child
    # ex - if the assigned relation is supports and the entailment is -0.5, then
    # parent somewhat attacks child
    # ex - if the assigned relation is attacks and the entailment is 1, then
    # parent clearly attacks child
    # ex - if the assigned relation is attacks and the entailment is -0.5, then
    # parent somewhat supports child
# parent score should never be allowed to be negative because the point of entailment
# is how does the parent affect the child ASSUMING THAT THE PARENT IS TRUE. If the parent
# is false, then we don't know how that would impact the child.
#
# Ex - if you attack a counter argument and prove it false (-1), that does not
# prove the original argument to be more true, it only proves that the counter argument
# does not prove the original argument to be false.
#
# Ex - if you support a thesis but the support turns out to be false (-1), that does not
# prove the thesis to be false, it only proves that the support does not prove the thesis
# to be true.
def add_score(curr_graph: graph_module.Graph, parent_id: Node_ID, child_id: Node_ID, entailment: float) -> None:
    if entailment < -1: entailment = -1
    if entailment > 1: entailment = 1

    parent_score = curr_graph.get_node_score(parent_id)
    if parent_score < 0: parent_score = 0
    child_score = curr_graph.get_node_score(child_id)
    curr_graph.set_node_score(child_id, round(child_score + parent_score * entailment, 3))

def json_to_file(fpath: str, json_dict: dict) -> None:
    with open(fpath, "w") as f:
        f.write(json.dumps(json_dict, indent=2))

def is_negative(num: float) -> bool:
    return num < 0

def maintain_sign(num_to_use_sign: float, num: float) -> float:
    if is_negative(num_to_use_sign):
        return abs(num) * -1
    else:
        return abs(num)

def query_gpt(messages, client, model):
    completion = client.chat.completions.create(
        model=model,
        messages=messages
    )
    return completion.choices[0].message.content

def strip_json(graph):
    return graph[graph.find('{') : graph.rfind('}') + 1]

def strip_array(arr):
    return arr[arr.find('[') : arr.rfind(']') + 1]

def remove_capitalization_and_punctuation(text: str) -> str:
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    return text

def text_matches(pred, ref):
    THRESHOLD = 0.75

    # tokenization 
    pred_list = word_tokenize(pred)  
    ref_list = word_tokenize(ref) 
    
    # sw contains the list of stopwords 
    sw = stopwords.words('english')  
    l1 =[];l2 =[] 
    
    # remove stop words from the string 
    pred_set = {w for w in pred_list if not w in sw}  
    ref_set = {w for w in ref_list if not w in sw} 
    
    # form a set containing keywords of both strings  
    rvector = pred_set.union(ref_set)  
    for w in rvector: 
        if w in pred_set: l1.append(1) # create a vector 
        else: l1.append(0) 
        if w in ref_set: l2.append(1) 
        else: l2.append(0) 
    c = 0
    
    # cosine formula  
    for i in range(len(rvector)): 
            c+= l1[i]*l2[i] 
    cosine = c / float((sum(l1)*sum(l2))**0.5) 
    return cosine >= THRESHOLD