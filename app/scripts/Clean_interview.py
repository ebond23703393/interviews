import json
import os

# Define path
file_path = r"C:/Users/edward_b/github/interviews-env/interviews/app/data/SIM-001.json"

# Load the JSON data
with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

conversation = []

for item in data:
    if item["type"] == "question":
        speaker = "Interviewer"
    elif item["type"] == "answer":
        speaker = "Interviewee"
    else:
        continue  # skip anything not a question or answer

    conversation.append(f"{speaker}: {item['content'].strip()}")

# Print the formatted conversation
for line in conversation:
    print(line)

output_path = r"C:/Users/edward_b/github/interviews-env/interviews/app/data/interview_transcript.txt"
with open(output_path, "w", encoding="utf-8") as out_file:
    for line in conversation:
        out_file.write(line + "\n\n")