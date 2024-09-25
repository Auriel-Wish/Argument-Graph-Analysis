import json
import copy
from queue import Queue
import networkx as nx
from my_types import *
from openai import OpenAI
import os

output_folder = "output"
graph_with_context_fpath = os.path.join(output_folder, "graph_with_context.json")
important_graph_info_fpath = os.path.join(output_folder, "important_graph_info.json")
absolute_score_output_fpath = os.path.join(output_folder, "absolute_score_out.json")
normalized_output_fpath = os.path.join(output_folder, "normalized_out.json")
full_consistency_output_fpath = os.path.join(output_folder, "full_consistency_out.json")

client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
gpt4o_mini_model = "gpt-4o-mini"

fill_in_context_prompt = '''
You will be given an essay along with a series of argumentative discourse units (ADUs).
The ADUs are broken down in such a way where each one serves its own argumentative idea.
This is done correctly, but sometimes context is missing, and it can be hard to understand
what exactly an ADU is saying without looking at the essay for context. Your job
is to convert each of these ADUs into the same thing that they were, but fill in
any missing pieces of context so that if I looked at the ADU on its own, I would
know what it was talking about. Do not change any of the meaning, only context.

One easy example is if one ADU says 'It was strong', you should fill in what 'It'
refers to. There are more nuanced examples as well.

Output this improved list of ADUs as a JSON, where the keys are
the node IDs (like 'N15') and the values are the ADU text.
'''

entailment_prompt = '''
You will be given 2 argumentative discourse units.
ADU 1 is the first input, ADU 2 is the second input.
Follow these instructions:
    1) Assume that ADU 1 is true. It does not matter how true or outlandish it sounds - assume it is true.
    2) Given that ADU 1 must be true, determine whether ADU 1 argumentatively
       supports or attacks ADU 2. ADU 1 supports ADU 2 if it makes ADU 2 more true,
       if it is reason for ADU 2, if it is evidence for ADU 2, or if it makes ADU 2
       a stronger argument. ADU 1 attacks ADU 2 if it makes ADU 2 less true,
       if it is reason against ADU 2, if it is evidence against ADU 2, or if it makes ADU 2
       a weaker argument.
    3) Place your conclusion on a scale [-1, 1], where -1 means that ADU 1
       clearly attacks ADU 2, 1 means that ADU 1 clearly supports ADU 2, and 0
       means that ADU 1 has no impact on the argumentative strength of ADU 2.
       You can choose any number on this scale that best fits the relationship,
       and it can be nuanced. For example, if ADU 1 supports ADU 2 pretty well but
       has some flaws, you can choose a number like 0.72. If ADU 1 somewhat
       attacks ADU 2, then you can choose a number like -0.29. If ADU 1 barely
       support ADU 2, you can choose a number like 0.06. IF ADU 1 barely attacks
       ADU 2, you can choose a number like -0.04.
    4) Output a python tuple where the first element is this real number
       between -1 and 1, and the second element is a string explaining your
       reasoning for the outputted number.
'''

# should we also prompt it to suggest a way to link the nodes?
paragraph_nodes_map_prompt = '''
The user has placed many ADUs in paragraph -(1)- of their essay. However, the ADUs do not
all relate to the same idea. There are groups of ADUs that relate to each other
but do not relate to ADUs in other groups. As such, each group of ADUs should
each be in their own paragraph, or a link between the groups of ADUs needs to
be introduced. Generate a comment to the user explaining this must be done for
paragraph -(1)-.
'''