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
import requests


# For first time, you should assign specific path of chromedriver and configuration file 

config_path = "/home/hhy/Desktop/booking/config.json"
chrome_path = '/home/hhy/Desktop/booking/chromedriver'

log_file = "./result.log"
def log(info):
    print(info)
    if not os.path.exists(log_file):
        with open(log_file, "w"):
            pass
    with open(log_file, "a+") as fw:
        fw.write(str(datetime.datetime.now()) + ":  " + info + "\n")


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
    login_url = "http://50.tsinghua.edu.cn/login_m.jsp"
    book_url = "http://50.tsinghua.edu.cn/gymbook/gymBookAction.do?ms=viewGymBook&gymnasium_id=3998000&item_id=4045681&time_date=%s&userType=&viewType=m"
    
    idlist = {} # format: {'19:00-20:00':{1: 4000102}}
    fresh_interval = 0.03
    sleep_interval = 5
    threshold = 15
    network_interval = 60
    book_start_time = "08:00:00"

    def __init__(self, resourcepath, configs):
        # assert len(time_priority) >= desire_hours
        self.driver_name = 'chrome'
        self.driver_path = chrome_path 
        
        self.id_priority = configs["id_priority"]
        assert len(self.id_priority) == 12
        self.time_priority = configs["time_priority"]
        self.date = configs["date"]
        self.net_url = configs["net_url"]
        self.username = configs["50_username"]
        self.username2 = configs["net_username"]
        self.password = configs["password"]
        self.phone_jq = configs["phone"]
        self.name = configs["name"]
        self.dept = configs["dept"]
        
        self.sourcepath = resourcepath
        # if set headless=True, meaning no GUI
        
        # self.driver = Browser(driver_name=self.driver_name, executable_path=self.driver_path, headless=False)
        # self.driver.driver.set_window_size(1400, 1000)
        self.driver = None
        
        self.start_time = datetime.datetime.strptime(self.date + ' ' + self.book_start_time, '%Y-%m-%d %H:%M:%S') - datetime.timedelta(
            days=3)
        if self.start_time <= datetime.datetime.now():
            log('You have missed the first-time chance! (Start time has gone!)')
            # sys.exit(0)
        # self.start_time = datetime.datetime.now() + datetime.timedelta(seconds=30)
        self.durations = set() 

    def __is_window_on(func):
        def wrapper(*args, **kwargs):
            assert len(args) > 0
            try:
                args[0].driver.visit(r"about:blank")
            except (AttributeError, selenium.common.exceptions.NoSuchWindowException, selenium.common.exceptions.WebDriverException) as e:
                args[0].driver = Browser(driver_name=args[0].driver_name, executable_path=args[0].driver_path, headless=True)
                args[0].driver.driver.set_window_size(1400, 1000)
            func(*args, **kwargs)
        return wrapper

    #deprecated
    #def __read_id_offline(self, filepath):
    #    f = open(filepath, 'r', encoding="utf-8")
    #    s = f.readlines()
    #    for entry in s:
    #        if re.match(r'\s*resourceArray.push\(.*\).*', entry):
    #            resource_id = re.search(r'\d{7}', entry).group(0)
    #            duration = re.search(r'[\d:-]{9,11}', entry).group(0)
    #            field = re.search(r'羽(?P<n1>\d*)', entry).groups(0)[0]
    #            if duration in self.idlist:
    #                self.idlist[duration][int(field)] = resource_id
    #            else:
    #                self.idlist[duration] = {int(field): resource_id}
    #            self.durations.add(duration)
    #    print(self.durations)

    def __read_id_online(self, filepath):
        url = "http://50.tsinghua.edu.cn/gymsite/cacheAction.do?ms=viewBook&gymnasium_id=3998000&item_id=4045681&time_date=%s&userType=1" %(self.date)
        res = requests.get(url)
        for entry in res.text.split("\n"):
            if re.match(r'\s*resourceArray.push\(.*\).*', entry):
                resource_id = re.search(r'\d{7}', entry).group(0)
                duration = re.search(r'[\d:-]{9,11}', entry).group(0)
                field = re.search(r'羽(?P<n1>\d*)', entry).groups(0)[0]
                if duration in self.idlist:
                    self.idlist[duration][int(field)] = resource_id
                else:
                    self.idlist[duration] = {int(field): resource_id}
                self.durations.add(duration)
    
    # fetch_targets calculates all prioritized field_id combinations
    def fetch_targets(self):
        def generate_targets(source_list, duration):
            targets = []

            def generate_iterations(depth, prefix=[]):
                for item in source_list:
                    if depth == 1:
                        targets.append(prefix + [item])
                    else:
                        generate_iterations(depth - 1, prefix + [item])

            def compare(x):
                weight = 0
                for item in x:
                    weight += source_list.index(item)
                # return weight + np.std(x) * 1e-10 # prioritize groups that have similar group members, but it's too slow
                return weight
            generate_iterations(duration)
            targets.sort(key=compare)
            return targets

        def transform(source_list, time_list, id_list):
            target_list = []
            for combination in source_list:
                target = [id_list[time_list[index]][combination[index]] for index in range(len(combination))]
                target_list.append(target)
            return target_list
        
        def check_time_exist():
            new_time_priority = []
            for time_set in self.time_priority:
                to_remove = False
                for time_iter in time_set:
                    if time_iter not in self.durations:
                        log(str(time_set) + " doesn't comply with real time slot, so this slot will be omitted.")
                        to_remove = True
                        break
                if not to_remove:
                    new_time_priority.append(time_set)
            self.time_priority = new_time_priority


            

        self.__read_id_online(self.sourcepath)
        targets = []
        # remove invaid time period 
        check_time_exist()
        for time_set in self.time_priority:
            field_targets = generate_targets(self.id_priority, len(time_set))
            # print("Target fields: ", field_targets)
            id_targets = transform(field_targets, time_set, self.idlist)
            targets += id_targets
        # print(len(targets))
        return targets
        # targets = []
        # for start in range(len(time_priority) - self.desire_hours + 1):
        #     target_hours = time_priority[start: start + self.desire_hours]
        #     for field in self.id_priority:
        #         target = []
        #         for hour in target_hours:
        #             target.append(self.idlist[hour][field])
        #         targets.append(target)
        # assert len(targets) == (len(self.time_priority) - self.desire_hours + 1) * len(self.id_priority)
        # return targets


    @judge_connect
    @__is_window_on
    def connect_net(self):
        self.driver.visit(self.net_url)
        try:
            self.driver.fill('username', self.username2)
            self.driver.fill('password', self.password)
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
        #self.driver.find_by_text(u'预约场地').click()
        self.driver.fill('un', self.username)
        self.driver.fill('pw', self.password)
        self.driver.find_by_value(u"登录").click()

    def __probe(self):
        # probe one field: priority time duration + field id
        # if all styles are in grey: False, haven't started
        # else if any one is not in grey: ready, True
        if self.driver.is_element_not_present_by_name('overlayView'):
            return False
        probes = [(self.time_priority[0][0], self.id_priority[0])]
        with self.driver.get_iframe('overlayView') as iframe:
            for (duration, field) in probes:
                box = iframe.find_by_id("resourceTd_%s" % self.idlist[duration][field]).first
                style = box._element.get_attribute('style')
                if style is not None and style != "background: gray;":
                    return True 
            return False 

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
        log('Go into booking procedure')
        begin_time = datetime.datetime.now()
        while booked is False:
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
                    log('failed to book %s, for reason: occupied.' % str(target))
                    continue
                else:
                    with self.driver.get_iframe('overlayView') as iframe:
                        box_list = []
                        for resource_id in target:
                            box = iframe.find_by_id('resourceTd_' + resource_id).first
                            box_list.append(box)
                        for box in box_list:
                            box.click()
                    log('%s is available, try to lock.' % str(target))
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
                    # self.driver.find_by_name("selectPayWay").first.find_by_id("selectPayWay0").first.check()
                    # self.driver.click_by_id
                    # self.driver.check("        现场支付")
                    # self.driver.check("selectPayWay")
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
                    log('book for designated hours in date %s : success, time consumed: %d days %d seconds and %d us' % (
                        self.date, duration.days, duration.seconds, duration.microseconds))
                    booked = True
                    self.driver.fill('xm', self.name)
                    self.driver.fill('dept', self.dept)
                    # os.system("pause")
                    self.driver.find_by_id('payLater').click()
                    break
                except BaseException as e:
                    log('try with resource_id: %s failed' % (str(target)))
                    traceback.print_exc()
                    # self.driver.reload()
                    if booked is not True:
                        self.driver.visit(self.book_url % self.date)
                        continue
            if booked:
                return True
            else:
                log("Fail to book: no free fields satisfying requirements!")
                return False

    def run(self):
        now = datetime.datetime.now()

        # check if time has passed

        book_date = datetime.datetime.strptime(self.date + ' ' + self.book_start_time, '%Y-%m-%d %H:%M:%S')
        if book_date < now:
            log("Date to book has passed!!! -- so stop!")
            return 

        left = (self.start_time - now).total_seconds()
        while left > self.threshold:
            print('long time from start, time now is %s, %f seconds remains, to sleep for %ds' % (
                now.isoformat(), left, self.sleep_interval))
            sleep(self.sleep_interval)
            now = datetime.datetime.now()
            left = (self.start_time - now).total_seconds()

        # ready for booking: ensure network ok
        # self.connect_net()
        self.login()
        # start booking
        if self.book():
            log('Success. HAPPY!^-^')

if __name__ == '__main__':
    log("\nStart a new task!")

    configs = {}
    with open(config_path, 'r', encoding="utf-8") as f:
        configs = json.load(f)
    
    global require_net_login
    require_net_login = configs["require_net_login"]

    gb = GymBook('id_resource', configs)
    # gb.connect_net()
    gb.run()
