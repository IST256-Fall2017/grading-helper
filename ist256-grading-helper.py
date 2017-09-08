from github import Github
from github.Requester import GithubException
import os
import subprocess

DEFAULT_GRADE_MD = """
# Grade Details

Total Grade: 

Below are the details of your grade:

- What the problem attempted? Effort made to start the homework assignment (1pts).
    - Grade:
- What the problem analysis thought out? Identified inputs and outputs, including sources and targets. Outlined a process which explains code flow in pseudo code – not python. (2pts)
    - Grade:
- Does the code written code execute? Program runs without error. (2pts)
    - Grade: 
- Does the code solve the problem? In addition does it does it handle edge cases and bad input when explicitly directed to do so? (1pt)
    - Grade:
- Is the code well written? Easy to understand, modular uses functions for code reuse and readability? Are python objects aptly named? No unnecessary code, or code not pertinent to the problem at hand? (1pt)
    - Grade:
- Are the questions answered at the bottom of the challenge? Are the answers well thought out and correct? (3pts)

"""

class AuthenticationError(Exception):
    def __init__(self, msg):
        self.msg = msg
    
    def __str__(self):
        return self.msg

class GradingGithub():
    GITHUB_TOKEN = None
    GITHUB_ORGNAME = None
    DEFAULT_DIR = "ist256"
    g = None
    org = None
    _repos_cache = None

    def _init_Github(self, username, password):
        """ Initialized Gitub 

        :param username: string
        :param password: string
        :returns Github Object
        :raises Authentication
        """
        try:
            self.g = Github(username, password=password)
            return self.g
        except GithubException.BadCredentialsException:
            raise AuthenticationError("Invalid Login")

    def __init__(self):
        self.GITHUB_TOKEN = os.environ.get("IST_GITHUB_TOKEN", None)
        self.GITHUB_ORGNAME = os.environ.get("IST_ORG_NAME", None)
        while True:
            if self.GITHUB_TOKEN is None:
                username = input("Please enter your Github username: ")
                password = input("Please enter your Github password: ")
            else:
                username = self.GITHUB_TOKEN
                password = None
            try:
                self._init_Github(username, password)
                break
            except AuthenticationError as e:
                print(e)
                print("Please try again")
        while True:
            if self.GITHUB_ORGNAME is None:
                orgname = input("Please enter your organization name: ")
            else:
                orgname = self.GITHUB_ORGNAME
            try:
                self.org = self._get_org(orgname)
                break
            except GithubException.UnknownObjectException:
                print("Invalid Organization")
                print("Please try again")
                
    def _get_org(self, orgname):
        """ get organization
        :param orgname str: Ogranization Github Name
        return the Organizatoin Object
        """
        return self.g.get_organization(orgname)

    def _add_grading_comments(self, path, grade_md=DEFAULT_GRADE_MD):
        """ add_grading_comments
        
        Adds a markdown file for grading notes
        :param path str: the path to add the file to
        """
        with open(os.path.join(path, "GRADE.md"), "w") as file:
            file.write(grade_md)
        print("Added GRADE.md to {}".format(path))

    def get_repos(self, filter=None):
        """ get repos
        Gets a list of repositories caches the initial reponse

        :param filter str: string to filter the clone_urls by
        :returns list of Repository Objects
        """
        if self._repos_cache is None:
            self._repos_cache = self.org.get_repos()
        
        if filter is not None:
            repos = [r for r in self._repos_cache if filter in r.clone_url]
        else:
            repos = [r for r in self._repos_cache]
        return repos
        
    def clone_repos(self, repo_list, path=None, branch_name="graded"):
        """ Clones the list of repos to the provided path

        If path is not provided it will default to the users home directory

        :param repo_list list: List of repository objects
        :param path str: the path to the folder for the cloned repos
        """
        if path is None or path == "":
            path = os.path.join(os.path.expanduser('~'), self.DEFAULT_DIR)
        
        # Make the directory if it doesn't exist
        if not os.path.exists(path):
            os.makedirs(path)
        
        command = "git clone {} && cd {} && git checkout -b {}"
        for repo in repo_list:
            folder = repo.clone_url.split("/")[-1].rstrip(".git")
            cproc = subprocess.call(command.format(repo.clone_url, folder, branch_name), shell=True, cwd=path)
            if cproc == 0:
                print("Successfully cloned {}".format(repo.full_name))
                self._add_grading_comments(os.path.join(path, folder))
            else:
                print("ERROR")
        

    def commit_and_push(self, commit_message, path=None, branch_name="graded"):
        """ commit_and_push
        Add changed to git tracking, commits them, and pushed to github

        :param commit_message str:Commit message
        :param path str: defaults to user home dir
        :param branch_name str: name of branch to push, defaults to 'graded'
        """ 
        if path is None or path == '':
            path = os.path.join(os.path.expanduser('~'), self.DEFAULT_DIR)
        sub_folders = [name for name in os.listdir(path)
            if os.path.isdir(os.path.join(path, name))]
        command = 'cd {} && git add . && git commit -a -m "{}" && git push origin {}'
        for sub_folder in sub_folders:
            cproc = subprocess.call(command.format(sub_folder, commit_message, branch_name), shell=True, cwd=path)
            while True:
                if cproc == 0:
                    print("Successfully pushed {}".format(sub_folder))
                else:
                    print("There was an error, trying to pull first")
                    cproc = subprocess.call("cd {} && git pull origin {} && git push origin {}".format(sub_folder, branch_name, branch_name),
                                            shell=True, cwd=path)
                    if cproc != 0:
                        print("ERROR: You will need to fix manually")
                    break


if __name__ == "__main__":
    print("Starting Grading Script")
    gh = GradingGithub()
    while True:
        print("Please choose and option")
        print("1 - Clone new repos and setup for grading")
        print("2 - Push graded repos to github")
        print("3 - Quit the program")
        user_choice = input("Option: ")
        if user_choice == "1":
            print("Please enter the repo filter. This will usually be the base of the lesson url")
            filter = input("Filter (enter q to cancel) ")
            if filter.lower() != "q":
                repos = gh.get_repos(filter=filter)
                print("Enter the path to clone the directories into. Defaults to ~/{}".format(gh.DEFAULT_DIR))
                path = input("Path: ")
                gh.clone_repos(repos, path=path)
                print("Cloning Complete")
        if user_choice == "2":
            print("Enter the path that contains cloned repositories. Defaults to ~/{}".format(gh.DEFAULT_DIR))
            path = input("Path (enter q to cancel): ")
            message = input("Please enter the commit message: ")
            if path.lower() != "q":
                gh.commit_and_push(message, path=path)
                print("All repos commited and pushed to github")
        if user_choice == "3":
            break

    print("Finished the grading script")


    
        





