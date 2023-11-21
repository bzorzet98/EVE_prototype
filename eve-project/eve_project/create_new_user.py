import os 
import pandas as pd
import numpy as np

from modules.user_manager import UserManager


def create_new_user(user, password):
    user_manager = UserManager()
    user_manager.create_user(user, password)
    pass

def delete_user(user):
    user_manager = UserManager()
    user_manager.delete_user(user)
    pass    

# Generate the print for create a new user

print("Create a new user")
print("Enter the user name: ")
user = input()
print("Enter the password: ")
password = input()
create_new_user(user, password)
print("User created successfully")

