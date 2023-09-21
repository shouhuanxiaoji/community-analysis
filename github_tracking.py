#!/usr/bin/env python3
# This is a python3 module for obtaining all branches list of all repos
# It Uses GraphQL Api for github and gitlab
# needed these modules: requests gitpython
# github test token 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
# gitlab(gitlab.gnome.org) test token ggopatPAQoirjNB3mQ79wxEyqy
# 获取tag对应branch的办法是，首先找到tag对应的commit，然后找到commit所属的branch(可能有多个)
import requests
import json
import os
from datetime import datetime,timedelta
import itertools
import time
#字典切片函数（即将一个大的字典切换为若干小字典）
def batch_iter(iterable, batch_size):
    iterator = iter(iterable)
    while True:
        batch = dict(itertools.islice(iterator, batch_size))
        if not batch:
            break
        yield batch

token = "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"
apiurl = 'https://api.github.com/graphql'
headers = {
  "Authorization": f"token {token}",
  "GraphQL-Features": "timeline-preview",
  "Content-Type": "application/json"
}

json_file = "metadata.json"
json_file_new = "metadata.json.new"
os.system("rm -rf " + json_file_new)
os.system("touch " + json_file_new)

json_file_new_obj = open(json_file_new, mode="w", buffering = -1, encoding="UTF-8")
json_file_obj = open(json_file, mode="r", buffering = -1, encoding="UTF-8")
json_data = json.load(json_file_obj)
json_github_data = {
  "total_count": 0,
  "lists": {}
}
total_count = 0
# github graphql api服务器对请求数据规模有限制，经过测试，同时发250条没有问题，为此需要拆分json为多个子字典
count_valve = 200
valve_list = 0

# github的软件数量，且组件一个新的字典，字典内为所有github的条目
for srpm in json_data['lists'].keys():
  if json_data['lists'][srpm]['repo_platform'] == "github":
    total_count = total_count + 1
    json_github_data["lists"][srpm] = json_data["lists"][srpm]
    json_github_data["lists"][srpm]["index"] = total_count
json_github_data["total_count"] = total_count

###############################
#获取tag 对应 commit oid 
###############################

# github api返回json
'''
{
'speex': {'ref': {'target': {'target': {'oid': '5dceaaf3e23ee7fd17c80cb5f02a838fd6c18e01', 'committedDate': '2022-06-11T19:39:11Z'}}}} [, Next item]
}
'''
github_oid_data = {}

# 当软件数量小于count_valve时，执行一次查询即可
if total_count <= count_valve:
  # 获取tag对应的commit oid的查询graphql
  query_tag_oid = """
  query {
  """
  for srpm in json_github_data['lists'].keys():
    repo_alias = srpm
    # graphql别名只允许字母和下划线，不允许其他字符
    # "-"替换为"__MINUS__"
    if "-" in repo_alias:
      repo_alias = repo_alias.replace("-", "__MINUS__")
    # "."替换为"__DOT__"
    if "." in repo_alias:
      repo_alias = repo_alias.replace(".", "__DOT__")
    query_tag_oid_list = f"""
      {repo_alias}: repository(owner: "{json_data['lists'][srpm]['repo_owner']}", name: "{json_data['lists'][srpm]['repo_name']}") {{
        ref(qualifiedName: "refs/tags/{json_data['lists'][srpm]['repo_tag']}") {{
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
    """
    query_tag_oid = query_tag_oid + query_tag_oid_list

  query_tag_oid = query_tag_oid + """
  \n}"""

  response = requests.post(
    apiurl, 
    headers=headers, 
    json={"query": query_tag_oid}
  )

  if response.ok:
    github_oid_data = (response.json())["data"]
  else:
    print("Error:", response.text)
# 软件数量大于阈值时，需要如下操作：
# 先切片字典，分批查询
# 然后合并返回的字典
else:
  for batch in batch_iter(json_github_data['lists'].items(), count_valve):
    # 获取tag对应的commit oid的查询graphql
    query_tag_oid = """
    query {
    """
    for srpm in batch.keys():
      repo_alias = srpm
      # graphql别名只允许字母和下划线，不允许其他字符，故进行转义
      # "-"替换为"__MINUS__"
      if "-" in repo_alias:
        repo_alias = repo_alias.replace("-", "__MINUS__")
      # "."替换为"__DOT__"
      if "." in repo_alias:
        repo_alias = repo_alias.replace(".", "__DOT__")
      query_tag_oid_list = f"""
        {repo_alias}: repository(owner: "{batch[srpm]['repo_owner']}", name: "{batch[srpm]['repo_name']}") {{
          ref(qualifiedName: "refs/tags/{batch[srpm]['repo_tag']}") {{
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
      """
      query_tag_oid = query_tag_oid + query_tag_oid_list
    query_tag_oid = query_tag_oid + """
    \n}"""
    response = requests.post(
      apiurl, 
      headers=headers, 
      json={"query": query_tag_oid}
    )

    if response.ok:
      github_oid_data = { **github_oid_data, **((response.json())["data"]) }
    else:
      print("get_commit_Error:", response.text)
    time.sleep(5)

###############################
# 获取tag 对应 branches
# 首先依据软件名，查询仓库的branches列表
# 查询列表的同时，筛选出tag对应时间点的 oid，即寻找与一个tag发布时间相同的branches的tag
# 最后对比两个tag的oid是否一致，如果一致，则说明tag属于这个(些)branch
###############################
# 如果json文件内容为空，说明是第一次查询，需要全量查询commits
# 如果json文件不为空，说明不是第一次查询，从上次结束的commits接着查即可
github_branches_data = {}

