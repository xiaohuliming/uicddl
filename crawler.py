import json
import re
import requests
import time
from bs4 import BeautifulSoup
import csv

# 打开CSV文件
f = open("data2.csv", mode="w", encoding="utf-8")
csvwriter = csv.writer(f)

# 获取用户名和密码
username = input("Please enter your username: ")
password = input("Please enter your password: ")

# 时间戳转化为字符串
def timestamp_to_timestr(timestamp):
    tre_timeArray = time.localtime(timestamp)
    return time.strftime("%Y-%m-%d %H:%M:%S", tre_timeArray)

# 模拟浏览器请求头
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
}


# 获取登录后的cookie值
def get_login_cookie(su, sp):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    session = requests.Session()
    session.headers = headers
    resp = session.get("https://ispace.uic.edu.cn/login/index.php")
    html = BeautifulSoup(resp.text, "lxml")
    login_token = html.find("input", attrs={"name": "logintoken"}).get("value")

    data = {
        "logintoken": login_token,
        "username": su,
        "password": sp
    }
    resp = session.post(
        "https://ispace.uic.edu.cn/login/index.php",
        data=data,
    )

    session.get("https://ispace.uic.edu.cn/login/index.php?testsession=13040")

    cookie = {}
    for key, value in session.cookies.items():
        cookie[key] = value
    return cookie


cookie = get_login_cookie(username, password)


# 获取课程ddl
def get_class_ddl():
    # 获取key
    url = "https://ispace.uic.edu.cn/my/"
    resp = requests.get(url, headers=headers, cookies=cookie)
    key = re.search('"sesskey":"(?P<key>.*?)",', resp.text).group("key")

    # 准备发送请求
    url = f"https://ispace.uic.edu.cn/lib/ajax/service.php?sesskey={key}&info=core_calendar_get_action_events_by_timesort"
    data = "[{\"index\":0,\"methodname\":\"core_calendar_get_action_events_by_timesort\",\"args\":{\"limitnum\":6,\"timesortfrom\":1720713600,\"limittononsuspendedevents\":true}}]"

    # 发送请求
    resp = requests.post(
        url=url,
        data=data,
        headers=headers,
        cookies=cookie
    )

    # 遍历循环每个ddl
    ret_dic_ls = []
    for json_data in resp.json():
        json_data = json_data["data"]["events"]
        for event in json_data:
            name = event["activityname"]
            time_str = re.search('time=(?P<time>.*?)"', event["formattedtime"]).group("time")
            time_str = timestamp_to_timestr(int(time_str))
            class_name = event["course"]["fullname"]
            if {
                "name": name,
                "time": time_str,
                "class": class_name
            } not in ret_dic_ls:
                print({
                    "name": name,
                    "time": time_str,
                    "class": class_name
                })
                ret_dic_ls.append(
                    {
                        "name": name,
                        "time": time_str,
                        "class": class_name
                    }
                )

    # 循环翻页
    next_id = resp.json()[0]["data"]["lastid"]
    limit_count = 11
    while True:
        data = (
            "[{\"index\":0,\"methodname\":\"core_calendar_get_action_events_by_timesort\",\"args\":{\"aftereventid\":"
            f"{next_id - 1}"
            ",\"limitnum\":"
            f"{limit_count}"
            ",\"timesortfrom\":1720713600,\"limittononsuspendedevents\":true}}]")
        try:
            resp = requests.post(
                url=url,
                data=data,
                headers=headers,
                cookies=cookie
            )
            next_id = resp.json()[0]["data"]["lastid"]
        except:
            break
        for json_data in resp.json():
            json_data = json_data["data"]["events"]
            for event in json_data:
                name = event["activityname"]
                time_str = re.search('time=(?P<time>.*?)"', event["formattedtime"]).group("time")
                time_str = timestamp_to_timestr(int(time_str))
                class_name = event["course"]["fullname"]
                if {
                    "name": name,
                    "time": time_str,
                    "class": class_name
                } not in ret_dic_ls:
                    print({
                        "name": name,
                        "time": time_str,
                        "class": class_name
                    })
                    ret_dic_ls.append(
                        {
                            "name": name,
                            "time": time_str,
                            "class": class_name
                        }
                    )
        limit_count += 5

    return ret_dic_ls


ret_dic_ls = get_class_ddl()
print(len(ret_dic_ls))
# print(ret_dic_ls)
# 写入表头
csvwriter.writerow(['name', 'time', 'class'])
# 遍历字典列表，写入每行数据
for data in ret_dic_ls:
    csvwriter.writerow([data['name'], data['time'], data['class']])
# 关闭文件
f.close()
# csvwriter.writerow(ret_dic_ls)
print("done")