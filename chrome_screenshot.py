# Install chromedriver from https://sites.google.com/a/chromium.org/chromedriver/downloads

import sys
import os
import glob
import time
import urllib
import urllib.request
from bs4 import BeautifulSoup
from urllib.request import urlopen
from optparse import OptionParser

import requests
import re

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC

from auto_crop import find_images_and_process

class GrabComics:
    def __init__(self, url, base_dir=os.getcwd(), driver=None, login_url=None, 
                 series_mode=True, pg_cnt=None, redirect_url=None, headless=True,
                 first_page=True):
        
        if 'linux' in sys.platform:
            self.CHROME_PATH = r'/usr/bin/google-chrome'
            #self.CHROMEDRIVER_PATH = r'/home/user/Downloads/chromedriver'
            self.CHROMEDRIVER_PATH = r'/home/server/Downloads/chromedriver'
            self.WINDOW_SIZE = "512,600"
        else:
            self.CHROME_PATH = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
            self.CHROMEDRIVER_PATH = r'C:\Users\sra40\Downloads\chromedriver_win32\chromedriver.exe'
            self.WINDOW_SIZE = "1920,1080"
        
        # open failed log
        self.fails = open('failed.txt','w')
        
        self.chrome_options = Options()
        
        # get initial driver settings
        self._driver_settings()
        
        self.driver=driver
        self.login_url=login_url
        self.redirect_url=redirect_url
        self.url=url
        self.headless=headless
        self.base_dir = base_dir
        self.series_mode = series_mode
        self.next_issue_code = None
        self.pause = 1.0
        self.pages = {}
        self.progress = ''
        self.output = None
        
        # set page count
        if pg_cnt:
            self.pg_cnt = pg_cnt
        else:
            self.pg_cnt = 1
        
        self.comic_no = 1
        self.comic_lim = None
        self.read_comic = True
        if first_page:
            self.first_page = first_page
        else:
            self.first_page = True
        
        self.load_url()
    
    def _driver_settings(self):
        
        self.chrome_options.add_argument("--user-data-dir=chrome-data")
        self.chrome_options.add_argument("--disable-features=NetworkService")
        self.chrome_options.add_argument("--window-size=%s" % self.WINDOW_SIZE)
        self.chrome_options.binary_location = self.CHROME_PATH
        
        usage = "usage: %prog [options] <url> <output>"
        parser = OptionParser(usage=usage)
        
        (self.options, args) = parser.parse_args()
    
    def mu_login(self):
        self.driver.get(self.login_url)
        if self.driver.current_url != self.redirect_url:
            # close window driver
            self.driver.close()
            # run headless
            self.chrome_options = Options()
            # self.chrome_options.add_argument("--start-maximized")
            # get initial driver settings
            self._driver_settings()
            self.driver = webdriver.Chrome(
                executable_path=self.CHROMEDRIVER_PATH,
                options=self.chrome_options)
            # self.driver.maximize_window()
            self.driver.get(self.login_url)
            input('Press Enter')
        else:
            # close window driver
            self.driver.close()
            if self.headless:
                # run headless
                self.chrome_options = Options()
                self.chrome_options.headless = True
                self.chrome_options.add_argument("--headless")
                self.chrome_options.add_argument("--disable-gpu")
                # self.chrome_options.add_argument("--start-maximized")
                self.WINDOW_SIZE = "1920,1080"
            # get initial driver settings
            self._driver_settings()
            self.driver = webdriver.Chrome(
                executable_path=self.CHROMEDRIVER_PATH,
                options=self.chrome_options)
            self.driver.set_window_size(1920,1080)
            # self.driver.maximize_window()
            self.driver.get(self.login_url)
            time.sleep(self.pause)

    def load_url(self, pages=None):
        if pages:
            self.pages = pages
        else:
            self.pages = {}
    
        if not self.url.startswith('http'):
            raise Exception('URLs need to start with "http"')
        
        if not self.driver:
            if self.headless:
                # run headless
                self.chrome_options.headless = True
                self.chrome_options.add_argument("--headless")
                self.chrome_options.add_argument("--disable-gpu")
                #self.chrome_options.add_argument("--start-maximized")
            self.driver = webdriver.Chrome(
                executable_path=self.CHROMEDRIVER_PATH,
                options=self.chrome_options
                )
            # set window size and maximise
            # self.driver.set_window_size(4000, 3000)
        
        if self.login_url:
            self.mu_login()
        
        self.driver.get(self.url)
        time.sleep(self.pause)
        
    def _get_key_info(self):
        """
        Obtains key info from the url loaded
        """
        self.output = self.driver.title
        # remove invalid chars
        self.output = re.sub(r'[\\/*?:"<>|]',"",self.output)
        print(self.output)
        # check to see if self.output exists in self.base_dir
        if os.path.join(self.base_dir,self.output + '.cbz') in \
                glob.glob(os.path.join(self.base_dir,'*.cbz')):
            # raise exception to stop scrolling
            raise Exception
        # make output directory
        if not os.path.isdir(os.path.join(self.base_dir,self.output)):
            os.mkdir(os.path.join(self.base_dir,self.output))
        
    def _get_next_issue(self):
        """
        Looks for class 'read_now back' obtains attribute 'data-nextid'
        """
        try:
            if not self.next_issue_code:
                # find next
                next = self.driver.find_elements_by_xpath("//a[@class = 'read_now back']")[0]
                # get next comic url
                self.next_issue_code = next.get_attribute("data-nextid")
                print(self.next_issue_code)
        except:
            self.next_issue_code = None
        
    def make_screenshot(self):
        time.sleep(1.0)
        self.driver.save_screenshot(os.path.join(self.base_dir, self.output, 'page_{:04d}.jpg'.format(self.pg_cnt)))
        time.sleep(0.5)
        
    def save_pages(self, process=False):
        # check .cbz not in base directory
        print(self.progress)
        if self.output and \
                (os.path.join(self.base_dir,self.output + '.cbz') not in \
                glob.glob(os.path.join(self.base_dir,'*.cbz'))) and \
                ('100%' in self.progress):
            for id,img_url in sorted(self.pages.items()):
                if img_url:
                    # change to img_url and call make_screenshot
                    self.driver.get(img_url)
                    self.make_screenshot()
                    self.pg_cnt += 1
            # call find_images_and_process to crop and zip
            print(os.path.join(self.base_dir,self.output))
            if process:
                find_images_and_process(base_dir=self.base_dir, output=self.output)
        else:
            if '100%' not in self.progress:
                self.fails.write('FAILED TO SAVE: {}'.format(self.output))
            else:
                print('Comic already exists: {}'.format(self.output))
        
    @staticmethod
    def _get_all_hrefs(driver, parent_name):
        # define empty dictionary
        hrefs = {}
        # find parent
        parents = driver.find_elements_by_tag_name(parent_name)
        for child_elem in parents:
            id = child_elem.get_attribute("id")
            href = child_elem.get_attribute("href")
            hrefs[id] = href
        return hrefs
        
    def _delay_by_id(self, driver, pause, el_id, else_click_el=None):
        try:
            myElem = WebDriverWait(driver, pause).until(EC.presence_of_element_located((By.ID, el_id)))
            #print("Page is ready!")
        except TimeoutException:
            print("Loading took too much time!")
            # check if else_click_el
            if else_click_el:
                else_click_el.click()
                self._delay_by_id(driver, pause, el_id)
    
    def click_next(self):
        # time.sleep(self.pause)
        # set pause times
        #if self.first_page:
            # self.pause = 1.0
            #self.pause = 3.0
            #self.pause = 0.5
        #else:
            # self.pause = 0.5
            #self.pause = 1.0
            #self.pause = 0.5
        self.pause = 0.5
        
        # footer
        footer = self.driver.find_element_by_id("footer")
            
        for child in footer.find_elements_by_tag_name("footer"):
            # ensure footer is visible
            self.driver.execute_script("arguments[0].setAttribute('class','')", child)
        # header
        header = self.driver.find_element_by_id("header")
        for child in footer.find_elements_by_tag_name("header"):
            # ensure footer is visible
            self.driver.execute_script("arguments[0].setAttribute('class','')", child)
        # generic sleep
        time.sleep(self.pause)
            
        # wait for element with ID 'page'
        self._delay_by_id(self.driver, self.pause*20.0, 'page')
        # toggle whole page view
        page = self.driver.find_element_by_id("page")
        # change class to whole-page view setting
        self.driver.execute_script("arguments[0].setAttribute('class','removeGif stripes')", page)
        # wait for element with ID 'footer'
        self._delay_by_id(self.driver, self.pause*20.0, 'footer', else_click_el=page)
        time.sleep(self.pause)
        
        # click full page view
        #if self.first_page:
            # wait for element with ID 'footer'
            #self._delay_by_id(self.driver, self.pause*20.0, 'footer', else_click_el=page)
            #time.sleep(self.pause)
            #fullpage = self.driver.find_elements_by_xpath("//section[@id = 'footer']//li[@class = 'icon btn-panel']")[0]
            #fullpage.click()
            #time.sleep(self.pause)
        
        # get next issue
        self._get_next_issue()
        
        # get output name
        self._get_key_info()
        
        # print progress
        progress_string=[]
        #header = self.driver.find_element_by_id("header")
        #progress = header.find_elements_by_class_name("progress-bar")
        progress = header.find_elements_by_xpath("//div[@class = 'progress-bar']//span[@class = 'progress']")
        for ob in progress:
            progress_string.append(ob.get_attribute("style"))
        print(progress_string)
        self.progress = progress_string[0]
        
        # extract hrefs
        time.sleep(self.pause)
        tmp_dict = self._get_all_hrefs(page, "image")
        
        # update self.pages with tmp_dict
        self.pages.update(tmp_dict)
        
        # next page
        # wait for element with ID 'page'
        self._delay_by_id(self.driver, self.pause*20.0, 'right_arrow')
        element = self.driver.find_element_by_id("right_arrow")
        element.click()
        time.sleep(.1)
        
        self.first_page = False

    @staticmethod
    def split_url(url, new_final_el):
        #split
        init_url = url.split('//')
        secondary_url = init_url[-1].split('/')
        #replace
        secondary_url[-1] = new_final_el
        #join
        init_url[-1] = '/'.join(secondary_url)
        url = '//'.join(init_url)
        return url

    def read_all(self):
        """
        Method to click through comic until unable to
        """
        # read comic
        while self.read_comic:
            print("Comic number: {}".format(self.comic_no))
            try:
                self.click_next()
            except Exception as e:
                # check if in series_mode if so get url of next comic 
                # pass to new instance of GrabComics with current page number
                if self.series_mode:
                    next_url_code = None
                    try:
                        # time.sleep(self.pause*5.0)
                        if self.next_issue_code:
                            next_url = self.split_url(self.url, self.next_issue_code)
                            print(next_url)
                            # save current 
                            self.save_pages(process=True)
                            # close current driver
                            self.clean_close()
                            # call another instance of GrabComics with next_url
                            next_comic = GrabComics(login_url=self.login_url,
                                                    driver=None,#self.driver,
                                                    #first_page=False,
                                                    url=next_url,
                                                    # output=save_name,
                                                    redirect_url="https://www.marvel.com/"
                                                    )
                            #next_comic.first_page = False
                            next_comic.read_all()
                        else:
                            # save current 
                            self.save_pages(process=True)
                            # close current driver
                            self.clean_close()
                    except:
                        self.save_pages(process=True)
                        self.driver.close()
                        print('FAILED TO RUN IN SERIES MODE')
                else:
                    self.save_pages(process=True)
                    # close current driver
                    self.clean_close()
                self.read_comic = False
        #return self.driver

    def clean_close(self):
        try:
            self.driver.close()
        except:
            pass

if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 2:
        parser.error("please specify a URL and an output")
    
    if len(args) >= 3:
        login_url = args[2]
    else:
        login_url="https://www.marvel.com/signin"

    comic = GrabComics(login_url=login_url,
                        url=args[0], 
                        output=' '.join(args[1:])
                        )
    
    # comic.make_screenshot()
    comic.read_all()
    
