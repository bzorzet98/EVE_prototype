import os

OPENAI_API_KEY = "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"
CONVERSATION_EXAMPLES_PATH = os.getcwd() + "/" + "documents" + "/" + "conversations_examples"

PREDEFINED_MESSAGES = os.getcwd() + "/" + "documents" + "/" + "predefined_messages"

USER_PATH = os.getcwd() + "/" + "documents" + "/" + "users"
SESSION_LIST_NAME = "session_list.csv"
PROMPTS_PATH = os.getcwd() + "/" + "documents" + "/" + "prompts"
DICT_STATES = {0: 'prompt_state_0.txt', 
               1: 'prompt_state_1.txt',
               2: 'prompt_state_2.txt',
               3: 'prompt_state_3.txt',
               4: 'prompt_state_4.txt',}