#!/usr/bin/env python3
# This is a python3 module for analysing commits
# json文件格式为:
# {
#  "branche1": [
#    {
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
#    },
#   {...}
#  ],
#  "branche2":[]
import requests
import json
import os

json_file = "metadata.json"
json_file_obj = open(json_file, mode="r", buffering = -1, encoding="UTF-8")
json_data = json.load(json_file_obj)

for srpm in json_data['lists'].keys():
  # 当前只支持github，因此筛选，未来会增加gitlab
  if not json_data['lists'][srpm]['repo_platform'] == "github":
    continue
  commit_file_new = json_data['lists'][srpm]["local_file"] + ".new"
  commit_file = json_data['lists'][srpm]["local_file"]
  os.system("rm -f " + commit_file_new)
  os.system("touch " + commit_file_new)
  commits_new_obj = open(commit_file_new, mode="w", buffering = -1, encoding="UTF-8")
  commits_obj = open(commit_file, mode="r", buffering = -1, encoding="UTF-8")
  commits_json_data = json.load(commits_obj)
  # 因为各种原因，未获取到commit数据
  if commits_json_data == {} or commits_json_data is None:
    continue
  for branch in commits_json_data:
    # 因为各种原因，未获取到branch的commits数据
    if branch == []:
      continue
    print(branch)
    print(branch[1])
  commits_new_obj.close()
  commits_obj.close()
    
###############################
# 使用三类引擎进行commit分析
# 结果分类："CVE fixes", "new security features", "new features other than security", "bug fixes", "performance optimization"
###############################
'''

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