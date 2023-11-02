import os
from functions_auxiliary import read_txt_files
from langchain.prompts import PromptTemplate

class BasePromptConfig():
    def __init__(self,):
        self.prompts_dicts = {}
        pass
    
    def load_prompts(self, path, key):
        pass
    
    def get_prompt(self, key):
        pass
    
    
    
class PromptConfig_v1(BasePromptConfig):
    def __init__(self,):
        super().__init__()
        pass
    
    def load_prompts(self, paths, keys, input_variables = []):
        # Check that paths, keys and input_variables are lists
        if not isinstance(paths, list):
            raise TypeError("paths must be a list")
        if not isinstance(keys, list):
            raise TypeError("keys must be a list")
        if not isinstance(input_variables, list):
            raise TypeError("input_variables must be a list")
        # Check that paths and keys have the same length
        if len(paths) != len(keys):
            raise ValueError("paths and keys must have the same length")
        
        # Load the prompts
        it = 0
        for path, key in zip(paths, keys):
            self.load_prompt(path, key, input_variables[it])
            it+=1
                  
    def load_prompt(self, path, key, input_variables = []):
        # We need to check that path is a valid path
        if not os.path.exists(path):
            raise FileNotFoundError("The path to load the prompts from does not exist")
        # Check that the key is not already in the prompts_dicts
        if key in self.prompts_dicts:
            raise KeyError("The key is already in the prompts_dicts")
        template = read_txt_files(path)
        self.prompts_dicts[key] = PromptTemplate(input_variables = input_variables, 
                                                 output_parser = None, 
                                                 partial_variables = {},
                                                 template = template, 
                                                 template_format = 'f-string', 
                                                 validate_template = True)
        
    def get_prompt(self, key):
        # Check that the key is in the prompts_dicts
        if key not in self.prompts_dicts:
            raise KeyError("The key is not in the prompts_dicts")
        return self.prompts_dicts[key]
        
    def get_empty_prompt_template(self,):
        return PromptTemplate.from_template("empty {empty}")