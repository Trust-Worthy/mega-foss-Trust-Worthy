import logging
import os
import sys
from typing import Any,Generator, ClassVar

from error_handling import handle_errors as handle
from szz_utils import szz
from configuration import script_setup as setup
from pydriller import Repository, Commit, ModifiedFile
from pydantic import BaseModel

class Patch_Commit_Classifier(BaseModel):
    """
    The goal of this class is to answer the question: What has been changed by the patch commit??
    """
    def __init__(self) -> None:
        super().__init__() # Calls the next class in MRO
        ### TO-DO ###
        # Continue reading papers to refine this list of fieds
        self._adds_code: bool = False
        self._deletes_code:bool = False
        self._refactors_code: bool = False
        self._changes_lines: bool = False
        self._changes_functions: bool = False
        self._changes_files: bool = False
        self._patch_partial_fix: bool = False
        self._number_of_vulns_fixed_by_patch: int = 1 # Sometimes multiple vulns are fixed by a single patch
        

        self._dmm_unit_size: float = None
        self._dmm_unit_complexity: float = None
        self._dmm_unit_interfacing: float = None
    def classify_patch_commit(self, patch_commit_hash_obj: Commit) -> None:
        # Update the fields based on the patch commit analysis (simplified here)
        self._adds_code = patch_commit_hash_obj.insertions > 0
        self._deletes_code = patch_commit_hash_obj.deletions > 0
        self._refactors_code: bool = False
        
        self._changes_lines = None
        self._changes_functions: bool = False
        self._changes_files = patch_commit_hash_obj.files > 0

        self._patch_partial_fix: bool = False
        self._number_of_vulns_fixed_by_patch: int = 1
        
        
         ### Complexity ### 
        
        self._dmm_unit_size = patch_commit_hash_obj.dmm_unit_size
        self._dmm_unit_complexity = patch_commit_hash_obj.dmm_unit_complexity
        self._dmm_unit_interfacing = patch_commit_hash_obj.dmm_unit_interfacing
  
class Patch_Commit():
    """
    All the data to capture from the Patch commits
    """

    ### I want each patch commit to have a classifier for that patch (this means a new instance of patch commit classifier)
    def __init__(self, full_repo_path: str, patch_commit_hash_obj:Commit) -> None:

        super().__init__() # Calls the next class in MRO

        self._fulle_repo_path: str = full_repo_path
        self._patch_commit_hash_obj: Commit = patch_commit_hash_obj
        self._mod_files_by_patch_commit: list[ModifiedFile] = [] ### This list needs to be "ordered" so that order in which files are changed is maintained
        self._changes_by_patch_commit: dict = {}

        # Create an instance of Patch_Commit_Classifier and associate it with this Patch_Commit instance
        self.classifier = Patch_Commit_Classifier()
        # Call the classifier method to update fields based on the patch commit object
        self.classifier.classify_patch_commit(patch_commit_hash_obj)

        ### Changes Made By Patch Commit ###
        self._mod_files_by_patch_commit.extend(patch_commit_hash_obj.modified_files) 
        

       


        
    def get_classifier_info(self) -> dict:
        """
        Returns a dictionary containing classifier-related information.
        """
        return {
            "adds_code": self.classifier._adds_code,
            "deletes_code": self.classifier._deletes_code,
            "refactors_code": self.classifier._refactors_code,
            "changes_lines": self.classifier._changes_lines,
            "changes_functions": self.classifier._changes_functions,
            "changes_files": self.classifier._changes_files,
            "patch_partial_fix": self.classifier._patch_partial_fix,
            "number_of_vulns_fixed_by_patch": self.classifier._number_of_vulns_fixed_by_patch,
            "dmm_unit_size": self.classifier._dmm_unit_size,
            "dmm_unit_complexity": self.classifier._dmm_unit_complexity,
            "dmm_unit_interfacing": self.classifier._dmm_unit_interfacing,
        }




class Vuln_Commit_Classifier:
    """
    The goal of this class is to answer the question: What has been changed by the vulnerability?
    """
    def __init__(self) -> None:

        super().__init__() # Calls the next class in MRO
        """ Classify's vulnerability based on factors related to implementation and severity"""
        ### TO-DO ###
        # Continue reading papers to refine this list of fieds
        self._adds_code: bool = False
        self._deletes_code:bool = False
        self._refactors_code: bool = False

        self._changes_lines: bool = False
        self._changes_functions: bool = False
        self._changes_files: bool = False
        
        self._is_prev_commit_to_patch = False
        self._was_patch_partial_fix: bool = False # did the patch only partially fix this vuln? True if num of patch commits (field below is greater than 1)

        self._number_of_patch_commits_for_vuln: int = 1 # Sometimes multiple patches are needed to fix a single vuln
  
class Vuln_Commit(Commit,Vuln_Commit_Classifier):
    """
    Every Vulnerable Commit has a corresponding patch commit to go along with it.
    There can also be multiple vulns that correspond to a single patch commit
    Args:
        Patch_Commit (_type_): _description_
    """

    ### I want each vulnerable commit to have a classifier for that commit!! ###
    def __init__(self, full_repo_path: str, patch_commit_hash_obj:Commit) -> None:
        super().__init__() # Calls the next class in MRO

        self._full_repo_path: str = full_repo_path
        self._patch_commit_hash_obj: Commit = patch_commit_hash_obj
        self._mod_files_by_vuln_commit: list[str] = []
        self._changes_vuln_commit: dict = {}
    
    
    

# patch commit class
# vuln commit class
# CVE / vulnerability class...
# I guess. When I iterate through the json, I want to just instantiate one class. I don't
# want a bunch of classes flying around.


