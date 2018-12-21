#-*- coding: utf-8 -*-
import json
import operator
import requests

# For event handling with thread
import multiprocessing as mp
from threading import Thread

from datetime import datetime
from selenium import webdriver
from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response

app = Flask(__name__)

filename = 'C:\github desktop\\bot_7\info.txt'

# Notice class
class Notice:
    def __init__(self):
        self.date = 0
        self.title = 0
        self.num = 0
        self.x_path = 0

# Alarm class
class Alarm:
    def __init__(self):
        self.type = 0
        self.title = 0
        self.time = 0


# 텍스트 파일을 불러옵니다.
corpus = 'corpus.txt'

# Read basic info
def read_info(filename):
    with open(filename) as file:
        for line in file:
            infos = line.split(",")
            # Slack Custom Token
            global slack_token
            slack_token = infos[0]
            global slack_client_id
            slack_client_id = infos[1]
            global slack_client_secret
            slack_client_secret= infos[2]
            global slack_verification
            slack_verification= infos[3]
            global sc
            sc= SlackClient(slack_token)
            # Temporary id. pwd
            global id
            id = infos[4]
            global pw
            pw = infos[5]
            # Crawl target url
            global url
            url = infos[6]
            global notice_url
            notice_url = infos[7]
            global alarm_url
            alarm_url = infos[8]
            # Dialog flow url and key
            global dialogflow_url
            dialogflow_url = infos[9]
            global authorization_key
            authorization_key = infos[10]

# Threading function
def processing_event(queue):
   while True:
       # Execute logic if the queue is not empty
       if not queue.empty():
           slack_event = queue.get()

           channel = slack_event["event"]["channel"]
           text = slack_event["event"]["text"]

           # Chambot crawl process logic execute
           keywords = _crawl_switch(text)

           sc.api_call(
               "chat.postMessage",
               channel=channel,
               text=keywords
           )

# Performing login
def login_selenium(_url, _id, _pw):
    # Load web driver
    driver = webdriver.Chrome("C:\Chrome Driver\chromedriver.exe")
    # Open browser
    driver.get(_url)
    # Fill out ID and password
    driver.find_element_by_name('userId').send_keys(_id)
    driver.find_element_by_name('userPwd').send_keys(_pw)
    # Login btn click using xpath
    driver.find_element_by_xpath('//*[@id="wrap"]/div/div/div[4]/form/div/div[2]/div[3]/a').click()
    return driver

# Performing attendance function
def attend_user(_url, _id, _pw):
    # Login with url
    driver = login_selenium(_url, _id, _pw)
    # Attendance btn component click
    driver.find_element_by_class_name('state').click()

# Performing departure function
def departure_user(_url, _id, _pw):
    # Login with url
    driver = login_selenium(_url, _id, _pw)
    # Departure btn component click
    driver.find_element_by_class_name('state2').click()

# Alarm page crawl
def alarm_crawling (_url, _alarm_url,_id, _pw) :
    driver = login_selenium(_url, _id, _pw)
    # Alarm url connect
    driver.get(_alarm_url)
    # Get data
    new_value = driver.find_element_by_css_selector('#paging > li.num.is-active').text
    # Make new alarm list
    alarms = []
    while 1 :
        old_value = new_value
        # Get page source
        sourcecode = driver.page_source
        soup = BeautifulSoup(sourcecode, 'html.parser')

        # Check the number of posts
        for all_list in soup.find_all('li', class_="position-base"):
            soup2 = BeautifulSoup(str(all_list), 'html.parser')
            # Extract unread data
            if (len(soup2.find_all('img', {'alt' : '안읽음'})) != 0) :
                for category in soup2.find_all('span', class_="text-group"):
                    alarm = Alarm()
                    alarm.type = category.get_text()
                    alarm.title = soup2.find_all('a', class_="title")[0].get_text()
                    alarm.time = soup2.find_all('span', class_="time")[0].get_text().replace('\t','').replace('\n','').replace(' ', '')
                    alarms.append(alarm)
        # Update data
        driver.find_element_by_css_selector("#paging > li.next > a").click()
        new_value = driver.find_element_by_css_selector('#paging > li.num.is-active').text
        # Break flag
        if old_value == new_value:
            break
        else:
            pass
    # Make response string
    results = ""
    for i in range(0, len(alarms)) :
        _str = "[" + alarms[i].time + "]["+alarms[i].type+"] " + alarms[i].title +'\n'
        results += _str
        print(_str)
    if results =="" :
        results = "새로운 알람이 없습니다."
    return results

