from users import *

if __name__ == "__main__":
    path = os.getcwd()
    user_path = path + "/" + "users"
    
    user_manager = UserManager(path = user_path)
    user_manager.identify_user()
    
    if user_manager.check_user_folder():
        print("La carpeta del usuario ya existe.")
    else:
        folder_name = user_manager.create_user_folder()
        print(f"Se ha creado la carpeta del usuario con el nombre: {folder_name}")
