from chatbots import *
import os

current_directory = os.getcwd()
prompts_field = "masters_prompts/"
user_profile_field = 'users_profile/'


args = {
    'prompt_to_default_system_file': current_directory + '/' + prompts_field +'system_default.txt',
    'user_profile_file': current_directory + '/' + user_profile_field + 'user_profile.txt',
    'prompt_to_instantiate_new_kb_file': current_directory + '/' + prompts_field + 'system_instantiate_new_kb.txt',
    'prompt_to_system_update_existing_kb_file': current_directory + '/' + prompts_field + 'system_update_existing_kb.txt',
    'prompt_to_system_split_kb_file': current_directory + '/' + prompts_field + 'system_split_kb.txt',
    'prompt_to_system_update_user_profile_file': current_directory + '/' + prompts_field + 'system_update_user_profile.txt',
    'openai_api_key_file': 'key_openai.txt',
    'chromab_directory': "chromadb",
    'n_messages_to_update': 5
}

if __name__ == '__main__':
    chatbot_instance = EVE_chat(**args)
    chatbot_instance.start_chat()   