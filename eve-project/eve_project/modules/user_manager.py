import pandas as pd
import numpy as np
import os
import datetime

from configurations.config_user_managers import USERS_LIST_PATH, PATH_TO_SAVE
from configurations.config_templates import PERSONAL_INFORMATION_TEMPLATE_PATH
from functions_auxiliary import save_as_txt, read_txt_file


class UserManager():
    def __init__(self,):
        self.user_list = pd.read_csv(USERS_LIST_PATH)
        self.permission = False
        self.user = None
        self.password = None
        
        self.information = {}
        pass
    
    def user_login(self):
        login = False
        while not login:
            # Check if the user is registered
            print("Username:")
            username = input()
            print("Password:")
            password = input()
            # Check user
            if self.check_user(username, password):
                login = True
                self.permission = True
                self.username = username
                self.password = password
                
                # Obtain information of the user folder
                self.load_user_information()
            else: 
                print("The user is not registered.")
                
    def save_content(self,content, filename, folder=None):
        # Check if permission is True
        if self.permission:
            # Obtain the folder path
            path_user = self.get_user_folder(self.username, self.password)
            # Check if the folder exists in the user folder
            if folder is None:
                # Save content in path
                save_as_txt(path_user + "/" + filename, content)
                return True
            if folder in os.listdir(path_user):
                # Save content in path
                save_as_txt(path_user + "/" + folder + "/" + filename, content)
                return True
            else:
                # Return an message of incorrect folder
                return False
             
    def load_content(self, path):
        # Check if permission is True
        if self.permission:
            # Load content in path
            return read_txt_file(path)
        else:
            # Return an message of incorrect user
            return False
           
    def check_user(self, user, password):
        if user in self.user_list['user'].values:
            if password in self.user_list['password'].values:
                return True
            else:
                return False
        else:
            # Return an message of incorrect user
            return False
    
    def create_user(self, user, password, type_='user'):
        if user in self.user_list['user'].values:
            # Return an message of user already exists
            return False
        else:
            # Create user and return a message of success
            # Suponiendo que 'user_list' es un DataFrame existente
            new_data = pd.DataFrame({'user': [user],'type':[type_], 'password': [password]})

            # Usar concat para agregar nuevas filas
            self.user_list = pd.concat([self.user_list, new_data], ignore_index=True)
            self.user_list.to_csv(USERS_LIST_PATH, index=False)
            # Create user folder
            self.create_user_folder(user)
            return True
    
    def delete_user(self, user):
        if user in self.user_list['user'].values:
            # Delete user and return a message of success
            self.user_list = self.user_list[self.user_list['user'] != user]
            self.user_list.to_csv(USERS_LIST_PATH, index=False)
            return True
        else:
            # Return an message of user not exists
            return False
    
    def create_user_folder(self, user):
        if user in self.user_list['user'].values:
            # Create user folder
            os.mkdir(PATH_TO_SAVE + "/" + user)
            # Users folders has the next folders: sessions, sessions_summary
            os.mkdir(PATH_TO_SAVE + "/" + user + "/sessions")
            os.mkdir(PATH_TO_SAVE + "/" + user + "/sessions_summary")
            
            # User folder has the next files: session_list.csv (has the columns session_number/date(YYYY/MM/DD)), personal_information.txt
            session_list = pd.DataFrame(columns=['session_number','date'])
            session_list.to_csv(PATH_TO_SAVE + "/" + user + "/session_list.csv", index=False)
            
            # Load the personal information template and save it in the user folder
            personal_information_template = read_txt_file(PERSONAL_INFORMATION_TEMPLATE_PATH)
            save_as_txt(PATH_TO_SAVE + "/" + user + "/personal_information.txt", personal_information_template)
            return True
        else:
            # Return an message of user not exists
            return False
        
    def get_user_folder(self, user, password):
        if user in self.user_list['user'].values:
            if password in self.user_list['password'].values:
                # Return user folder
                return PATH_TO_SAVE + "/" + user
        else:
            # Return an message of user not exists
            return False
        
    def load_user_information(self):
        # Check if permission is True
        if self.permission:
            # Load the personal information template and save it in the user folder
            personal_information = self.load_content(PATH_TO_SAVE + "/" + self.username + "/personal_information.txt")
            # Load the sesion list
            session_list = pd.read_csv(PATH_TO_SAVE + "/" + self.username + "/session_list.csv")
            # Obtain the date and number of the last session
            # Check if the session list is empty
            if session_list.shape[0] == 0:
                # If the session list is empty, the last session number and date is 0 and 0
                last_session_number = None
                last_session_date = None
            else:
                # If the session list is not empty, the last session number and date is the last session number and date
                last_session_number = session_list['session_number'].values[-1]
                last_session_date = session_list['date'].values[-1]
            
            # Convert the personal information in a dictionary
            self.information = {'personal_information': personal_information,
                                'last_session_number': last_session_number,
                                'last_session_date': last_session_date}
        else:
            # Return an message of incorrect user
            return False
        
    def get_user_information(self, key=None):
        # Check if permission is True
        if self.permission:
            if key is not None:
                # Return the information of the user
                return self.information[key]
        else:
            # Return an message of incorrect user
            return False
        
    def update_user_information(self, key=None, value=None):
        # Check if permission is True
        if self.permission:
            if key is not None:
                # Save the information of the user
                self.information[key] = value
                return True
        else:
            # Return an message of incorrect user
            return False
        
    def save_user_information(self):
        # Check if permission is True
        if self.permission:
            
            # Save the personal information template and save it in the user folder
            self.save_content(content = self.information['personal_information'], 
                               folder = None, 
                               filename = 'personal_information.txt')
            
            # Read the session list
            session_list = pd.read_csv(PATH_TO_SAVE + "/" + self.username + "/session_list.csv")
            
            # Generate the new dataframe with session list and the new number session and date
            date = datetime.datetime.now().strftime("%Y_%m_%d")
            if self.information['last_session_number'] is None:
                session_number = 0
            else:
                session_number = self.information['last_session_number']
            session_number += 1
            new_session_list = pd.DataFrame({'session_number':session_number,'date':date}, index=[0])
            session_list = pd.concat([session_list, new_session_list], ignore_index=True)
            session_list.to_csv(PATH_TO_SAVE + "/" + self.username + "/session_list.csv", index=False)
            return True
        else:
            # Return an message of incorrect user
            return False