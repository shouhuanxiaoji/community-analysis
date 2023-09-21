#!/usr/bin/env python3
# This is a python3 module for obtaining all branches list of all repos
# It Uses GraphQL Api for github and gitlab
# needed these modules: requests gitpython
# github test token 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
# gitlab(gitlab.gnome.org) test token ggopatPAQoirjNB3mQ79wxEyqy
# 获取tag对应branch的办法是，首先找到tag对应的commit，然后找到commit所属的branch(可能有多个)
import requests
import json
from datetime import datetime,timedelta

owner = "gcc-mirror"
repo = "gcc"
token = "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"
apiurl = 'https://api.github.com/graphql'
repourl = f"https://github.com/{owner}/{repo}.git/"

marked_tag = "releases/gcc-12.3.0"

headers = {
    "Authorization": f"token {token}",
    "GraphQL-Features": "timeline-preview"
}
# branch lists
bb = []

# commit oid for marked_tag
commit_date = ""

query_tag_oid = F"""
query {{
  repository(owner: "{owner}", name: "{repo}") {{
    ref(qualifiedName: "refs/tags/{marked_tag}") {{
      target {{
        ... on Tag {{
          target {{
            ... on Commit {{
              oid
              committedDate
            }}
          }}
        }}
        ... on Commit {{
          oid
          committedDate
        }}
      }}
    }}
  }}
}}
"""

response = requests.post(
    apiurl, 
    headers=headers, 
    json={"query": query_tag_oid}
)

if response.ok:
    data = response.json()
    commit_oid = data["data"]["repository"]["ref"]["target"]["target"]["oid"]
    commit_date = data["data"]["repository"]["ref"]["target"]["target"]["committedDate"]

    # 使用从第一个查询返回的 commit_date 查询分支
    oid_get_branch = f"""
    query {{
      repository(owner: "{owner}", name: "{repo}") {{
        refs(refPrefix: "refs/heads/", first: 100) {{
          edges {{
            node {{
              name
              target {{
                ... on Commit {{
                  history(first: 1, since: "{commit_date}", until: "{commit_date}") {{
                    edges {{
                      node {{
                        oid
                      }}
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
      }}
    }}
    """
    response2 = requests.post(
        apiurl, 
        headers=headers, 
        json={"query": oid_get_branch}
    )

    if response2.ok:
        data2 = response2.json()
        for branch in data2['data']['repository']['refs']['edges']:
          if not branch['node']['target']['history']['edges']:
            pass
          else:
            if branch['node']['target']['history']['edges'][0]['node']['oid'] == commit_oid:
              bb.append(branch['node']['name'])
    else:
        print("Error:", response.text)

else:
    print("Error:", response.text)

#默认的graphql的since规则，是给定一个时间点，获取从该时间之后的所有commits，也就是说包含了该时间点的commit，但我们不需要这一条，所以时间加一秒，就只会获取该时间之后的新commits
commit_date_strip = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ")
commit_date_exclude_this_obj = commit_date_strip + timedelta(seconds=1)
commit_date_exclude_this = commit_date_exclude_this_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

# github's order was from new date commit to old one
# so 0 is the newest, 99 is the oldest

commit_cursor = ""

branch_get_commits = F"""
query {{
  repository(owner: "{owner}", name: "{repo}") {{
    object(expression: "{bb[0]}") {{
        ... on Commit {{
          history(first: 100 {', after: "' + commit_cursor + '"' if commit_cursor else ''}, since: "{commit_date_exclude_this}") {{
            totalCount
            pageInfo {{
              hasNextPage
              endCursor
              startCursor
            }}
            edges {{
              node {{
                oid
                committedDate
                message
              }}
            }}
          }}
        }}
    }}
  }}
}}
"""

response3 = requests.post(
    apiurl, 
    headers=headers, 
    json={"query": branch_get_commits}
)
# return value of github api was limited 100 per page, so we need pagination
hasNextPage = False
commits_list = []
if response3.ok:
    data3 = response3.json()
    commits_list = data3['data']['repository']['object']['history']
    # return type is bool
    hasNextPage = data3['data']['repository']['object']['history']['pageInfo']['hasNextPage']
    if hasNextPage == True:
      commit_cursor = data3['data']['repository']['object']['history']['edges'][99]['node']['oid'] + " 0"
    else:
      commit_len = len(data3['data']['repository']['object']['history']['edges'])
      commit_cursor = data3['data']['repository']['object']['history']['edges'][commit_len - 1]['node']['oid'] + " 0"       
else:
    print("Error:", response.text)

commits_list_extra = []
# if return json has NextPage
while hasNextPage == True:
  branch_get_commits = F"""
  query {{
    repository(owner: "{owner}", name: "{repo}") {{
      object(expression: "{bb[0]}") {{
          ... on Commit {{
            history(first: 100 {', after: "' + commit_cursor + '"' if commit_cursor else ''}, since: "{commit_date_exclude_this}") {{
              totalCount
              pageInfo {{
                hasNextPage
                endCursor
                startCursor
              }}
              edges {{
                node {{
                  oid
                  committedDate
                  message
                }}
              }}
            }}
          }}
      }}
    }}
  }}
  """

  response3 = requests.post(
      apiurl, 
      headers=headers, 
      json={"query": branch_get_commits}
  )
  data3 = response3.json()
  commits_list_extra = data3['data']['repository']['object']['history']['edges']
  
  for i in  commits_list_extra:
    commits_list['edges'].append(i)

  hasNextPage = data3['data']['repository']['object']['history']['pageInfo']['hasNextPage']
  if hasNextPage == True:
    commit_cursor = data3['data']['repository']['object']['history']['edges'][99]['node']['oid'] + " 0"
  else:
    commit_cursor = ""

# we need commits_list
# the data struction is :
#{'totalCount': 1, 'pageInfo': {'hasNextPage': False, 'endCursor': 'xxx 0', 'startCursor': 'xxx 0'}, 'edges': [{'node': {'oid': 'xxx', 'committedDate': '2023-07-05T13:49:24Z', 'message': 'xxx'}}]}
#print(commits_list)


# using AI to analyse commit message
AI_IP = "xxx.xxx.xxx.xxx"

for i in commits_list['edges']:
  i['node']['chatglm2-6b'] = ""
  demo = i['node']['message']
  demo = json.dumps(demo, ensure_ascii=False)

  chat = f'''Please analyze the following paragraph and categorize it according to the following criteria: "CVE fixes", "new security features", "new features other than security", "bug fixes", "performance optimization". The paragraph can be classified into one or more categories; if none of the above categories are satisfied, or if you cannot recognize the paragraph, please output "neither". Only tell me "CVE fixes", "new security features", "new features other than security", "bug fixes", "performance optimization" or "neither":
  {demo}
  '''

  chat_data = {
    "prompt": chat,
    "history": []
  }

  response_ai = requests.post(
    f"http://{AI_IP}:8000/",
    headers = {"Content-Type": "application/json"},
    json = chat_data
  )
  if response_ai.ok:
    ai_data = response_ai.json()
    i['node']['chatglm2-6b'] = json.dumps(ai_data['response'])
  else:
    i['node']['chatglm2-6b'] = json.dumps(response_ai.text)


f = open(f"./html/gcc-12.3.0-init.json","w")
f.write(json.dumps(commits_list))
f.close()