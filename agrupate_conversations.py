import os

def read_files(folders, output_file):
    with open(output_file, 'w') as output:
        output.write("Examples of psychologist responses:\n\n")
        for folder in folders:
            for subdir, _, files in os.walk(folder):
                file_count = 0
                for file in files:
                    if file.endswith('.txt'):
                        file_count += 1
                        full_path = os.path.join(subdir, file)
                        folder_name = os.path.basename(subdir)
                        file_name = os.path.splitext(file)[0]
                        
                        if file_count == 1:
                            output.write(f"\n\n# Folder: {folder_name} - Example {file_count}\n")
                        else:
                            output.write(f"\n\n# Folder: {folder_name} - Example 1 OR 2 OR ... OR {file_count}\n")
                        
                        with open(full_path, 'r') as txt_file:
                            content = txt_file.read()
                            output.write(content)

folders = ['/home/bruno/Proyectos/Talk-to-Eve/eve-training/conversations']  # Replace this list with the paths of the folders you want to read
output_file = 'conversations.txt'  # Name of the output file

read_files(folders, output_file)

print("File reading and writing completed.")
