import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import logging
from parameters import INTERVIEW_PARAMETERS, OPENAI_API_KEY
from core.sim_agent import SimulatedIntervieweeAgent
from scripts.Clean_interview import clean_interview_output
from core.logic import next_question, begin_interview_session, resume_interview_session

# Setup logging
logging.basicConfig(level=logging.INFO)

# Interview configuration
interview_id = "Social_Assistance"
session_id = "SIM-002-politician-india-gpt40mini"

# Define simulated persona (directly used below)
simulated_persona = """
    You are a poor female living in a rural community of brazil, struggling to raise your children. 
    Keep any responses to a max of 100 words. 
    You must respond exactly to the question being asked.
    You have good  knowledge, but feel free to ask questions about transfer programmes if you aren't sure.
    Speak in a tone that you would use in an interview. If told to respond with a number, you must respond only with a single number.
    If told to type "ok", you must respond with "ok".
"""

# Start the interview (initial message)
response = begin_interview_session(session_id, interview_id)
print(response['message'])

# Load the simulated user
sim_user = SimulatedIntervieweeAgent(api_key=OPENAI_API_KEY, persona_prompt=simulated_persona)

# Simulate interview loop
user_message = "They work really hard."  # Initial answer to first question
print(f"Simulated Respondent: {user_message}")
response = next_question(session_id, interview_id, user_message)
print(response["message"])

while not response["message"].startswith("The interview is over"):
    # Simulate a user reply
    interview = resume_interview_session(session_id, interview_id, user_message)
    user_message = sim_user.respond(interview.get_history(), response["message"])
    print(f"Simulated Respondent: {user_message}")

    
    # Get next question
    response = next_question(session_id, interview_id, user_message)
    print(response["message"])

# Clean and save the transcript
interview = resume_interview_session(session_id, interview_id, user_message)
interview.update_session()  # <-- this ensures it's saved
clean_interview_output(session_id=session_id)
logging.info("Simulated interview complete.")