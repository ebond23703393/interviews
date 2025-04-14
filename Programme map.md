# Survey app organisation

This file describes the organisation of the Interviews app. 

# Key folders

## Core

These programmes define the flow of the interview.

 `agent.py` - the agent script defines the logic and behaviour of the LLM agent interviewer. 
 * `Constructs queries` by combining the history of the interview and user inputs to send chat requests to the Open AI API.
 * `Review answer` / `review question` moderate the user's response as well as the LLMs generated questions to ensure on topic and appropriate.
 * `probe within topic` utilises the probing agent to develop questions within topic, whilst `transition topic` determines the question to move onto the next topic. In some cases, the transition topic returns a pre-defined scripted message rather than allowing the LLM to come up with the next question. 

`auxiliary.py` - This file contains helper functions that facilitate data formatting, prompt construction, LLM task execution, and programmatic selection/extraction of social assistance programme preferences.

* `chat to string`: converts messages from the conversation into a single string. Used to extract history of single topic or up to a single topic.
* `fill prompt with interview`: Fills a prompt template with contextual information from the current interview session, ready to be sent to GPT. 
* `execute queries`: Executes Open AI API tasks.
* `get randomised programmes`: Returns a randomly shuffled list of social assistance programmes and a mapping from 1-5.
* `extract programme choice`: Parses a user's input to detect a number 1-5 and returns the name of the programme. This enables number based selection in a randomised list. 

`logic.py`  - This is the core loop handler. This file initiates the interview and defines the next question in the interview flow.

* Moderates the the user's answers using the functions defined in *agent.py*.
* Uses if conditions to determine the location of the interview (e.g. at the end of a topic) to then decide on which question to ask (e.g. a probing question or a transition question).

`manager.py` - This script defines the InterviewManager class which tracks and manages the state of the interview. It begins by setting the default state variables, such as topic index and the conversation history.

* Tracks progress across topics and questions.
* Sends chat history to a database
* Handling flagged responses. 

`sim_agent.py` - this script defines a simulated agent class which is used in `simulated_interview.py` for running simulated interviews. The characteristics of the simulated interviee are defined in `parameters.py` script.

## Interviews folder

`app.py` - this file needs to be run to launch the app in a web browser.

`Lambda.py` - This file is for deploying the interview as an AWS Lambda function.

`parameters.py` - This script is where the user can define the parameters of the interview, such as whether the interview is moderated, the number of flags raised before the interview terminates, and whether or not the interview is summarised. This is also where the user defines the topics, the length of topics (i.e. the number of questions asked in each topic) and any specific scripted messages. 

This script also characterises the various LLM agents:
* `summary`: This agent formulates a summary of the conversation thus far, summarizing themes and key ideas.
* `transition`: This agent formulates the first question of a new topic as per the interview plan.
* `probe`: this agent creates probing questions following guidelines from academic literature. It's task is to forumulate follow-up questions to dig deeper into the respondents' thoughts.
* `moderator`: this agent reads the latest part of the conversation and determines whether or no the conversation is on track. If not, it will flag the response.

## Scripts
Contains a script for cleaning the output of simulated interviews. This is automatically run in the simulated interview and output is saved in the `app\data` folder.

# How to run the app
To run the app and participate in the interview, do the following:
1. Open the command prompt and navigate to the interviews-env folder. 
2. From here, type `Scripts\activate`.
3. Next, naviagte the app directory by typing `cd interviews\app`.
4. Type `python app.py` to run the application. 
5. Open `http://127.0.0.1:8000` in a browser and it should say `running!`.
6. Modify the url to `http://127.0.0.1:8000\Social_Assistance\session-id-1`. This capture firstly the interview-id, such that the application knows we are in the social assistance workshop, and secondly defines a session. `session-id-1` can be modified as per the user's preference. 
7. At the end of the interview, the interview will be saved in `interviews\app\data`.


# Running simulations
To run a simulated interview:
1. Open the command prompt and navigate to the interviews-env folder. 
2. From here, type `Scripts\activate`.
3. Next, naviagte the interviews directory by typing `cd interviews`.
4. Type `python app\simulated_interview.py`.


This will run the simulated interview and export the clean transcript to `interviews\app\data`. You can modify the persona of the simulated interviee in the `simulated_interview.py` script. 
