import os
import uuid

from config import USER_PATH , SESSION_LIST_NAME, PERSONAL_INFORMATION_TEMPLATE_PATH
import pandas as pd

from functions_auxiliary import save_as_txt, obtain_number_session


class UserManager:
    def __init__(self,path = USER_PATH):
        self.user_id = None
        self.username = None
        self.path_root = path
        self.user_path = None
        self.current_session_number = None
        self.personal_information = None

    def identify_last_sessions_number(self):
        # Return the number of sessions and the date of the last session
        # Identify if the SESSION_LIST_NAME file exists
        if not os.path.exists(self.user_path + "/" + SESSION_LIST_NAME):
            return None , None
        else:
            # Read the file
            df = pd.read_csv(self.user_path  + "/" + SESSION_LIST_NAME)
            last_session_number = df['session_number'].max()
            date_last_session = df[df['session_number'] == last_session_number]['date'].values[0]
            return last_session_number , date_last_session
            
    def modify_last_sessions_number(self,current_number_session, current_date):
        # Identify if the SESSION_LIST_NAME file exists
        # Obtain the current date
        self.current_session_number = current_number_session
        if not os.path.exists(self.user_path + "/" + SESSION_LIST_NAME):
            # Create the file
            df = pd.DataFrame({'session_number': [current_number_session], 'date': [current_date]})
            df.to_csv(self.user_path + "/" + SESSION_LIST_NAME, index = False)
        else:
            # Modify the data
            new_data = {'session_number': current_number_session, 'date': current_date}
            new_row = pd.DataFrame([new_data])

            # Read the file
            df = pd.read_csv(self.user_path + "/" + SESSION_LIST_NAME)

            # Concatenate the new row with the existing DataFrame
            df = pd.concat([df, new_row], ignore_index=True)
            
            # Save the file
            df.to_csv(self.user_path + "/" + SESSION_LIST_NAME, index = False)
        return None

    def identify_user(self):
        self.username = input("Please enter your username: ")
        #self.username = "test"
        self.user_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, self.username))
        # Check if the user exists
        if self.check_user_folder():
            pass
        else:
            self.create_user_folder()

    def create_user_folder(self):
        if self.user_id is None:
            raise ValueError("El usuario no ha sido identificado.")
        
        if not os.path.exists(self.user_path):
            os.makedirs(self.user_path)
        else:
            print("La carpeta del usuario ya existe.")

        return None

    def check_user_folder(self):
        self.user_path = self.path_root + "/" + f"user_{self.user_id}"
        if os.path.exists(self.user_path):
            return True
        else:
            return False
    
    def give_user_path(self):
        if self.user_id is None:
            raise ValueError("El usuario no ha sido identificado.")
        return self.user_path
    
    def give_user_id(self):
        if self.user_id is None:
            raise ValueError("El usuario no ha sido identificado.")
        return self.user_id
    
    def read_file(self, file_name):
        #file_path = self.user_path + "/" + file_name
        file_path = file_name
        with open(file_path, 'r') as output_file:
            content = output_file.read()
        return content
    
    def write_file(self, path, content):
        save_as_txt(path, content)
    
    def save_summary_session(self, session_summary, n_session, date):
        date = date.replace("/", "-")
        file_path = self.user_path + "/" + "summary_sessions" + "/" + f"summary_session_{n_session}_{date}.txt"
        self.write_file(file_path, session_summary)
        
    def save_entery_conversation(self, conversation, n_session, date):
        date = date.replace("/", "-")
        file_path = self.user_path + "/" + "conversations" + "/" + f"conversation_{n_session}_{date}.txt"
        self.write_file(file_path, conversation)
    
    def load_personal_information(self,):
        # Check if it is the first session
        if self.current_session_number == 0:
            # Create the file in txt format
            # Load the template format
            path = PERSONAL_INFORMATION_TEMPLATE_PATH
        else:
            path = self.user_path + "/" + "personal_information.txt"
        self.personal_information = self.read_file(path)
    
    def load_last_session_summary(self,):
        if not os.path.exists(self.user_path + "/" + "summary_sessions"):
            print("")
            self.last_session_summary = ""
        else:
            # Posible files
            sessions_files = os.listdir(self.user_path + "/" + "summary_sessions")
            if len(sessions_files) == 0:
                print("")
                self.last_session_summary = ""
            else:
                # Sort by session number
                file_names = sorted(sessions_files, key=obtain_number_session, reverse=True)
                # Last session
                last_session = file_names[0]
                self.last_session_summary = self.read_file(self.user_path + "/" + "summary_sessions" + "/" + last_session)
        
    def give_personal_information(self):
        return self.personal_information
    
    def give_last_session_summary(self):
        return self.last_session_summary
    
    def modify_personal_information(self, personal_information):
        self.personal_information = personal_information
        file_path = self.user_path + "/" + "personal_information.txt"
        self.write_file(file_path, personal_information)
