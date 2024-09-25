import json
from collections import defaultdict

# Read the JSON file
with open('entailments_test.json', 'r') as file:
    data = json.load(file)

# Initialize a dictionary to store scores for each essay type
essay_scores = defaultdict(list)

# Process each key-value pair in the JSON data
for key, value in data.items():
    essay_type = value[0]  # First value in the array is the essay type
    score = value[1]       # Second value in the array is the score
    essay_scores[essay_type].append(score)

# Calculate the average score for each essay type
average_scores = {essay_type: sum(scores) / len(scores) for essay_type, scores in essay_scores.items()}

# Print the average scores
for essay_type, avg_score in average_scores.items():
    print(f"Essay Type: {essay_type}, Average Score: {avg_score:.2f}")