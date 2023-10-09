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
#        "glm6b_2": ["CVE", "bugfix", "performance-optimization", "security-issue", "others"],
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
import time

chatglm2_6b_ip = "9.134.126.222"
chatglm2_6b_port = "16001"
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
  for branch in commits_json_data.keys():
    # 因为各种原因，未获取到branch的commits数据
    if branch == []:
      continue
    for node in commits_json_data[branch]:
      message = node['commit_message']
      # noob-engine
      ################################################################################
      # 未来计划通过打通github 安全公告，解决cve问题
      # github graphql 有vulnerabilityAlerts字段，筛选一个repo对应的安全公告
      # 调出其cve id和description，筛选description中的commit，即可对应一个cve和commit
      ################################################################################
      cve_string = ("ghsa-", "GHSA-", "cve-", "CVE-")
      performance_string = ("perform", "behavior", "improve", "raise", "optimiz")
      bugfix_string = ("bug")
      security_string = ("security")
      # cve_string中的元素是否在 message 中
      if any(i in cve_string for i in message):
        (node['message_analysis']['noob_engine']).append("CVE")
      if any(i in performance_string for i in message):
        (node['message_analysis']['noob_engine']).append("performance-optimization")
      if any(i in bugfix_string for i in message):
        (node['message_analysis']['noob_engine']).append("bugfix")
      if any(i in security_string for i in message):
        (node['message_analysis']['noob_engine']).append("security-issue")

      demo = json.dumps(message, ensure_ascii=False)
      print("Ask: --------------------------------")
      print(demo)
      print("Answer: +++++++++++++++++++++++++++++")
      # chatglm2-6b engine
      '''      
      chat = f"""对于以下段落，如果其中涉及“CVE”、“新增安全特性”、“性能改进”、“bugfix”、“新功能”等之一，只提供结论即可；如果都不是，则仅回复“都不是”:
      {demo}
      """

      glm2_chat_data = {
        "prompt": chat,
        "history": [],
        "max_length": 4096
      }

      response_glm2 = requests.post(
        f"http://{chatglm2_6b_ip}:{chatglm2_6b_port}/",
        headers = {"Content-Type": "application/json"},
        json = glm2_chat_data,
      )
      if response_glm2.ok:
        glm2_data = response_glm2.json()
        print(glm2_data)
        #commits_json_data[branch][node]['message_analysis']['noob_engine'].append(glm2_data['response'])
      else:
        print("chatglm2-6b error:" + response_glm2.text)
      time.sleep(0.2)
      '''
      # llama2 engine
      chat = f"""The following are git commit messages. Please categorize them into the following categories: "Bug Fix", "Performance Optimization", "Common Vulnerabilities and Exposures", "New Feature or Functions", "Document Improvement", "CI/CD Improvement", "Test Improvement" and "Other". Your answer can only be one of these categories. If it contains the word "cve" or "ghsa", please answer "CVE". If it contains the word "fix" or "bugs", please answer "Bug Fix". If it contains the word "performance", please answer "Performance Optimization". If it contains the words "new feature" or "new function", please answer "New Feature or Functions".If it contains the words "doctest", please answer "Test Improvement" :
      {demo}
      """

      glm2_chat_data = {
        "messages": [
          {
          "role": "user",
          "content": chat
          }
        ]
      }

      response_glm2 = requests.post(
        f"http://{chatglm2_6b_ip}:{chatglm2_6b_port}/chat",
        headers = {"Content-Type": "application/json"},
        json = glm2_chat_data,
      )
      if response_glm2.ok:
        glm2_data = response_glm2.json()
        print(glm2_data["choices"][0]["message"]["content"])
        # commits_json_data[branch][node]['message_analysis']['noob_engine'].append(glm2_data['response'])
      else:
        print("chatglm2-6b error:" + response_glm2.text)
      # 5 items per second
      time.sleep(0.2)
  commits_new_obj.close()
  commits_obj.close()
  
###############################
# 使用三类引擎进行commit分析
# 结果分类："CVE fixes", "new security features", "new features other than security", "bug fixes", "performance optimization"
###############################

