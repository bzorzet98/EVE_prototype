import chromadb
from chromadb.config import Settings
import openai
import yaml
from time import time, sleep
from uuid import uuid4


class EVE_chat:
    def __init__(self,prompt_to_default_system_file = 'system_default.txt', 
                 user_profile_file = 'user_profile.txt',
                 prompt_to_instantiate_new_kb_file = 'system_instantiate_new_kb.txt',
                 prompt_to_system_update_existing_kb_file = 'system_update_existing_kb.txt',
                 prompt_to_system_split_kb_file = 'system_split_kb.txt',
                 prompt_to_system_update_user_profile_file ='system_update_user_profile.txt',
                 openai_api_key_file = 'key_openai.txt', 
                 chromab_directory = "chromadb", 
                 n_messages_to_update = 5 ):
        
        self.persist_directory = chromab_directory
        self.chroma_client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.chroma_client.get_or_create_collection(name="knowledge_base")
        self.n_messages_to_update = n_messages_to_update
        self.openai_api_key = self.open_file(openai_api_key_file)
        
        # User profile file
        self.user_profile_file = user_profile_file
        self.prompt_to_default_system_file = prompt_to_default_system_file
        # Files prompts 
        self.prompt_to_instantiate_new_kb_file = prompt_to_instantiate_new_kb_file
        self.prompt_to_system_update_existing_kb_file = prompt_to_system_update_existing_kb_file
        self.prompt_to_system_split_kb_file = prompt_to_system_split_kb_file
        self.prompt_to_system_update_user_profile_file = prompt_to_system_update_user_profile_file

    def save_yaml(self, filepath, data):
        with open(filepath, 'w', encoding='utf-8') as file:
            yaml.dump(data, file, allow_unicode=True)

    def save_file(self, filepath, content):
        with open(filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(content)

    def open_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
            return infile.read()

    def chatbot(self, messages, model="gpt-4", temperature=0):
        max_retry = 7
        max_tokens = 7000
        retry = 0
        while True:
            try:
                openai.api_key = self.openai_api_key
                response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature)
                text = response['choices'][0]['message']['content']

                debug_object = [i['content'] for i in messages]
                debug_object.append(text)
                self.save_yaml('api_logs/convo_%s.yaml' % time(), debug_object)
                if response['usage']['total_tokens'] >= max_tokens:
                    a = messages.pop(1)

                return text
            except Exception as oops:
                print(f'\n\nError communicating with OpenAI: "{oops}"')
                if 'maximum context length' in str(oops):
                    a = messages.pop(1)
                    print('\n\n DEBUG: Trimming oldest message')
                    continue
                retry += 1
                if retry >= max_retry:
                    print(f"\n\nExiting due to excessive errors in API: {oops}")
                    exit(1)
                print(f'\n\nRetrying in {2 ** (retry - 1) * 5} seconds...')
                sleep(2 ** (retry - 1) * 5)

    def update_data_profile(self, user_messages, current_profile):
        prompt_to_system_update_user_profile = self.open_file(self.prompt_to_system_update_user_profile_file)
        print('\n\nUpdating user profile...')
        # if len(user_messages) > 3:
        #     user_messages.pop(0)
        user_scratchpad = '\n'.join(user_messages).strip()
        profile_length = len(current_profile.split(' '))
        profile_conversation = [{'role': 'system', 'content': prompt_to_system_update_user_profile.replace('<<UPD>>', current_profile).replace('<<WORDS>>', str(profile_length))},
                                {'role': 'user', 'content': user_scratchpad}]
        profile = self.chatbot(profile_conversation)
        self.save_file(self.user_profile_file , profile)
        
    def update_kd(self, all_messages):
        # if len(all_messages) > 5:
        #     all_messages.pop(0)
        prompt_to_instantiate_new_kb = self.open_file(self.prompt_to_instantiate_new_kb_file)
        prompt_to_system_update_existing_kb = self.open_file(self.prompt_to_system_update_existing_kb_file)
        prompt_to_system_split_kb = self.open_file(self.prompt_to_system_split_kb_file)
        
        main_scratchpad = '\n\n'.join(all_messages).strip()
        print('\n\nUpdating KB...')
        if self.collection.count() == 0:
            kb_convo = [{'role': 'system', 'content': prompt_to_instantiate_new_kb},
                        {'role': 'user', 'content': main_scratchpad}]
            article = self.chatbot(kb_convo)
            new_id = str(uuid4())
            self.collection.add(documents=[article], ids=[new_id])
        else:
            results = self.collection.query(query_texts=[main_scratchpad], n_results=1)
            kb = results['documents'][0][0]
            kb_id = results['ids'][0][0]

            kb_convo = [{'role': 'system', 'content': prompt_to_system_update_existing_kb.replace('<<KB>>', kb)},
                        {'role': 'user', 'content': main_scratchpad}]
            article = self.chatbot(kb_convo)
            self.collection.update(ids=[kb_id], documents=[article])
            #self.save_file('db_logs/log_%s_update.txt' % time(), 'Updated document %s:\n%s' % (kb_id, article))

            kb_len = len(article.split(' '))
            if kb_len > 1000:
                kb_convo = [{'role': 'system', 'content': self.open_file('system_split_kb.txt')},
                            {'role': 'user', 'content': article}]
                articles = self.chatbot(kb_convo).split('ARTICLE 2:')
                a1 = articles[0].replace('ARTICLE 1:', '').strip()
                a2 = articles[1].strip()
                self.collection.update(ids=[kb_id], documents=[a1])
                new_id = str(uuid4())
                self.collection.add(documents=[a2], ids=[new_id])
                
    def start_chat(self):
        current_profile = self.open_file(self.user_profile_file)
        prompt_to_default_system = self.open_file(self.prompt_to_default_system_file)
        
        conversation = [{'role': 'system', 'content': prompt_to_default_system}]
        user_messages = []
        all_messages = []

        finish_session = False
        
        while finish_session == False:
            text = input('\n\nUSER: ')
            
            if text.lower() == "exit":
                finish_session = True
            
            user_messages.append(text)
            all_messages.append('USER: %s' % text)
            conversation.append({'role': 'user', 'content': text})
            
            self.save_file('chat_logs/chat_%s_user.txt' % time(), text)

            if len(all_messages) > self.n_messages_to_update:
                all_messages.pop(0)
            main_scratchpad = '\n\n'.join(all_messages).strip()


            kb = 'No KB articles yet'
            if self.collection.count() > 0:
                results = self.collection.query(query_texts=[main_scratchpad], n_results=1)
                kb = results['documents'][0][0]

            #That part we can to do differently
            default_system_prompt = prompt_to_default_system.replace('<<PROFILE>>', current_profile).replace('<<KB>>', kb)
            conversation[0]['content'] = default_system_prompt

            response = self.chatbot(conversation)

            self.save_file('chat_logs/chat_%s_chatbot.txt' % time(), response)
            conversation.append({'role': 'assistant', 'content': response})
            all_messages.append('EVE: %s' % response)
            print('\n\nEVE: %s' % response)            
            
            # If all_messages have more than 7000 tokens, update the knowledge database
            total_tokens = sum(len(message.split()) for message in all_messages)
            if total_tokens >= 7000:
                self.update_kd(all_messages)

            # If finish session, we have to update the current profile, the knoledge database, obtain the tags, etc,etc 
            if finish_session:
                print('Finish session')
                # Here we need to implement other method that update the profile
                self.update_data_profile(user_messages = user_messages, current_profile = current_profile)
                

