# -*- coding:utf-8 -*-
# author: fjzzhongyi@163.com
from splinter.browser import Browser
import os, time, sys
from time import sleep
import json, re, traceback
import datetime

class AutoLogin:

    url1 = 'http://auth4.tsinghua.edu.cn/'
    url2 = 'http://net.tsinghua.edu.cn/'

    def __init__(self, config_dir,  config_path, minutes):
        with open(os.path.join(config_dir, config_path), 'r') as fr:
            config = json.load(fr)
        self.username = config["username"]
        self.password = config["password"]
        self.sleep_interval = minutes*60 # translate minutes to seconds
        self.config_dir = config_dir


    def connect_net(self, net_url, fill_id):
        self.driver.visit(net_url)
        sleep(0.8)
        try:
            self.driver.fill(fill_id[0], self.username)
            self.driver.fill(fill_id[1], self.password)
            self.driver.find_by_id('connect').click()
            sleep(0.5)
            # race condition: may conflict with other orders
            alert = self.driver.get_alert()
            alert.accept()
            alert.dismiss()
        except BaseException, e:
            #traceback.print_exc()
            #print('You have been connected.') 
            pass
        finally:
            print('Try to login. Check your net. Using %s' %net_url)


    def run(self):
        while True:
            self.driver_name = 'chrome'
            self.driver_path = os.path.join(self.config_dir, 'chromedriver')
            print (self.driver_path)
            self.driver = Browser(driver_name=self.driver_name, executable_path=self.driver_path)
            self.driver.driver.set_window_size(1400, 1000)
            self.connect_net(self.url1, ['username','password'])
            self.connect_net(self.url2, ['uname', 'pass'])
            self.driver.quit() 
            sleep(self.sleep_interval)

        
if __name__=='__main__':
    gb = AutoLogin('/home/hhy/Documents/autologin', 'config.json', 30) 
    gb.run()