# Dialogflow execute and result
def get_dialogflow_response(_dialogflow_url, _authorization_key, text, user_key):
    # Make request
    data_send = {
        'query': text,
        'sessionId': user_key,
        'lang': 'ko',
    }
    data_header = {
        'Authorization': _authorization_key,
        'Content-Type': 'application/json; charset=utf-8'
    }
    # Request and get response
    res = requests.post(_dialogflow_url, data=json.dumps(data_send), headers=data_header)
    # Check status code
    if res.status_code != requests.codes.ok:
        return 'Dialogflow error occured'

    # Return dialogflow response speech
    data_receive = res.json()
    return data_receive['result']['fulfillment']['speech']

# Make notice data using selenium
def make_notice_selenium(_login_url, _notice_url,_id, _pw, dialog_text):
    # Login with url
    driver = login_selenium(_login_url, _id, _pw)
    # Open browser
    driver.get(_notice_url)

    # Make notice list
    list = []
    # default-tb1
    try:
        # Extract data using xpath
        for i in range(1, 1000):
            notice = Notice()
            notice.date = driver.find_element_by_xpath(
                '// *[@id="wrap"]/form/div/div[2]/div/div[1]/table[1]/tbody/tr[' + str(i) + ']/td[3]/span').text
            notice.title = driver.find_element_by_xpath(
                '// *[ @ id = "wrap"] / form / div / div[2] / div / div[1] / table[1] / tbody / tr[' + str(i) + '] / td[2] / a ').text
            notice.x_path = '// *[ @ id = "wrap"] / form / div / div[2] / div / div[1] / table[1] / tbody / tr[' + str(i) + '] / td[2] / a '
            list.append(notice)
    except:
        # Extract date data using xpath
        for i in range(0, len(list)):
            print(str(i+1) + ".[" + list[i].date + "] " + list[i].title)
        print("tb1 date finish")
        pass

    # default-tb1 type2
    try:
        # Extract date data using xpath
        notice = Notice()
        notice.date = driver.find_element_by_xpath(
            '//*[@id="wrap"]/form/div/div[2]/div/div[1]/table[2]/tbody/tr/td[3]/span').text
        notice.title = driver.find_element_by_xpath(
            '// *[ @ id = "wrap"] / form / div / div[2] / div / div[1] / table[2] / tbody / tr / td[2] / a').text
        notice.x_path = '// *[ @ id = "wrap"] / form / div / div[2] / div / div[1] / table[2] / tbody / tr / td[2] / a'
        list.append(notice)
    except:
        # Extract date data using xpath
        try:
            for i in range(1, 1000):
                print(driver.find_element_by_xpath(
                    '// *[@id="wrap"]/form/div/div[2]/div/div[1]/table[1]/tbody/tr[' + str(i) + ']/td[3]/span').text)
                notice = Notice()
                notice.date = driver.find_element_by_xpath(
                    '//*[@id="wrap"]/form/div/div[2]/div/div[1]/table[2]/tbody/tr[' + str(i) + ' ]/td[3]/span').text
                notice.title = driver.find_element_by_xpath(
                    '// *[ @ id = "wrap"] / form / div / div[2] / div / div[1] / table[2] / tbody / tr[' + str(i) + '] / td[2] / a').text
                notice.x_path = '// *[ @ id = "wrap"] / form / div / div[2] / div / div[1] / table[2] / tbody / tr[' + str(i) + '] / td[2] / a'
                list.append(notice)
        except:
            for i in range(0, len(list)):
                print(str(list[i].num) + ".[" + list[i].date + "] " + list[i].title)
            print("tb1 type2 date finish")
            pass

    # Sort list by date and numbering
    sorted_list = sorted(list, key=operator.attrgetter('date'), reverse=True)
    for i in range(0, len(sorted_list)):
        sorted_list[i].num = i + 1

    # Make results
    keywords = []
    # Check number of responses
    # Recent 3
    if dialog_text.find("default") != -1:
        keywords.append("====================================================")
        keywords.append("       최신 공지사항입니다. (3/" + str(len(sorted_list))+")")
        keywords.append("====================================================")
        # Recent 3 data
        if len(sorted_list) > 0:
            for i in range(0, 3):
                keywords.append(str(sorted_list[i].num) + ".[" + sorted_list[i].date + "] " + sorted_list[i].title)
        keywords.append("\n* 전체 공지사항을 보시려면 '전체 공지사항'을 입력하세요.")
    # All notices
    elif dialog_text.find("all") != -1:
        keywords.append("====================================================")
        keywords.append("      전체 공지사항입니다.")
        keywords.append("====================================================")
        for i in range(0, len(sorted_list)):
            keywords.append(str(sorted_list[i].num) + ".[" + sorted_list[i].date + "] " + sorted_list[i].title)
        keywords.append("\n* 공지내용을 보시려면 'N번째 공지'을 입력하세요.")
    # Today notice
    elif dialog_text.find("today") != -1 :
        # Get today data
        today_str = datetime.today().strftime("%Y.%m.%d")
        keywords.append("====================================================")
        keywords.append("      오늘(" + today_str + ") 공지사항입니다.")
        keywords.append("====================================================")
        for i in range(0, len(sorted_list)):
            if sorted_list[i].date == today_str:
                keywords.append(str(sorted_list[i].num) + ".[" + sorted_list[i].date + "] " + sorted_list[i].title)
        if len(keywords) <= 3 :
            keywords.append(" * 오늘(" + today_str + ") 공지가 없습니다.")
    # Request monthly
    elif dialog_text.find("month-") != -1 : # 해당 달 요청
        month_str = dialog_text.split("month-")[1]
        dates = month_str.split("-")
        cur_month = dates[0] + "." + dates[1]
        keywords.append("====================================================")
        keywords.append("      " + dates[1] + "월 공지사항입니다.")
        keywords.append("====================================================")
        for i in range(0, len(sorted_list)):
            if sorted_list[i].date.find(cur_month) != -1:
                keywords.append(str(sorted_list[i].num) + ".[" + sorted_list[i].date + "] " + sorted_list[i].title)
        if len(keywords) <= 3 :
            keywords.append(" * " + cur_month + " 공지가 없습니다.")
    # Request numbering
    else:
        num = int(dialog_text.split("-")[1]) - 1
        keywords.append("====================================================")
        keywords.append("      " + str(num + 1) + "번째 공지사항입니다.")
        keywords.append("====================================================")
        for i in range(0, len(sorted_list)):
            if i == num :
                # Extract and read detail content
                driver.find_element_by_xpath(sorted_list[i].x_path).click()
                keywords.append("<<< [" + sorted_list[i].date + "] " + sorted_list[i].title +">>>\n")
                keywords.append(driver.find_element_by_class_name('datail-content').text)
                driver.execute_script("window.history.go(-1)")

    ''' # Analyze xpath data
    // *[ @ id = "wrap"] / form / div / div[2] / div / div[1] / table[1] / tbody / tr[1] / td[2] / a        //*[@id="wrap"]/form/div/div[2]/div/div[1]/table[1]/tbody/tr[1]/td[3]/span
    // *[ @ id = "wrap"] / form / div / div[2] / div / div[1] / table[1] / tbody / tr[2] / td[2] / a        //*[@id="wrap"]/form/div/div[2]/div/div[1]/table[1]/tbody/tr[2]/td[3]/span
    // *[ @ id = "wrap"] / form / div / div[2] / div / div[1] / table[1] / tbody / tr[3] / td[2] / a        //*[@id="wrap"]/form/div/div[2]/div/div[1]/table[1]/tbody/tr[3]/td[3]/span
    // *[ @ id = "wrap"] / form / div / div[2] / div / div[1] / table[1] / tbody / tr[4] / td[2] / a        //*[@id="wrap"]/form/div/div[2]/div/div[1]/table[1]/tbody/tr[4]/td[3]/span

    // *[ @ id = "wrap"] / form / div / div[2] / div / div[1] / table[2] / tbody / tr / td[2] / a           //*[@id="wrap"]/form/div/div[2]/div/div[1]/table[2]/tbody/tr/td[3]/span
    '''

    # Attach u to support korean
    return u'\n'.join(keywords)

