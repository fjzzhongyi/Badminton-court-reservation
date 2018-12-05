# -*- coding:utf-8 -*-
# author: fjzzhongyi@163.com
from splinter.browser import Browser
import os, time, sys
from time import sleep
import json, re, traceback
import datetime

class GymBook:

    login_url = 'http://50.tsinghua.edu.cn/'
    book_url = 'http://50.tsinghua.edu.cn/gymbook/gymBookAction.do?ms=viewGymBook&gymnasium_id=3998000&item_id=4045681&time_date=%s&userType=&viewType=m'
    net_url = 'http://net.tsinghua.edu.cn/wired'
    username = '2017311691'
    username2 = 'hhy17'
    password = 'Hhy123456'
    idlist = {} # format: {'19:00-20:00':{1: 4000102}}

    def __init__(self, resourcepath, id_priority, time_priority, desire_hours, date):
        assert len(id_priority)==12
        assert len(time_priority)>=desire_hours
        self.driver_name = 'chrome'
        self.driver_path = os.getcwd() + '/chromedriver'
        self.id_priority = id_priority
        self.time_priority = time_priority
        self.desire_hours = desire_hours # 1/2 hours
        self.date = date
        self.sourcepath = resourcepath
        
        self.driver = Browser(driver_name=self.driver_name, executable_path=self.driver_path)
        self.driver.driver.set_window_size(1400, 1000)
    
    def __read_id(self, filepath):
        f=open(filepath,'r')
        s=f.readlines()
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
        for start in range(len(time_priority)-self.desire_hours+1):
            target_hours = time_priority[start: start+self.desire_hours]
            for field in self.id_priority:
                target = [] 
                for hour in target_hours:
                    target.append(self.idlist[hour][field])   
                targets.append(target)
        assert len(targets) == (len(self.time_priority)-self.desire_hours+1)*len(self.id_priority) 
        return targets

    def connect_net(self):
        self.driver.visit(self.net_url)
        try:
            self.driver.fill('uname', self.username2)
            self.driver.fill('pass', self.password)
            self.driver.find_by_id('connect').click()
        except BaseException, e:
            #traceback.print_exc()
            print('has loged in') 
    def login(self):
        self.driver.visit(self.login_url)
        self.driver.find_by_text(u'预约场地').click()
        self.driver.fill('un', self.username)
        self.driver.fill('pw', self.password)
        self.driver.find_by_value(u"登录").click()
    
    def book(self):  
        self.login()
        self.driver.visit(self.book_url % self.date)
        booked = False 
        targets = self.fetch_targets()
        begin_time = datetime.datetime.now()
        while booked is False:
            for target in targets:
                filtered = False
                with self.driver.get_iframe('overlayView') as iframe:
                    for resource_id in target:
                        box = iframe.find_by_id('resourceTd_' + resource_id).first
                        lock = box._element.get_attribute('lock')
                        if lock is None:
                            box.click()
                            continue
                        else:
                            if bool(lock):
                                filtered = True 
                                break
                if filtered:
                    continue
                try:
                    #money = re.search(r'\d+', self.driver.find_by_id('yyPullRight').value).group(0)
                    #if not(int(money) == 20 * self.desire_hours):
                    #    raise BaseException 
                    
                    #try:
                    #    alert = self.driver.get_alert()
                    #    alert.accept()
                    #    alert.dismiss()
                    #except BaseException, e:
                    #    pass

                    self.driver.find_link_by_href(u"#popupLogin").click()
                    self.driver.find_by_id('popupLogin-screen').click()
                    self.driver.find_by_id('payWayConfirm').first.click()

                    try:
                        # race condition: may conflict with other orders
                        alert = self.driver.get_alert()
                        alert.accept()
                        alert.dismiss()
                    except BaseException, e:
                        #TODO
                        pass 

                    end_time = datetime.datetime.now()
                    duration = end_time - begin_time
                    print('book for hour: success, cost: %d days %d seconds and %d us'%(duration.days, duration.seconds, duration.microseconds))
                    booked = True
                    self.driver.fill('xm',u'黄宏毅')
                    self.driver.fill('dept',u'交叉信息研究院')
                    self.driver.find_by_id('payLater').click()
                    break
                except BaseException, e:
                    print('try with resource_id: %s failed'%(str(target)))
                    traceback.print_exc()
                    #self.driver.reload()
                    self.driver.visit(self.book_url % self.date)
                    #sleep(0.001)
                    continue
    def run(self):
        self.book()
        
if __name__=='__main__':
    id_priority = [10,9,8,7,6,5,4,3,2,1,11,12]
    #time_priority = ['21:00-22:00', '20:00-21:00']
    time_priority = ['12:00-13:00','11:30-12:00']
    desire_hours = 2 
    date = "2018-12-06"
    gb = GymBook('id_resource', id_priority, time_priority, desire_hours, date)
    gb.connect_net()
    gb.run()
