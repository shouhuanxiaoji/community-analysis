#!/usr/bin/env python3
import requests
import git

url = "https://gitlab.gnome.org/api/v4/projects/GNOME%2Fgtk/repository/branches"
repourl = "https://gitlab.gnome.org/GNOME/gtk.git"
marked_branches = ("main", "wip/otte/path")

headers = {
            "Private-Token": "ggopatPAQoirjNB3mQ79wxEyqy"
}

response = requests.get(url, headers=headers)
projects = response.json()

repo = git.cmd.Git()
repo_ls_remote = repo.ls_remote("--head", repourl).split('\n')
print(repo_ls_remote)

#for project in projects:
#        print(f"Project name: {project['name']} (ID: {project['id']})")
