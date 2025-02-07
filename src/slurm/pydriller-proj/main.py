import script_setup
import cve_config
import szz
import error_handling as handle


import logging
import json

from typing import Any


basic_logger = logging.getLogger("basic_logger")
robust_logger = logging.getLogger("robust_logging")




def process_JSON_CVE(json_file_path: str) -> cve_config.CVE:

    processed_cve: set[str] = set() # o(1) lookup

    with open(json_file_path, 'r') as file:
        cve_data: list[dict[str, Any]] = json.load(file)

    for cve_entry in cve_data:

        json_cve_id:str = handle.safe_dict_get(cve_entry,"cve_id")
        
        repo: str = handle.safe_dict_get(cve_entry,"repo")
        hash_patch_commit: str = handle.safe_dict_get(cve_entry,"commit")

        if json_cve_id in processed_cve:
            ## How can I associate the cve id with the existing CVE and corresponding cve object?
        
        cve: cve_config.CVE = cve_config.CVE()

        cve.cve_id = json_cve_id



if __name__ == "__main__":

    # Setup Basic logging cofiguration in case anything goes wrong during setup
    script_setup.setup_initial_logging()

    # Find the modified files by patch commit
    szz.find_modified_files()