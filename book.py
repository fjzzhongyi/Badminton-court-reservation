#!/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author   : Hongyi Huang
# @Github   : fjzzhongyi
from splinter.browser import Browser
import selenium
import os, time, sys
from time import sleep
import json, re, traceback
import datetime


# import requests

def judge_connect(func):
    def wrapper(*args, **kwargs):
        global require_net_login
        # try:
        #     html = requests.get(r"https://www.baidu.com", timeout=2)
        # except:
        #     require_net_login = False
        # require_net_login = True
        if require_net_login:
            ret = func(*args, **kwargs)
            return ret
        else:
            pass

    return wrapper


class GymBook:
    login_url = 'http://50.tsinghua.edu.cn/'
    book_url = 'http://50.tsinghua.edu.cn/gymbook/gymBookAction.do?ms=viewGymBook&gymnasium_id=3998000&item_id=4045681&time_date=%s&userType=&viewType=m'
    net_url = 'http://net.tsinghua.edu.cn/wired'
    username = '2017311691'
    username2 = 'hhy17'
    password = 'Hhy123456'
    idlist = {}  # format: {'19:00-20:00':{1: 4000102}}
    fresh_interval = 0.1
    sleep_interval = 5
    threshold = 15
    network_interval = 60

    def __init__(self, resourcepath, id_priority, time_priority, desire_hours, date):
        assert len(id_priority) == 12
        assert len(time_priority) >= desire_hours
        self.driver_name = 'chrome'
        self.driver_path = os.getcwd() + '/chromedriver'
        self.id_priority = id_priority
        self.time_priority = time_priority
        self.desire_hours = desire_hours  # 1/2 hours
        self.date = date
        self.sourcepath = resourcepath
        # if set headless=True, meaning no GUI
        self.driver = Browser(driver_name=self.driver_name, executable_path=self.driver_path, headless=False)
        self.driver.driver.set_window_size(1400, 1000)
        self.start_time = datetime.datetime.strptime(date + ' 08:00:00', '%Y-%m-%d %H:%M:%S') - datetime.timedelta(
            days=3)
        # self.start_time = datetime.datetime.now() + datetime.timedelta(seconds=30)

    def __is_window_on(func):
        def wrapper(*args, **kwargs):
            assert len(args) > 0
            try:
                args[0].driver.visit(r"about:blank")
            except selenium.common.exceptions.NoSuchWindowException as e:
                args[0].driver = Browser(driver_name=args[0].driver_name, executable_path=args[0].driver_path, headless=False)
                args[0].driver.driver.set_window_size(1400, 1000)
            func(*args, **kwargs)
        return wrapper

    def __read_id(self, filepath):
        f = open(filepath, 'r')
        s = f.readlines()
        for entry in s:
            if re.match(r'\s*resourceArray.push\(.*\).*', entry):
                resource_id = re.search(r'\d{7}', entry).group(0)
                duration = re.search(r'[\d:-]{9,11}', entry).group(0)
                field = re.search(r'羽(?P<n1>\d*)', entry).groups(0)[0]
                if duration in self.idlist:
                    self.idlist[duration][int(field)] = resource_id
                else:
                    self.idlist[duration] = {int(field): resource_id}

    def fetch_targets(self):
        self.__read_id(self.sourcepath)
        targets = []
        for start in range(len(time_priority) - self.desire_hours + 1):
            target_hours = time_priority[start: start + self.desire_hours]
            for field in self.id_priority:
                target = []
                for hour in target_hours:
                    target.append(self.idlist[hour][field])
                targets.append(target)
        assert len(targets) == (len(self.time_priority) - self.desire_hours + 1) * len(self.id_priority)
        return targets

    @judge_connect
    @__is_window_on
    def connect_net(self):
        self.driver.visit(self.net_url)
        try:
            self.driver.fill('uname', self.username2)
            self.driver.fill('pass', self.password)
            self.driver.find_by_id('connect').click()
            sleep(1)
            # race condition: may conflict with other orders
            alert = self.driver.get_alert()
            alert.accept()
            alert.dismiss()
        except BaseException as e:
            # traceback.print_exc()
            print('has loged in')

    @__is_window_on
    def login(self):
        self.driver.visit(self.login_url)
        self.driver.find_by_text(u'预约场地').click()
        self.driver.fill('un', self.username)
        self.driver.fill('pw', self.password)
        self.driver.find_by_value(u"登录").click()

    def __probe(self):
        # probe (6:30-8:00, 01) 5500347 and (13:00-14:00, 07) 4045872
        # if grey: False, haven't started
        # else: ready, True
        if self.driver.is_element_not_present_by_name('overlayView'):
            return False
        with self.driver.get_iframe('overlayView') as iframe:
            for resource_id in ['5500347', '4045872']:
                box = iframe.find_by_id('resourceTd_' + resource_id).first
                style = box._element.get_attribute('style')
                if style is not None and style == "background: gray;":
                    return False
            return True

    @__is_window_on
    def book(self):
        targets = self.fetch_targets()
        booked = False

        self.driver.visit(self.book_url % self.date)
        # loop untils gray to yellow
        while not self.__probe():
            print('approaching but not available now, continue to sleep for fresh_interval %ds' % self.fresh_interval)
            sleep(self.fresh_interval)
            self.driver.reload()
        # start booking now 
        print('go into booking procedure')
        begin_time = datetime.datetime.now()
        while booked is False:
            if booked:
                return True
            for target in targets:
                filtered = False
                with self.driver.get_iframe('overlayView') as iframe:
                    for resource_id in target:
                        box = iframe.find_by_id('resourceTd_' + resource_id).first
                        lock = box._element.get_attribute('lock')
                        if lock is None:
                            continue
                        else:
                            if bool(lock):
                                filtered = True
                                break
                if filtered:
                    print('failed to book %s, for reason: occupied.' % str(target))
                    continue
                else:
                    with self.driver.get_iframe('overlayView') as iframe:
                        for resource_id in target:
                            box = iframe.find_by_id('resourceTd_' + resource_id).first
                            box.click()
                    print('%s is available, try to lock.' % str(target))
                try:
                    # money = re.search(r'\d+', self.driver.find_by_id('yyPullRight').value).group(0)
                    # if not(int(money) == 20 * self.desire_hours):
                    #    raise BaseException 

                    # try:
                    #    alert = self.driver.get_alert()
                    #    alert.accept()
                    #    alert.dismiss()
                    # except BaseException, e:
                    #    pass

                    self.driver.find_link_by_href(u"#popupLogin").click()
                    try:
                        self.driver.find_by_id('phone_jq').click()
                    except BaseException as e:
                        pass
                    try:
                        self.driver.find_by_id('popupLogin-screen').click()
                    except BaseException as e:
                        pass
                    self.driver.find_by_id('payWayConfirm').first.click()

                    try:
                        # race condition: may conflict with other orders
                        alert = self.driver.get_alert()
                        alert.accept()
                        alert.dismiss()
                        # may be something bad: race condition occurs; revisit
                        self.driver.visit(self.book_url % self.date)
                    except BaseException as e:
                        # no alert: it goes on
                        traceback.print_exc()
                        pass

                    end_time = datetime.datetime.now()
                    duration = end_time - begin_time
                    print('book for designated hours: success, time consumed: %d days %d seconds and %d us' % (
                        duration.days, duration.seconds, duration.microseconds))
                    booked = True
                    self.driver.fill('xm', u'黄宏毅')
                    self.driver.fill('dept', u'交叉信息研究院')
                    self.driver.find_by_id('payLater').click()
                    break
                except BaseException as e:
                    print('try with resource_id: %s failed' % (str(target)))
                    traceback.print_exc()
                    # self.driver.reload()
                    self.driver.visit(self.book_url % self.date)
                    continue

    def run(self):
        now = datetime.datetime.now()
        left = (self.start_time - now).total_seconds()
        while left > self.threshold:
            print('long time from start, time now is %s, %f seconds remains, to sleep for %ds' % (
                now.isoformat(), left, self.sleep_interval))
            sleep(self.sleep_interval)
            now = datetime.datetime.now()
            left = (self.start_time - now).total_seconds()

        # ready for booking: ensure network ok
        self.connect_net()
        self.login()
        # start booking
        if self.book():
            print('HAPPY!^-^')


if __name__ == '__main__':
    global require_net_login
    require_net_login = False
    id_priority = [9, 8, 7, 6, 5, 4, 3, 2, 1, 11, 12, 10]
    # time_priority = ['21:00-22:00', '20:00-21:00']
    time_priority = ['19:00-20:00', '20:00-21:00']
    desire_hours = 2
    date = "2019-03-10"
    gb = GymBook('id_resource', id_priority, time_priority, desire_hours, date)
    # gb.connect_net()
    gb.run()
