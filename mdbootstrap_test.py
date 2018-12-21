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
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    print("ok")
    result = 7
    result2 = [
        ['나동빈', 75, 38, 55],
        ['홍길동', 80, 95, 100],
        ['박동익', 70, 80, 90]
    ]
    return render_template("full-page-gallery.html", result =result, result2 = result2)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)