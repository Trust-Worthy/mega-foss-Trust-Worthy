



"""
Obtaining ...

1. Total size of the cloned repos
2. Total number of vulnerability inducing commits (vuln commits) found & not found
3. Average number of months between vuln commit and patch commit (or fix)
4. Average number of commits between the vuln commit & patch commit (or fix)
5. Average number of vuln commits fixed by patch commit (or fix)
6. Percentage of vulns where the vuln commit and fix were made by the same person
"""



import os
import shutil
from pydriller import Repository, Commit
from datetime import datetime
from dateutil.relativedelta import relativedelta


# Calculate repo size
def get_directory_size(path: str) -> float:
    size: float = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            size += os.path.getsize(fp)
    return size

SIZE_OF_ALL_CLONED_REPOS: list[float] = 0 ### size in MB
TOTAL_NUM_MONTHS: int = 0

TOTAL_NUM_COMMITS: int = 0

TOTAL_PATCH_COMMITS_W_VULN_COMMIT: int = 0
TOTAL_VULNS: int = 0 ### Another way to say this is total patch vuln pairs 
### I can get the the number of patches without vulns / not found by doing total entires - total vulns
BY_SAME_PERSON: int = 0 ### Num of vulns made by the same person
PERCENTAGE_OF_VULN_N_PATCH_BY_SAME_PERSON: float = 0.0

### Averages --> my goal!
AVERAGE_NUM_MONTHS_BETWEEN_VULN_N_PATCH: float = 0.0
AVERAGE_NUM_COMMITS_BETWEEN_VULN_N_PATCH: float = 0.0

### Variable used to track repos analyzed for Point 1 so that we get accurate storage metrics
unique_repo_paths: set[str] = set()

### Point 1, 3, 4 , 6
for owner_repo, patch_commit, vuln_commits in zip(
    patch_vuln_df["repo"], 
    patch_vuln_df["patch_commit"], 
    patch_vuln_df["vuln_commits"]
):
    print("Working on iteration --{count}-- of df")

    ## If there aren't any commits to analyze, go onto the next iteration
    if vuln_commits == []:
        continue

    # Compose remote repo for pydriller
    owner, repo = owner_repo.split("/")
    remote_url: str = f"https://github.com/{owner}/{repo}.git"

    

    commits_to_analyze: list[str] = []
    commits_to_analyze.append(patch_commit)
    commits_to_analyze.extend(vuln_commits)


    temp_repo: Repository = Repository(remote_url, only_commits=commits_to_analyze, order='reverse')

    patch_author: str = ""
    patch_author_date: datetime = None

    for commit in temp_repo.traverse_commits():
       
        
        vuln_author: str = ""
        vuln_author_date: datetime = None

        if  TOTAL_VULNS == 0:
            patch_author_date = commit.author_date
            patch_author = commit.author ## is that the correct syntax? what type of object is being returned
            TOTAL_PATCH_COMMITS_W_VULN_COMMIT += 1 ## this patch HAS at least one vuln commit
            
        else: ### reassing the value of vuln_author_date on each iteration after count > 1
            vuln_author_date = commit.author_date
            vuln_author = commit.author
            
        
        ### Calculate difference between patch date and vuln date in months
        difference: datetime = relativedelta(patch_author_date,vuln_author_date)

        # Get the difference in months
        months_difference = difference.year * 12 + difference.month
        
        
        ### Logic for point 1
        if commit.project_path not in unique_repo_paths:
            temp_repo_path = commit.project_path  # Path to the cloned repo
            unique_repo_paths.add(temp_repo_path)
            repo_size: float = get_directory_size(temp_repo_path) / (1024 * 1024)  # Convert to MB
            
            



        ### Logic for point 3


    
        
        
        
        shutil.rmtree(temp_repo_path)
    
    for vuln_commit in temp_repo_vulns.traverse_commits():
        temp_repo_path = vuln_commit.project_path  # Path to the cloned repo
        


        ### Logic for point 3


    
        
        
        
        shutil.rmtree(temp_repo_path)

    SIZE_OF_ALL_CLONED_REPOS += repo_size
    TOTAL_NUM_MONTHS += months_difference
    TOTAL_VULNS += len(vuln_commits) ### Getting total vulns

    
    ### Point 2,Point 5
    
    
        

AVERAGE_NUM_OF_VULNS_TO_PATCH: float = (TOTAL_VULNS / TOTAL_PATCH_COMMITS_w_VULN_COMMIT)
AVERAGE_NUM_MONTHS_BETWEEN_VULN_N_PATCH = (TOTAL_NUM_MONTHS / TOTAL_VULNS )
PERCENTAGE_OF_VULN_N_PATCH_BY_SAME_PERSON = (TOTAL_VULNS / BY_SAME_PERSON )


### Checks
assert(TOTAL_VULN_COMMITS_FOUND == TOTAL_VULNS)
