import os

OPENAI_API_KEY = "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"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# User files paths
USER_PATH = os.getcwd() + "/" + "documents" + "/" + "users"
SESSION_LIST_NAME = "session_list.csv"


DICT_STATES = {0: 'prompt_state_0.txt', 
               1: 'prompt_state_1.txt',
               2: 'prompt_state_2.txt',
               3: 'prompt_state_3.txt',
               4: 'prompt_state_4.txt',}

CONVERSATION_EXAMPLES_PATH = os.getcwd() + "/" + "documents" + "/" + "conversations_examples" + "/" + "conversations.txt"
PREDEFINED_MESSAGES = os.getcwd() + "/" + "documents" + "/" + "predefined_messages"

# Templates
PERSONAL_INFORMATION_TEMPLATE_PATH = os.getcwd() + "/" + "documents" + "/" + "templates" + "/" + "personal_information_template.txt"

# Template of prompts
PROMPTS_PATH = os.getcwd() + "/" + "documents" + "/" + "master_prompts"
FIRST_SESSION_PROMPT_PATH = PROMPTS_PATH + "/" + "first_session.txt"
FIRST_SESSION_SUMMARY_PROMPT_PATH = PROMPTS_PATH + "/" + "first_session_summary.txt"
SESSION_FINISHED_SUMMARY_PROMPT_PATH = PROMPTS_PATH + "/" + "session_summary.txt"
PERSONAL_INFORMATION_PROMPT_PATH = PROMPTS_PATH + "/" + "personal_information.txt"