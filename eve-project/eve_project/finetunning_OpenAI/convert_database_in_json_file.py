import re
import json
import random
from config import EVE_PROMPT_SYSTEM_FOR_FINE_TUNNING

# read EVE_PROMPT_SYSTEM_FOR_FINE_TUNNING file
with open(EVE_PROMPT_SYSTEM_FOR_FINE_TUNNING, "r") as archivo:
    PROMPT_PSYCOLOGIST = archivo.read()

# Lee el archivo txt
with open("documents/conversations_examples/conversations.txt", "r") as archivo:
    contenido = archivo.read()

# Divide el contenido en ejemplos usando "Folder: " como separador
ejemplos = re.split(r'# Folder: ', contenido)[1:]

# Inicializa una lista para almacenar los messages
all_messages_json = []

n_examples = len(ejemplos)
n_examples_train = int(0.7 * n_examples)
n_examples_val = int(0.15 * n_examples)
n_examples_test = int(0.15 * n_examples)

# Random split
examples_train = random.sample(ejemplos, n_examples_train)
examples_val = list(set(ejemplos) - set(examples_train))
examples_val = random.sample(examples_val, n_examples_val)
examples_test = list(set(ejemplos) - set(examples_train) - set(examples_val))
 
# Train
with open("documents/conversations_examples/conversations_train.jsonl", "w") as jsonl_file:
    # Itera a través de los ejemplos
    it = 0
    for ejemplo in examples_train:
        lines = ejemplo.strip().split('\n')
        messages = []
        messages.append({"role": "system", "content": PROMPT_PSYCOLOGIST})
        user_message = True
        for index in range(1, len(lines), 2):
            line = lines[index]
            if user_message:
                line = line.replace("User: ","")
                messages.append({"role": "user", "content": line})
                user_message = False
            else:
                line = line.replace("EVE: ","")
                messages.append({"role": "assistant", "content": line})
                user_message = True
        # Escribe el objeto JSON en una línea del archivo JSONL
        json_str = json.dumps({"messages": messages}, separators=(',', ':'))
        jsonl_file.write(json_str + '\n')
        it+=1
        
# Validation
with open("documents/conversations_examples/conversations_val.jsonl", "w") as jsonl_file:
    # Itera a través de los ejemplos
    it = 0
    for ejemplo in examples_val:
        lines = ejemplo.strip().split('\n')
        messages = []
        messages.append({"role": "system", "content": PROMPT_PSYCOLOGIST})
        user_message = True
        for index in range(1, len(lines), 2):
            line = lines[index]
            if user_message:
                line = line.replace("User: ","")
                messages.append({"role": "user", "content": line})
                user_message = False
            else:
                line = line.replace("EVE: ","")
                messages.append({"role": "assistant", "content": line})
                user_message = True
        # Escribe el objeto JSON en una línea del archivo JSONL
        json_str = json.dumps({"messages": messages}, separators=(',', ':'))
        jsonl_file.write(json_str + '\n')
        it+=1

# Test
with open("documents/conversations_examples/conversations_test.jsonl", "w") as jsonl_file:
    # Itera a través de los ejemplos
    it = 0
    for ejemplo in examples_test:
        lines = ejemplo.strip().split('\n')
        messages = []
        messages.append({"role": "system", "content": PROMPT_PSYCOLOGIST})
        user_message = True
        for index in range(1, len(lines), 2):
            line = lines[index]
            if user_message:
                line = line.replace("User: ","")
                messages.append({"role": "user", "content": line})
                user_message = False
            else:
                line = line.replace("EVE: ","")
                messages.append({"role": "assistant", "content": line})
                user_message = True
        # Escribe el objeto JSON en una línea del archivo JSONL
        json_str = json.dumps({"messages": messages}, separators=(',', ':'))
        jsonl_file.write(json_str + '\n')
        it+=1
print("finish")




