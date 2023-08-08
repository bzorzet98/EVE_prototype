import os
import uuid

class UserManager:
    def __init__(self,path):
        self.user_id = None
        self.path_root = path
        self.user_path = None

    def identify_user(self):
        username = input("Por favor, introduce tu nombre de usuario: ")
        self.user_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, username))

    def create_user_folder(self):
        if self.user_id is None:
            raise ValueError("El usuario no ha sido identificado.")

        self.user_path = self.path_root + "/" + f"user_{self.user_id}"
        if not os.path.exists(self.user_path):
            os.makedirs(self.user_path)
        else:
            print("La carpeta del usuario ya existe.")
        return self.user_path

    def check_user_folder(self):
        if self.user_id is None:
            raise ValueError("El usuario no ha sido identificado.")
        folder_name = self.path_root + "/" + f"user_{self.user_id}"
        return os.path.exists(folder_name)
    
    def give_user_path(self):
        if self.user_id is None:
            raise ValueError("El usuario no ha sido identificado.")
        return self.user_path
