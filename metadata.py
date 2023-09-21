#!/usr/bin/python3
# data struction: 
# {'total_count': 1, 
#  'lists': {
#   'golang': {  
#     'os_name': 'golang',
#     'os_version': '1.0',
#     github/gitlab/bitbucket etc
#     'repo_platform': 'github',
#     'repo_owner': 'Golang',
#     'repo_name': 'Go',
#     'repo_tag': 'v1.0',
#     'tag_oid': '9123asdas123sdfasdaasfsdf',
#     这里描述分支名及最新的commit oid
#     'repo_branches': {'v1.0': '0sadsdgasdqwesdzfasdasdasd', 'v1.0-fix': 'qwesadfsdfawrwearaerw123'},
#     'last_update_time': '20230916T154420Z'
#     'local_file': 'data/Golang__v1.0.json',
#   }
#  }
# }

# 更新逻辑：
# 每次更新srpm列表，然后增量更新到json中
# json与yaml比较，当软件的repo_platform为空，或值不等于github/gitlab/gnome.gitlab时删除该目标

import os
import json
import yaml
import subprocess

#  处理正则|
def un_regex_or(str):
    pass

# 处理正则^
def un_regex_prefix(str):
    return str.strip("^")

total_count = 0

# update repo metadata_srpm
os.system("dnf makecache")
print("Update repo metadata_srpm, OK!")

# grab all srpm list in file
## there is a dubble-checking with grep and python check to ensure only "xxx.src" will be existing in txt
metadata_srpm_tmp = "metadata_srpm.txt.tmp"
metadata_srpm = "metadata_srpm.txt"
os.system("rm -f " + metadata_srpm + " && touch " + metadata_srpm)
os.system("rm -f " + metadata_srpm_tmp)
os.system("dnf repoquery --srpm --all | grep '.src' > " + metadata_srpm_tmp)
metadata_srpm_obj_tmp = open(metadata_srpm_tmp, mode = "r", buffering = -1, encoding = "UTF-8")
metadata_srpm_obj = open(metadata_srpm, mode = "a", buffering = -1, encoding = "UTF-8")
metadata_srpm_lines_tmp = metadata_srpm_obj_tmp.readlines()
for line in metadata_srpm_lines_tmp:
    if ".src" in line:
        metadata_srpm_obj.write(line)
        total_count = total_count + 1
metadata_srpm_obj_tmp.close()
metadata_srpm_obj.close()

if total_count == 0:
    raise Exception("请检查rpm仓库配置文件或python代码，获取到0条srpm记录，请尝试手动运行 dnf repoquery --srpm --all")

os.system("rm -f " + metadata_srpm_tmp)

# filter objects for json
# line: pkgname-version-dist.src.rpm
json_file = "metadata.json"
json_file_new = "metadata.json.new"
## initial
if not os.path.exists(json_file):
    # 创建json文件结构
    json_data_init = {
        "total_count": total_count,
        "lists": {}
    }
    # 创建json文件
    os.system("touch " + json_file)    
    json_file_obj = open(json_file, mode="w", encoding="UTF-8")
    ## json内容写入版本号
    metadata_srpm_obj = open(metadata_srpm, mode = "r", buffering = -1, encoding = "UTF-8")
    metadata_srpm_obj_lines = metadata_srpm_obj.readlines()
    for line in metadata_srpm_obj_lines:
        line = line.strip()
        line_obj = line.rsplit("-", 2)
        line_data = {
            f"{line_obj[0]}": {
                'os_name': line_obj[0],
                'os_version': (line_obj[1]).split(":")[1],
                'repo_platform': '',
                'repo_owner': '',
                'repo_name': '',
                'repo_tag': '',
                'tag_oid': '',
                'repo_branches': {},
                'last_update_time': '',
                'local_file': f"data/{line_obj[0]}__{(line_obj[1]).split(':')[1]}.json"               
            }
        }
        ## 信息添加到json
        json_data_init["lists"][line_obj[0]] = line_data[line_obj[0]]
    ## 写入文件
    json_data_init_dumps = json.dumps(json_data_init)
    json_file_obj.write(json_data_init_dumps)
    #json_file_obj.write(json_data_init_dumps)
    json_file_obj.close
    metadata_srpm_obj.close

## update
else:
    os.system("rm -rf " + json_file_new)
    os.system("touch " + json_file_new)
    json_file_new_obj = open(json_file_new, mode="w", buffering = -1, encoding="UTF-8")
    json_file_obj = open(json_file, mode="r", buffering = -1, encoding="UTF-8")
    json_data = json.load(json_file_obj)
    metadata_srpm_obj = open(metadata_srpm, mode = "r", buffering = -1, encoding = "UTF-8")
    metadata_srpm_obj_lines = metadata_srpm_obj.readlines()
    for line in metadata_srpm_obj_lines:
        line = line.strip()
        line_obj = line.rsplit("-", 2)
        # 每次都同步json与srpm列表
        if not line_obj[0] in (json_data["lists"]).keys():
            line_data = {
                f"{line_obj[0]}": {
                    'os_name': line_obj[0],
                    'os_version': (line_obj[1]).split(":")[1],
                    'repo_platform': '',
                    'repo_owner': '',
                    'repo_name': '',
                    'repo_tag': '',
                    'tag_oid': '',
                    'repo_branches': {},
                    'last_update_time': '',
                    'local_file': f"data/{line_obj[0]}__{(line_obj[1]).split(':')[1]}.json"
                }
            }
            json_data["lists"][line_obj[0]] = line_data[line_obj[0]]

        # 更新版本信息
        if (line_obj[1]).split(':')[1] != json_data["lists"][line_obj[0]]["os_version"]:
            json_data["lists"][line_obj[0]]["os_version"] = (line_obj[1]).split(':')[1]
        # 删除软件,请看yaml处理部分

    ## 写入文件
    json_data_dumps = json.dumps(json_data)
    json_file_new_obj.write(json_data_dumps)
    json_file_obj.close
    json_file_new_obj.close
    metadata_srpm_obj.close

    ## 清理
    os.system("rm -f " + json_file)
    os.system("mv " + json_file_new + " " + json_file)