# I want a CVE to have, a vuln classifier, a patch commit class, and a vuln commit class


class CVE(BaseModel):
    """
    A CVE instance should contain everything. Vuln classifier, vuln commits, patch commits
    Args:
        Vulnerability_Classifier (_type_): _description_
        Vuln_Commits (_type_): _description_
    """
    def __init__(self,cve_id: str, partial_repo_path: str, hash_patch_commit:str, config: setup.SCRIPT_CONFIG) -> None:
        
        # I need to get the full repo path from the partial repo path 
        # the full repo path is the path on the super computer
        # create a partial repo path field
        # and full repo path field!

        super().__init__() # Calls the next class in MRO

        ### CVE Info ###
        ############################################################################
        self._cve_id:str = cve_id

        ### Repo Info ###
        ############################################################################
        
        self._partial_repo_path: str = partial_repo_path
        self._full_repo_path: str = self.get_full_repo_path(partial_repo_path,config)

        
        self._commits_up_to_patch: Generator = Repository( # Get all commits up to the patch commit (define order)
                                                            self._full_repo_path,
                                                            single = hash_patch_commit,
                                                            to_commit = hash_patch_commit).traverse_commits()

        ### Patch Commit Info ###
        ############################################################################
        self._patch_commit_objects: list[Patch_Commit] = []

        commit_hash_obj: Commit = next(Repository( # Only get the hash patch commit object
                                                                self._full_repo_path,
                                                                single = hash_patch_commit).traverse_commits())

        self._primary_patch_commit: Patch_Commit = Patch_Commit(self._full_repo_path,commit_hash_obj)
        self._patch_commit_objects.append(self._primary_patch_commit)

        ### Vuln Commit Info ###
        ### Objective of project ###
        ############################################################################
        self._vuln_commit_objects: list[Vuln_Commit] = []


    def create_patch_commit_obj(self,patch_commit_hash:str) -> Patch_Commit:
        commit_obj: Commit = next(Repository( # Only get the hash patch commit object
                                                                self._full_repo_path,
                                                                single = patch_commit_hash).traverse_commits())
        
        patch_commit_obj: Patch_Commit = Patch_Commit(self._full_repo_path,commit_obj)
        
        return patch_commit_obj
    
    def add_patch_commit_obj_to_CVE(self,patch_commit_obj:Patch_Commit)->None:
        """
        This function is used when a cve id appears twice in the json file which implies multiple patch commits for a single cve.
        Args:
            patch_commit_hash (str): Commit hash that patches the cve
        """
        self._patch_commit_objects.append(patch_commit_obj)
        
    
    def create_vuln_commit_obj(self,vuln_commit_hash:str) -> Vuln_Commit:
        commit_obj: Commit = next(Repository( # Only get the hash Vuln commit object
                                                                self._full_repo_path,
                                                                single = vuln_commit_hash).traverse_commits())
        
        vuln_commit_obj: Vuln_Commit = Vuln_Commit(self._full_repo_path,commit_obj)
        
        return vuln_commit_obj
    
    def get_full_repo_path(partial_repo_path: str, config: setup.SCRIPT_CONFIG) -> str:
        """
        Use the global config ROOT DIR field to get to the specific repo for the project. 
        Make sure that there is a .git! That's a little check that can go a long way.
        Args:
            partial_repo_path (str): _description_

        Returns:
            str: _description_
        """
        pass
    
    def compare_patch_and_vuln():
        """
        Previously, the issue has been: How do you prove that you found the vulnerability with a specific
        percentage of accuracy. 

        Below we're going to do that! If anything differs (caveat some things can differ like file path because things change), 
        we know we don't have the correct commit that introduced the vulnerability.

        *** How do I develop a probability prediction metric system? *** I want to know with a certain degree of confidence
        that the vuln commit/ commits are in fact what I went looking for.

        Ex: 
        - modified files: patch commit could be doing more than just fixing the vuln. But if some of the vuln modified files are in 
        the list of modified files by the patch commit, then we're cooking! 
        """
        pass


    @property
    def _cve_id(self) -> str:
        return self._cve_id
    
    @_cve_id.setter
    def _cve_id(self,value:str) -> None:
        self._cve_id = value

    @property
    def _partial_repo_path(self) -> str:
        return self._partial_repo_path

    @_partial_repo_path.setter
    def _partial_repo_path(self, value: str) -> None:
        self._partial_repo_path = value

    @property
    def _full_repo_path(self) -> str:
        return self._full_repo_path

    @_full_repo_path.setter
    def _full_repo_path(self, value: str) -> None:
        self._full_repo_path = value

    @property
    def _commits_up_to_patch(self) -> Generator:
        return self._commits_up_to_patch
    
    @_commits_up_to_patch.setter
    def _commits_up_to_patch(self,value:Generator) -> None:
        self._commits_up_to_patch = value
    
    @property
    def _primary_patch_commit(self) -> Commit:
        return self._primary_patch_commit

    @_primary_patch_commit.setter
    def _primary_patch_commit(self, value: Commit) -> None:
        self._primary_patch_commit = value
    
    @property
    def _patch_commit_objects(self) -> list[Patch_Commit]:
        return self._patch_commit_objects

    @_patch_commit_objects.setter
    def _patch_commit_objects(self, value: Patch_Commit) -> None:
        self._patch_commit_objects.append(value)

    @property
    def _vuln_commit_objects(self) -> list[Patch_Commit]:
        return self._vuln_commit_objects

    @_vuln_commit_objects.setter
    def _vuln_commit_objects(self, value: Patch_Commit) -> None:
        self._vuln_commit_objects.append(value)