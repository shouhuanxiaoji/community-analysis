#!/usr/bin/env python3
# This is a python3 module for obtaining all branches list of all repos
# It Uses GraphQL Api for github and gitlab
# needed these modules: requests gitpython
# github test token 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
# gitlab(gitlab.gnome.org) test token ggopatPAQoirjNB3mQ79wxEyqy

import requests
import os
import git
from urllib.parse import parse_qs, urlparse

owner = "gcc-mirror"
repo = "gcc"
token = "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"
apiurl = 'https://api.github.com/graphql'
repourl = f"https://github.com/{owner}/{repo}.git/"

marked_branch = ("master", "trunk")

headers = {
    "Authorization": f"token {token}",
    "GraphQL-Features": "timeline-preview"
}

#repo = git.cmd.Git()
#repo_ls_remote = repo.ls_remote("--head", repourl).split('\n')
#print(len(repo_ls_remote))

#for i in repo_ls_remote:
#    print(i)

#print(get_commits_count(owner, repo, token))

#commits = requests.get(commiturl, headers=headers).json()
#for commit in commits:
#    print(f"{commit['commit']['message']}, {commit['html_url']}")


query = '''
{
  repository(owner: "gcc-mirror", name: "gcc") {
      master: ref(qualifiedName: "master") {
        target {
          ... on Commit {
            history(first: 100) {
              totalCount
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                message
                committedDate
              }
            }
          }
        }
      }
      devel__SLASH__gccgo: ref(qualifiedName: "devel/gccgo") {
        target {
          ... on Commit {
            history(first: 100) {
              totalCount
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                message
                committedDate
              }
            }
          }
        }
      }
  }
}
'''

data = {'query': query}
response = requests.post(apiurl, headers=headers, json=data)

if response.status_code == 200:
    commit_count = response.json()
#    commit_count_value = commit_count['data']['repository']['ref']['target']['history']['totalCount']
    print(f'Total commits: {commit_count}')
else:
    print('An error occurred.')
