#!/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author   : Hongyi Huang
# @Github   : fjzzhongyi

#
# from splinter.browser import Browser
# from time import sleep
# import os
# import selenium

# driver_name = 'chrome'å
# driver_path = os.getcwd() + '/chromedriver'
# # if set headless=True, meaning no GUI
# driver = Browser(driver_name=driver_name, executable_path=driver_path, headless=False)
# driver.driver.set_window_size(1400, 1000)
# sleep(10)
# try:
#     driver.visit(r'about:blank')
# except selenium.common.exceptions.NoSuchWindowException as e:
#     print("1)")
#     pass

def foo(func):
    def wrapper(*args, **kwargs):
        print(args, kwargs)
        func(*args, **kwargs)
        print(args[0].A)
    return wrapper


class T:
    def __init__(self):
        self.A = 1
    @foo
    def test(self):
        print(0)
        return


T().test()

