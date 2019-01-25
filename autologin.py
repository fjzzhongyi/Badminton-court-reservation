# -*- coding:utf-8 -*-
# author: fjzzhongyi@163.com
from splinter.browser import Browser
import os, time, sys
from time import sleep
import json, re, traceback
import datetime

class AutoLogin:

    net_url = 'http://auth4.tsinghua.edu.cn/'
    sleep_interval = 15 * 60 # time interval to login: unit--second 

    def __init__(self, config_path):
        with open(config_path, 'r') as fr:
            config = json.load(fr)
        self.username = config["username"]
        self.password = config["password"]


    def connect_net(self):
        self.driver_name = 'chrome'
        self.driver_path = os.getcwd() + '/chromedriver'
        self.driver = Browser(driver_name=self.driver_name, executable_path=self.driver_path)
        self.driver.driver.set_window_size(1400, 1000)
        self.driver.visit(self.net_url)
        sleep(0.8)
        try:
            self.driver.fill('username', self.username)
            self.driver.fill('password', self.password)
            self.driver.find_by_id('connect').click()
            sleep(0.5)
            # race condition: may conflict with other orders
            alert = self.driver.get_alert()
            alert.accept()
            alert.dismiss()
        except BaseException, e:
            traceback.print_exc()
            print('has loged in') 
        finally:
            self.driver.quit() 


    def run(self):
        while True:
            self.connect_net()
            sleep(self.sleep_interval)

        
if __name__=='__main__':
    gb = AutoLogin('./config.json') 
    gb.run()