# Crawl branch
def _crawl_switch(text):
    # Get dialogflow data
    dialog_result = get_dialogflow_response(dialogflow_url, authorization_key, str(text).split("> ")[1], 'session')
    # Check response
    print("Ask : " + str(text).split("> ")[1] + "\nAnswer : " + dialog_result)

    # Branch
    if dialog_result.find("notice") != -1:
        return make_notice_selenium(url, notice_url, id, pw, dialog_result)
    elif dialog_result.find("alarm") != -1:
        return alarm_crawling(url, alarm_url, id, pw)
    elif dialog_result.find("attendance") != -1:
        attend_user(url, id, pw)
        return id + "님이 정상 입실되었습니다."
    elif dialog_result.find("departure") != -1:
        departure_user(url, id, pw)
        return id + "님이 정상 퇴실되었습니다."
    else:
        return dialog_result

# Event handling
def _event_handler(event_type, slack_event):
    # Using multiprocessing queue enqueue and response immediately to avoid request again
   if event_type == "app_mention":
       event_queue.put(slack_event)
       return make_response("App mention message has been sent", 200, )

# For slack verification
@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)
    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                                 "application/json"})

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})

@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"

if __name__ == '__main__':
    read_info(filename)
    # Use multiprocessing event queue to handle event
    event_queue = mp.Queue()

    p = Thread(target=processing_event, args=(event_queue,))
    p.start()
    print("subprocess started")

    app.run('0.0.0.0', port=8080)
    p.join()
