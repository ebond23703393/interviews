import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import logging
from parameters import INTERVIEW_PARAMETERS, OPENAI_API_KEY
from core.manager import InterviewManager
from core.agent import LLMAgent
from core.sim_agent import SimulatedIntervieweeAgent
from database.file import FileWriter
from scripts.Clean_interview import clean_interview_output

# Setup logging
logging.basicConfig(level=logging.INFO)

# Pick your interview ID
interview_id = "Social_Assistance"
session_id = "SIM-002-rich-uk"

 # SIMULATED RESPONDENT
simulated_persona =  """
        You are a rich person in a rich European country where unconditional cash transfers are prevalent as part of government welfare. 
        Keep any responses to a max of 100 words. 
        You must respond exactly to the question being asked.
		You have very little knowledge, and so feel free to ask 
        questions about transfer programmes if you aren't sure.
        Speak in an informal tone. If told to respond with a number,
        you must respond only with a single number"""

# Load config
parameters = INTERVIEW_PARAMETERS[interview_id]

# Instantiate agents
db = FileWriter()
interview = InterviewManager(db, session_id)
interview.begin_session(parameters)

interviewer = LLMAgent(api_key=OPENAI_API_KEY)
interviewer.load_parameters(parameters)

sim_user = SimulatedIntervieweeAgent(api_key=OPENAI_API_KEY, persona_prompt=simulated_persona)

interview.add_chat_to_session("What comes to mind when you think of the poorest in your country?", type="question")
interview.add_chat_to_session("They work really hard.", type="answer")

# Start interview loop
while not interview.is_terminated():
    if interview.get_current_topic() > len(parameters['interview_plan']):
        interview.terminate("exceeded_topic_index")
        print("Interview terminated")
        break

    current_topic = interview.get_current_topic()
    current_question = interview.get_current_topic_question()
    topic_data = parameters['interview_plan'][current_topic - 1]
    num_questions = topic_data['length']  # total planned questions in this topic

    # Get interviewer message
    if current_question <= len(topic_data.get("questions", [])):
        # Use pre-scripted question
        message = topic_data["questions"][current_question - 1]
    elif current_question >= num_questions:
        # Reached end of this topic
        if current_topic >= len(parameters['interview_plan']):
            interview.terminate("end_of_topics")
            print("Interview terminated")
            break

        # Transition to next topic
        message, summary = interviewer.transition_topic(interview.get_history())
        interview.update_transition(summary)

        # Double check if we’re out of topics now
        if interview.get_current_topic() > len(parameters['interview_plan']):
            interview.terminate("no_more_topics")
            print("Interview terminated")
            break
    else:
        # Generate a probing question within-topic
        message = interviewer.probe_within_topic(interview.get_history())

    interview.update_probe()
    logging.info(f"Interviewer: {message}")
    interview.add_chat_to_session(message, type="question")

    # Simulated response
    user_reply = sim_user.respond(interview.get_history(), message)
    logging.info(f"Simulated Respondent: {user_reply}")
    interview.add_chat_to_session(user_reply, type="answer")

# Save final session
interview.update_session()
logging.info("Simulated interview complete.")

# Clean the output
clean_interview_output(session_id=session_id)