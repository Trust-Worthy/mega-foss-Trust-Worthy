

"""

Module Name: pydriller_RC_script.py

Description:
    This python script is a generalized version of VHP_ffmpeg.py. This script will read and process a list of 
    git commit hashes that correlate to documented CVE vulnerabilities from a json file. The patch commmit will
    help locate the vulnerability inducing commit hashes by utilizing pydriller's implementation of the
    popular SZZ algorithm. 

    Once found, the vulnerability inducing commit hashes will be written to a new json file corresponding to their
    respective patch inducing commit & CVE.

    This first version of the script won't be able to guarantee any degree of accuracy because it simply gathers data.

    Algorithm Process & Steps:
        1. 

        
Author: Trust-Worthy
Date: 2/4/2025

Notes:
    - pydriller must be installed on the system to run this program

Citations:
    @inbook{PyDriller,
    title = "PyDriller: Python Framework for Mining Software Repositories",
    abstract = "Software repositories contain historical and valuable information about the overall development of software systems. Mining software repositories (MSR) is nowadays considered one of the most interesting growing fields within software engineering. MSR focuses on extracting and analyzing data available in software repositories to uncover interesting, useful, and actionable information about the system. Even though MSR plays an important role in software engineering research, few tools have been created and made public to support developers in extracting information from Git repository. In this paper, we present PyDriller, a Python Framework that eases the process of mining Git. We compare our tool against the state-of-the-art Python Framework GitPython, demonstrating that PyDriller can achieve the same results with, on average, 50% less LOC and significantly lower complexity.URL: https://github.com/ishepard/pydrillerMaterials: https://doi.org/10.5281/zenodo.1327363Pre-print: https://doi.org/10.5281/zenodo.1327411",
    author = "Spadini, Davide and Aniche, Maurício and Bacchelli, Alberto",
    year = "2018",
    doi = "10.1145/3236024.3264598",
    booktitle = "The 26th ACM Joint European Software Engineering Conference and Symposium on the Foundations of Software Engineering (ESEC/FSE)",
}

"""

import os 
import sys
import subprocess
import logging
import pprint
import json

import error_handling as handle

from collections import Counter
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Type

from pydriller import Git, ModifiedFile, Commit




"""global variables:

    PATH_ALL_PROJ_REPOS (str): Path to the directory containing all the FOSS project git repos.
    PATH_SELECTED_REPO (str): Path to the specific repo. This changes as the script iterates through the different patch commits in the json file.
    PATH_PATCH_COMMITS (str): Path to the json file containing all of the patch commits that fix vulnerabilities.
    PATH_OUTPUT_DIR (str): Path to the output directory where the json file with vulnerable commits will be written to.
    PATH_LOG_OUTPUT_DIR (str): Path to the output directory where the logs and errors will be stored.

    HASH_PATCH_COMMIT (str): Commit hash of the patch commit to a vulnerability.
    HASH_VULN_COMMIT (str): Commit hash of the original commit that introduced the vulnerability.
    
    MOD_FILES_BY_PATCH set[str]: Set of paths to files modified by the patch commit.
    
    CHANGES_PATCH_COMMIT dict[str,dict[str,list[tuple[int,str]]]] (dict): The key of the outer dictionary is the name of the modified file by the patch commit. The value is another dictionary. The second
                                                  dictionary has two keys, either "added" or "deleted". The added section has the code that was added by the
                                                 commit and vice-versa. The changes are in a list of tuples where the first index of the tuple is the line number, and the second tuple is the code change.

    CHANGES_VULN_COMMIT dict[str,dict[str,list[tuple[int,str]]]] (dict): Tke key of the dictionary is the modified file by the suspected vulnerable commit. The value is another dictionary. The second
                                                 dictionary has two keys, either "added" or "deleted". The added section has the code that was added by the
                                                 commit and vice-versa. The changes are a code snippet for verification and validation purposes against the CHANGES_PATCH_COMMIT. The changes are in a list 
                                                 of tuples where the first index of the tuple is the line number, and the second tuple is the code change.
    
"""


### TO-DO ###
# make sure that when I call functions in error_handling, to use Pass or continue keyword to skip to the next thing
## ***** above is very important    
# copy all code over and adjust variable names and add necessary error handling for skipping messed up cases
# write code to get the previous commit (the one directly before the patch) this way we can compare that to the other hash.
# write code to get the specific path to the git repo of the selected FOSS Project for the specific patch commit from list in json. Fill PATH_SELECTED_REPO:str = "" variable 
# write code to get the vuln changes for CHANGES VULN COMMIT in the same format as the patch commit.
# write code to get the parent directory with all the .git repos. Use error handling to make sure there is a .git file
# write code to get the name / directory of the FOSS project in the json and verify it exists in the parent directory with all .git repos.
# write code to write the original patch commit, directly prev commit, and the suspected vuln commit (or replace with error if unable to find), and changes to a new json file --> This is the solution
# write correct shebang at the top of script aka find location of python3 on RC
# put all paths into the .env file when I login to RC and find everything on my terminal. Can I carry the .env file with me??? How are env vars handled on RC?
# write code to write the commit changes to the json file (this is already kinda done, but I need to clean it up)
# add env variables to .env 

# answer this question --> Where am I getting path selected repo, 



