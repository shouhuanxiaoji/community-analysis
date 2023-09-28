#!/usr/bin/env python3
# This is a python3 module for obtaining all branches list of all repos
# It Uses GraphQL Api for github and gitlab
# needed these modules: requests gitpython
# github test token1 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
# github test token2 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
# gitlab(gitlab.gnome.org) test token ggopatPAQoirjNB3mQ79wxEyqy
# 获取tag对应branch的办法是，首先找到tag对应的commit，然后找到commit所属的branch(可能有多个)
import requests

token = "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"
apiurl = 'https://api.github.com/graphql'
headers = {
  "Authorization": f"token {token}",
  "GraphQL-Features": "timeline-preview",
  "Content-Type": "application/json"
}


###############################
# 获取对应branch的commits信息（先循环软件，再循环分支，最后循环翻页，总计要三次循环）
# 如果指定了分支，则只获取指定分支的数据
# 写入对应的json文件内
# 如果json_data['lists'][repo]['repo_branches']中branch的值为空且json_data['lists'][repo]['tag_oid']不为空，说明是第一次查询，需要全量查询commits
# 否则认为已经查询过数据，此时原子写入新数据即可
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
commit_cursor = "d00c742403d74da3ca532e335ca03c189644db8e 0" 
branch_get_commits = F"""
query {{
  repository(owner: "gdraheim", name: "zziplib") {{
   ref(qualifiedName: "develop") {{
      target {{
        ... on Commit {{
          history(first: 40 {', after: "' + commit_cursor + '"' if commit_cursor else ''}, since: "2021-01-05T07:05:00Z") {{
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
                parents(first: 100) {{
                  nodes {{
                    message
                    oid
                    committedDate
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

response3 = requests.post(
  apiurl, 
  headers=headers, 
  json={"query": branch_get_commits}
)

if response3.ok:
  data3 = response3.json()
  print(data3)
else:
  print("Error:", response3.text)