########################################################################

# 更新其他信息并创建数据文件
git_rpm_upgrade = "https://gitee.com/OpenCloudOS/pkgs-info.git"
git_dest_path = "./pkgs-info"
os.system("rm -rf pkgs-info")
try:
    # 执行git clone命令
    result = subprocess.run(['git', 'clone', git_rpm_upgrade, git_dest_path], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Clone {git_rpm_upgrade} successful!")
    else:
        print(f"Clone {git_rpm_upgrade} failed: {result.stderr}")
except Exception as e:
    print(f"Clone {git_rpm_upgrade} failed: {e}")

rpm_upgrade_infodir = "pkgs-info/upstream-info/"
filelists = os.listdir(rpm_upgrade_infodir)

os.system("rm -rf " + json_file_new)
os.system("touch " + json_file_new)
json_file_new_obj = open(json_file_new, mode="w", buffering = -1, encoding="UTF-8")
json_file_obj = open(json_file, mode="r", buffering = -1, encoding="UTF-8")
json_data = json.load(json_file_obj)

# 遍历yaml文件列表，获取信息
for filename in filelists:
    if filename.strip(".yaml") in (json_data["lists"]).keys():
        file_full_path = rpm_upgrade_infodir + filename
        rpm_upgrade_file_obj = open(file_full_path, mode="r", buffering = -1, encoding="UTF-8")
        yaml_data = yaml.safe_load(rpm_upgrade_file_obj)
        # platform must be github and gitlab
        if "repo_type" in yaml_data.keys():
            # 不属于github gitlab的条目删除
            if yaml_data["repo_type"] == "github" or yaml_data["repo_type"] == "gitlab.gnome" or yaml_data["repo_type"] == "gitlab":
                json_data["lists"][filename.strip(".yaml")]["repo_platform"] = yaml_data["repo_type"]
                # repo and name
                json_data["lists"][filename.strip(".yaml")]["repo_owner"] = ((yaml_data["src_repo"]).split('/'))[0]
                json_data["lists"][filename.strip(".yaml")]["repo_name"] = ((yaml_data["src_repo"]).split('/'))[1]
                # tag version
                tag_version = ""
                if "tag_separator" in yaml_data.keys():
                    if yaml_data["tag_separator"] == None:
                        tag_version = json_data["lists"][filename.strip(".yaml")]["os_version"]
                    else:
                        tag_version = json_data["lists"][filename.strip(".yaml")]["os_version"].replace(".", yaml_data["tag_separator"])
                else:
                    tag_version = json_data["lists"][filename.strip(".yaml")]["os_version"]
                json_data["lists"][filename.strip(".yaml")]["repo_tag"] = tag_version
                if "tag_prefix" in yaml_data.keys():
                    if yaml_data["tag_prefix"] == None:
                        pass
                    elif yaml_data["tag_prefix"] == "":
                        pass
                    else:
                        json_data["lists"][filename.strip(".yaml")]["repo_tag"] = un_regex_prefix(yaml_data["tag_prefix"]) + tag_version
                if "tag_suffix" in yaml_data.keys():
                    if yaml_data["tag_suffix"] == None:
                        pass
                    elif yaml_data["tag_suffix"] == "":
                        pass
                    else:
                        json_data["lists"][filename.strip(".yaml")]["repo_tag"] = tag_version + yaml_data["tag_suffix"]
            else:
                # 第一步清理json，当repo_platform在yaml中且不等于github、gitlab或gnome.gitlib时，若这些目标未在yaml中，则使用第二步清理
                (json_data["lists"]).pop(filename.strip(".yaml"), None)
                if filename.strip(".yaml") not in json_data["lists"]:
                    json_data['total_count'] = json_data['total_count'] - 1
        rpm_upgrade_file_obj.close()

# 第二步清理json，当repo_platform为空时删除目标，因为其还没有写入yaml或不支持平台
for srpm in json_data["lists"].copy():
    if json_data["lists"][srpm]["repo_platform"] == "":
        (json_data["lists"]).pop(srpm, None)
        if srpm not in json_data["lists"].keys():
            json_data['total_count'] = json_data['total_count'] - 1

# 创建数据文件
for srpm in json_data["lists"].keys():
    if not os.path.exists(json_data['lists'][srpm]['local_file']):
        os.system(f"touch {json_data['lists'][srpm]['local_file']}")

json_file_new_obj.write(json.dumps(json_data))
json_file_obj.close
json_file_new_obj.close
# 清理
os.system("rm -f " + json_file)
os.system("mv " + json_file_new + " " + json_file)