#经过测试，阈值大于25时api返回结果有几率报错
count_valve = 25
# 软件数量小于阈值时，执行一次即可
if total_count <= count_valve:
  # 获取tag对应的commit oid的查询graphql
  query_tag_branches = """
  query {
  """
  # github_oid_data中的key是已经经过转义的srpm字符串
  for repo_alias in github_oid_data.keys():
    if github_oid_data[repo_alias]["ref"] == None:
      commit_oid = "0"
      commit_date = "0"
    else:
      commit_oid = github_oid_data[repo_alias]["ref"]["target"]["target"]["oid"]
      commit_date = github_oid_data[repo_alias]["ref"]["target"]["target"]["committedDate"]
    query_tag_branches_list = f"""
      {repo_alias}: repository(owner: "{json_data['lists'][repo_alias]['repo_owner']}", name: "{json_data['lists'][repo_alias]['repo_name']}") {{
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
    """
    query_tag_branches = query_tag_branches + query_tag_branches_list

  query_tag_branches = query_tag_branches + """
  \n}"""

  response2 = requests.post(
    apiurl, 
    headers=headers, 
    json={"query": query_tag_branches}
  )

  if response2.ok:
    github_branches_data = (response2.json())["data"]
  else:
    print("Error:", response2.text)
# 软件数量大于阈值时，需要如下操作：
# 先切片字典，分批查询
# 然后合并数据字典
else:
  for batch in batch_iter(github_oid_data.items(), count_valve):
    # 获取tag对应的commit oid的查询graphql
    query_tag_branches = """
    query {
    """
    for repo_alias in batch.keys():
      if github_oid_data[repo_alias] == None:
        continue
      else:
        if github_oid_data[repo_alias]["ref"] == None:
          continue
        else:
          if "target" in github_oid_data[repo_alias]["ref"]["target"].keys():
            commit_oid = github_oid_data[repo_alias]["ref"]["target"]["target"]["oid"]
            commit_date = github_oid_data[repo_alias]["ref"]["target"]["target"]["committedDate"]
          else:
            commit_oid = github_oid_data[repo_alias]["ref"]["target"]["oid"]
            commit_date = github_oid_data[repo_alias]["ref"]["target"]["committedDate"]
      srpm = repo_alias
      # "__MINUS__"替换为"-"
      if "__MINUS__" in srpm:
        srpm = srpm.replace("__MINUS__", "-")
      # "__DOT__"替换为"."
      if "__DOT__" in srpm:
        srpm = srpm.replace("__DOT__", ".")
      query_tag_branches_list = f"""
        {repo_alias}: repository(owner: "{json_data['lists'][srpm]['repo_owner']}", name: "{json_data['lists'][srpm]['repo_name']}") {{
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
      """
      query_tag_branches = query_tag_branches + query_tag_branches_list

    query_tag_branches = query_tag_branches + """
    }
    """

    response2 = requests.post(
      apiurl, 
      headers=headers, 
      json={"query": query_tag_branches}
    )

    if response2.ok:
      github_branches_data = { **github_branches_data, **((response2.json())["data"]) }
    else:
      print("get_branches_Error:", response2.text)
    time.sleep(5)

for repo in github_branches_data.keys():
  if "target" in github_oid_data[repo]["ref"]["target"].keys():
    commit_oid = github_oid_data[repo]["ref"]["target"]["target"]["oid"]
  else:
    commit_oid = github_oid_data[repo]["ref"]["target"]["oid"]

  srpm = repo
  # "__MINUS__"替换为"-"
  if "__MINUS__" in srpm:
    srpm = srpm.replace("__MINUS__", "-")
  # "__DOT__"替换为"."
  if "__DOT__" in srpm:
    srpm = srpm.replace("__DOT__", ".")
    
  json_data['lists'][srpm]["tag_oid"] = commit_oid

  for branches in github_branches_data[repo]["refs"]["edges"]:
    if len(branches["node"]["target"]["history"]["edges"]) == 1:
      if branches["node"]["target"]["history"]["edges"][0]["node"]["oid"] == commit_oid:
        branch_name = branches["node"]["name"]
        json_data['lists'][srpm]["repo_branches"][branch_name] = ""

###############################
# 获取对应branch的commits信息（先循环软件，再循环分支，最后循环翻页，总计要三次循环）
# 如果指定了分支，则只获取指定分支的数据
# 写入对应的json文件内
###############################
# json文件格式为:
# {
#  "branche1": {
#    [{
#      "commit_oid": "xxxx",
#      "commit_message": "xxxx",
#      "commit_date": "xxxx",
#      "commit_author": ""
#      "message_analysis": {
#        # chatglm6b-2
#        "glm6b_2": ["cve", "bugfix", "performance optimization", "new security features", "others"],
#        # 手动标记
#        "manual": [],
#        # 根据简单规则的判断
#        "noob_engine": []
#      }
#    }]
#  },
#  "branche2":{}
#}


'''
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

#循环翻页
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

  chat = f"""Please analyze the following paragraph and categorize it according to the following criteria: "CVE fixes", "new security features", "new features other than security", "bug fixes", "performance optimization". The paragraph can be classified into one or more categories; if none of the above categories are satisfied, or if you cannot recognize the paragraph, please output "neither". Only tell me "CVE fixes", "new security features", "new features other than security", "bug fixes", "performance optimization" or "neither":
  {demo}
  """

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

'''

json_file_new_obj.write(json.dumps(json_data))
json_file_new_obj.close()
json_file_obj.close()
os.system("rm -rf " + json_file)
os.system("mv " + json_file_new + " " + json_file)