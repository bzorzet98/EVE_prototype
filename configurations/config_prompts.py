import os

# Template of prompts
PROMPTS_PATH = os.getcwd() + "/" + "documents" + "/" + "master_prompts"


SUMMARY_CONVERSATION_PROMPT_PATH = PROMPTS_PATH + "/" + "summary_conversations" + "/" + "summary_conversation_prompt_v0_english.txt"
SUMMARY_CONVERSATION_v1 = {'path': SUMMARY_CONVERSATION_PROMPT_PATH, 'input_variables': ['n_messages_before', 'conversation']}

MODIFIED_PERSONAL_INFORMATION_PATIENT_PROMPT_PATH = PROMPTS_PATH + "/" + "modified_personal_information_patient" + "/" + "modified_personal_information_patient_prompt_v0_english.txt"
PERSONAL_INFORMATION_v1 = {'path': MODIFIED_PERSONAL_INFORMATION_PATIENT_PROMPT_PATH, 'input_variables': ['conversation', 'previous_information']}

EVE_PROMPT_SYSTEM_FOR_FINE_TUNNING = PROMPTS_PATH + "/" + "eve_response" + "/" + "eve_prompt_system_for_finetunning_english.txt"
EVE_PROMPT_v1 = {'path': EVE_PROMPT_SYSTEM_FOR_FINE_TUNNING, 'input_variables': ['personal_information', 'previous_conversation_summary', 'last_messages','patient_message']}