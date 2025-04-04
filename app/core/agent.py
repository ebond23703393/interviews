import logging
import random
from core.auxiliary import (
    execute_queries, 
    fill_prompt_with_interview, 
    chat_to_string,
    get_randomised_programmes
)
from io import BytesIO
from base64 import b64decode
from openai import OpenAI


class LLMAgent(object):
    """ Class to manage LLM-based agents. """
    def __init__(self, api_key, timeout:int=30, max_retries:int=3):
        self.client = OpenAI(api_key=api_key, timeout=timeout, max_retries=max_retries)
        logging.info("OpenAI client instantiated. Should happen only once!")

    def load_parameters(self, parameters:dict):
        """ Load interview guidelines for prompt construction. """
        self.parameters = parameters

    def transcribe(self, audio) -> str:
        """ Transcribe audio file. """
        audio_file = BytesIO(b64decode(audio))
        audio_file.name = "audio.webm"

        response = self.client.audio.transcriptions.create(
          model="whisper-1", 
          file=audio_file,
          language="en" # English language input
        )
        return response.text

    def construct_query(self, tasks:list, history:list, user_message:str=None) -> dict:
        """ 
        Construct OpenAI API completions query, 
        defaults to `gpt-4o-mini` model, 300 token answer limit, and temperature of 0. 
        For details see https://platform.openai.com/docs/api-reference/completions.
        """
        return {
            task: {
                "messages": [{
                    "role":"user", 
                    "content": fill_prompt_with_interview(
                        self.parameters[task]['prompt'], 
                        self.parameters['interview_plan'],
                        history,
                        user_message=user_message
                    )
                }],
                "model": self.parameters[task].get('model', 'gpt-4o-mini'),
                "max_tokens": self.parameters[task].get('max_tokens', 300),
                "temperature": self.parameters[task].get('temperature', 0)
            } for task in tasks
        }

    def review_answer(self, message:str, history:list) -> bool:
        """ Moderate answers: Are they on topic? """
        response = execute_queries(
            self.client.chat.completions.create,
            self.construct_query(['moderator'], history, message)
        )
        return "yes" in response["moderator"].lower()

    def review_question(self, next_question:str) -> bool:
        """ Moderate questions: Are they flagged by the moderation endpoint? """
        response = self.client.moderations.create(
            model="omni-moderation-latest",
            input=next_question,
        )
        return response.to_dict()["results"][0]["flagged"]
        
    def probe_within_topic(self, history:list) -> str:
        """ Return next 'within-topic' probing question. """

        # Get current topic from parameters
        state = history[-1]
        topic_idx = int(state.get('topic_idx', 1)) - 1  # 0-based
        current_topic = self.parameters['interview_plan'][topic_idx - 1]

        # Randomly use scripted follow-up if defined
        if "scripted_followups" in current_topic:
            logging.info("Using randomized scripted follow-up question.")
            return random.choice(current_topic["scripted_followups"])


        response = execute_queries(
            self.client.chat.completions.create,
            self.construct_query(['probe'], history)
        )
        return response['probe']

    def transition_topic(self, history: list) -> tuple[str, str]:
        """ 
        Determine next interview question transition from one topic
        cluster to the next. If `scripted_message` exists in the next topic,
        return that instead of an LLM-generated transition.
        """
        # Get the current topic index from the latest state
        state = history[-1]
        current_topic_idx = int(state.get('topic_idx', 1))
        interview_plan = self.parameters['interview_plan']

        # Prevent out-of-bounds errors
        if current_topic_idx >= len(interview_plan):
            logging.warning("Already at final topic — no next topic to transition to.")
            return "We've reached the end of the planned topics.", state.get("summary", "")

        # Look ahead to the next topic
        next_topic = interview_plan[current_topic_idx]  # No -1 because we're transitioning TO it
        favourite = state.get("favourite_programme", "").lower()

        # Dynamic scripting: handle programme explanation
        if next_topic.get("dynamic_script") == "explain_programmes":
            logging.info("Generating dynamic programme explanation script.")
            programmes, programme_map = get_randomised_programmes()
            # Save mapping to state for later reference
            state["programme_map"] = programme_map

            # Construct scripted message from programme list
            scripted_message = "Let me explain five common types of social assistance programmes:\n\n"
            for idx, (name, desc) in enumerate(programmes, start=1):
                scripted_message += f"{idx}. {name} - {desc}\n\n"
            scripted_message += "Let me know if you'd like me to repeat or clarify any of these. Type ok if you don't need any further explanation."
            logging.info("Using dynamically scripted_message.")
            return scripted_message, state.get("summary", "")


        if "programme_info_treatment" in next_topic:
        # Filter out any message that contains the favourite programme
            filtered_messages = [
            msg for msg in next_topic["programme_info_treatment"]
            if favourite not in msg.lower()
            ]
            chosen = random.choice(filtered_messages) if filtered_messages else random.choice(next_topic["programme_info_treatment"])
            logging.info(f"Randomized evidence message (≠ favourite): {chosen}")
            return chosen, state.get("summary", "")

        if "scripted_message" in next_topic:
            logging.info("Using single scripted_message.")
            return next_topic["scripted_message"], state.get("summary", "")

        # Otherwise, use the LLM to generate transition (and summary if needed)
        summarize = self.parameters.get('summarize')
        tasks = ['summary', 'transition'] if summarize else ['transition']
        response = execute_queries(
            self.client.chat.completions.create,
            self.construct_query(tasks, history)
        )
        return response['transition'], response.get('summary', '')