def setup_initial_logging() -> None:
    """
    This function will be called inside of main before calling subsequent functions.
    """
    # Basic logging setup for initialization phase
    log_file_path: str = 'setup_logs.txt'

    # Ensure the log file is in the same directory as the script
    log_dir: str = os.path.dirname(os.path.abspath(__file__))
    log_file: str = os.path.join(log_dir, log_file_path)

    # Set up file logging with rotation (in case the file grows large)
    logging.basicConfig(
        level=logging.DEBUG,  # Set the logging level to DEBUG
        format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
        handlers=[logging.FileHandler(log_file)]  # Only log to the file, no console output
    )

    # Get the logger
    logger: logging.Logger = logging.getLogger()

    # Example logging message
    logger.info("Basic logging setup complete.")

def initialize_globals() -> None:
    
    """
    Ensures that all global variables are initialized. If they are not, logs an error and initializes them.
    If the environment variables required for initialization are not found, logs the error and exits.
    """
    try:
        load_dotenv()  # Load environment variables from .env file

        # Fetch and assign the environment variables to global variables
        globals()["PATH_ALL_PROJ_REPOS"] = os.getenv("GIT_ALL_REPOS_DIR")
        globals()["PATH_PATCH_COMMITS"] = os.getenv("PATCH_COMMITS_JSON")
        globals()["PATH_OUTPUT_DIR"] = os.getenv("OUTPUT_DIR_JSON")
        globals()["PATH_LOG_OUTPUT_DIR"] = os.getenv("LOGGING_DIR")

        # Check if essential environment variables were set
        missing_vars = []
        for var in ["PATH_ALL_PROJ_REPOS", "PATH_PATCH_COMMITS", "PATH_OUTPUT_DIR", "PATH_LOG_OUTPUT_DIR"]:
            if not globals().get(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise handle.MissingEnvironmentVariableError(f"Missing environment variables: {', '.join(missing_vars)}")

    except handle.MissingEnvironmentVariableError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Error loading environment variables or assigning global variables: {e}")
        sys.exit(1)

    logger.info("Global variables initialized successfully.") 



    # If any global variables are not initialized or are empty, initialize them
    global_vars = {
        "PATH_SELECTED_REPO": "", # call separate function to initialize this
        "HASH_PATCH_COMMIT": "", # call function to retrieve commit from viable_patches json
        "HASH_VULN_COMMIT": "",
        "MOD_FILES_BY_PATCH": set(),
        "CHANGES_PATCH_COMMIT": {},
        "CHANGES_VULN_COMMIT": {},
    }

    # Initialize global variables
    for var_name, value in global_vars.items():
        if globals().get(var_name) is None or globals().get(var_name) == "":
            logger.error(f"Global variable '{var_name}' is not initialized or is empty. Initializing it.")
            globals()[var_name] = value  # Set the value to the empty placeholder (empty string, set, or dict)
        else:
            logger.info(f"Global variable '{var_name}' is already initialized.")

    logger.info("All global variables are initialized as empty values.")


def setup_robust_logging(log_directory: str = "") -> None:
    """

    Set up logging to a file with rotation, using a specified directory.
    If no directory is provided, use the global PATH_LOG_OUTPUT_DIR.

    Args:
        log_directory (str, optional): Defaults to "" in preparation for assignment to global variable.
    """

    if log_directory == "":
        globals().get("PATH_LOG_OUTPUT_DIR")
    
    if not log_directory:
        logger.error("Log directory is not set. Cannot initialize logging.")
        sys.exit(1)

    # Ensure the log directory exists
    if not os.path.exists(log_directory):
        os.makedirs(log_directory, exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_file:str = f'error_log_{timestamp}.txt'
    log_path:str = os.path.join(log_directory, log_file)

    # Check if the log file exists, and if so, increment the name
    if os.path.exists(log_path):
        i = 2
        while os.path.exists(os.path.join(log_directory, f'error_log.txt{i}')):
            i += 1
        log_path = os.path.join(log_directory, f'error_log.txt{i}')
    
    # Set up rotating log file handler
    handler: RotatingFileHandler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=10)  # 5MB per log file, 10 backups
    handler.setLevel(logging.DEBUG)

    # Define log format
    formatter:logging.Formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s - Line: %(lineno)d')
    handler.setFormatter(formatter)

    # Add handler to the root logger
    logging.getLogger().addHandler(handler)

    logger.info("File-based logging has been set up successfully.")

def get_selected_repo_path() -> None:
    return None
def get_hash_patch_commit() -> None:
    return None



if __name__ == "__main__":

   # Basic logging setup for initialization phase
    log_file_path: str = 'setup_logs.txt'

    # Ensure the log file is in the same directory as the script
    log_dir: str = os.path.dirname(os.path.abspath(__file__))
    log_file: str = os.path.join(log_dir, log_file_path)

    # Set up file logging with rotation (in case the file grows large)
    logging.basicConfig(
        level=logging.DEBUG,  # Set the logging level to DEBUG
        format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
        handlers=[logging.FileHandler(log_file)]  # Only log to the file, no console output
    )

    # Get the logger
    logger: logging.Logger = logging.getLogger()

    # Example logging message
    logger.info("Basic logging setup complete.")


    

    # Call the function to initialize the globals
    initialize_globals()

    # Setup the more robust logging setup
    setup_robust_logging()

    # Initialize global variables 
    """
    These parts below will be in some sort of loop in main iterating through all of the repos in the json
    """
    get_selected_repo_path()
    get_hash_patch_commit()

    # Find the modified files by patch commit
    find_modified_files()
    