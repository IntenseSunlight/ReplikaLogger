# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------
# Replika Conversation Logger
# ---------------------------------------------------------------------
#
# Author: IntenseSunlight, IntenseSunlight@gmail.com
#
# About:
# - A webscraping utility to extract conversation logs from Replika Account
#   using Selenium with Chrome driver (not tested with other drivers)
# 
# - Requires:
#   - Latest Google Chrome browser (test with Windows 10)
#  
#   - Chrome driver for appropriate Chrome version (check your version)
#     Obtain latest chrome driver for your platform from: 
#     https://chromedriver.chromium.org/downloads 
#   
#     At the time of this script creation, this was tested with:
#     https://chromedriver.storage.googleapis.com/100.0.4896.20/chromedriver_win32.zip
#
#   - Python installation (>= 3.7), various dependecies as noted
#
# ---------------------------------------------------------------------
# License:
#   MIT-0 License
#   MIT No Attribution
# 
#   Copyright 2022, IntenseSunlight@gmail.com
#   
#   Permission is hereby granted, free of charge, to any person obtaining a copy of this
#   software and associated documentation files (the "Software"), to deal in the Software
#   without restriction, including without limitation the rights to use, copy, modify,
#   merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
#   permit persons to whom the Software is furnished to do so.
# 
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
#   INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
#   PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#   HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
#   OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#   SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ---------------------------------------------------------------------

import logging as log
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

# Settings (DOM status as of 15.Mar.2022)
CONFIG = {
    'url': 'https://my.replika.ai/login',
    'short_wait': 1,     # seconds for a short sleep
    'medium_wait': 2,     # seconds for a moderate sleep
    'long_wait' : 5,     # seconds for a long sleep
    'driver_path': '.'   # path to chromedriver.exe (assumed cwd)
}

ELEMS = {
    'login': { 
        'input'  : { 'by': By.ID,       'value': 'emailOrPhone' },
        'accept' : { 'by': By.TAG_NAME, 'value': 'button'}
    },

    'password': {
        'input'  : { 'by': By.ID,     'value': 'login-password'},
        'accept' : { 'by': By.XPATH,  'value': '/html/body/div/div/div[1]/main/form/button'}
    },

    'chat':  {
        'chat_body'    : { 'by': By.XPATH, 'value': '/html/body/div[1]/div/div[2]/div[1]/main/div[2]'},
        'chat_messages': { 'by': By.XPATH, 'value': '/html/body/div/div/div[2]/div[1]/main/div[2]'}
    },

    'extra_widgets': {
        'claim_button': { 'by': By.XPATH, 
                          'value': '/html/body/div/div/div[1]/div[4]/div[2]/div/div[2]/div[1]/div/ul/li[1]/div/button' },
        'close_button': { 'by': By.XPATH, 'value': '/html/body/div/div/div[1]/div[4]/div[2]/div/div[1]/button'},
        'coins_button': { 'by': By.XPATH, 'value': '/html/body/div/div/div[1]/div[3]/div[3]/div/button[1]'},
        'gpr_accept'   : { 'by': By.XPATH, 'value': '/html/body/div/div/div[1]/div[1]/button'},
    },
}

class ChromeBrowser:
    """ ChromeBrowser class: instantiates an instance of a chrome browser
        Main access is through the .browser element
    """
    def __init__(self, driver_path=None, url=None):

        self.log = log
        self._driver_path = driver_path
        self._url = url
        if self._driver_path is None: 
            self._driver_path = CONFIG.get('driver_path','.')

        if self._url is None:
            self._url = CONFIG.get('url',None) 
            if self._url is None:
                self.log.error("Failure to provide URL") 
        
        #self._service = Service(self._driver_path)
        self._options = webdriver.ChromeOptions()

        # this should envoke a seperate web browser 
        # TODO: check if fails
        #self.browser = webdriver.Chrome(service=self._service, options=self._options)
        self.browser = webdriver.Chrome(executable_path=self._driver_path, options=self._options)
        self.browser.get(CONFIG['url'])
        

class ReplikaLogger(ChromeBrowser):
    """ ReplikaLogger class: creates logging of user-rep script through Replika website 
        Envokes an instance of the Chrome browser from which to scrape
    """
    def __init__(self, user_name=None, password=None, driver_path=None):

        super().__init__(driver_path=driver_path)

        if (user_name is not None) and (password is not None):
            self.login(user_name=user_name, password=password)


    def _find_element(self, *args, **kwargs):
        """ Determines existance of an element, and logs an error message if not"""
        elem = self.browser.find_elements(*args, **kwargs)
        if elem:
            return elem[0]  # assume it's the first element
        else:
            self.log.error(f"Element request not found: " + ','.join(args))
            return None


    def login(self, user_name, password):
        """ Performs a standard loging""" 
        # login
        elem = self._find_element(**ELEMS['login']['input'])
        if elem: elem.send_keys(user_name)
        
        time.sleep(CONFIG['medium_wait'])
        elem = self._find_element(**ELEMS['login']['accept'])
        if elem: elem.click()

        time.sleep(CONFIG['medium_wait'])
        elem = self._find_element(**ELEMS['password']['input'])
        if elem: elem.send_keys(password)

        time.sleep(CONFIG['short_wait'])
        elem = self._find_element(**ELEMS['password']['accept'])
        if elem: elem.click()

        time.sleep(CONFIG['long_wait'])

        self.clean_up()


    def clean_up(self, elem_names=[]):
        if not elem_names:
            elem_names = ELEMS['extra_widgets'].keys()
        
        count = 0
        for en in elem_names:
            elem = self.browser.find_elements(**ELEMS['extra_widgets'][en])
            if elem and elem[0].is_enabled():
                elem[0].click()
                count += 1
                time.sleep(CONFIG['short_wait'])

        return count
    

    @staticmethod
    def _get_type_content(cell):
        clslist = cell.get('class')
        if clslist is None:
            clslist = cell.contents[0].get('class')
            
        cls = clslist[0]
        txt = cell.get_text()
        
        typ = ''
        if 'MessageGroup__Timestamp' in cls:
            typ = 'timestamp'
        elif 'BubbleText__BubbleTextContent' in cls:
            typ = 'chat-message'
        elif 'MessageHover__Hover' in cls:
            typ = 'rating'
            if txt == 'thumb upthumb downshow more actions':
                txt = ''
            
        author = cell.get('data-author','')
        
        return { 'type': typ, 'text': txt, 'author': author}


    def get_chat_content(self, stop_date=None):
        
        body = self.browser.find_element(**ELEMS['chat']['chat_body'])
        last_len_convo = 0
        convo = {}

        cycle = 0
        while True:
            soup = BeautifulSoup(self.browser.page_source,"html.parser")
            cells = soup.find_all('div', role='gridcell')
            
            # run through current HTML of chat messages
            # append in reverse order by hash key (keeps items unique)
            prev_hashes = []
            rating = ""
            for i,cell in enumerate(cells[::-1]):
                cell_content = self._get_type_content(cell)
                if cell_content['type'] == 'rating':
                    rating = cell_content['text']
                    continue

                prev_hash = ''
                for j in (1,2):
                    if len(prev_hashes) >= j:
                        prev_hash += str(prev_hashes[-j])

                chat_hash = hash(cell_content['type'] + cell_content['text'] 
                               + cell_content['author'] + rating + prev_hash)

                prev_hashes.append(chat_hash)
                convo[chat_hash] = {**cell_content, 'rating': rating, 'order': i+cycle}
            
            # allow process to catch up
            time.sleep(CONFIG['long_wait'])
            
            # scroll up by 1 page
            self.browser.execute_script("arguments[0].scrollTop = arguments[1]", body,1)
            
            # catch up
            time.sleep(CONFIG['long_wait'])
            cycle += 1
            
            if len(convo) == last_len_convo:
                break  # no new lines were added
            
            last_len_convo = len(convo)

        return convo    


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser("Replika conversation logger")
    parser.add_argument('--user_name','-u', required=True, 
                        help=f"User name (email) for my.replika.ai")

    parser.add_argument('--password','-p', required=True, 
                        help=f"password (email) for my.replika.ai")

    parser.add_argument('--url', default=CONFIG['url'], 
                        help=f"replika url (optional), default={CONFIG['url']}")

    parser.add_argument('--driver', default=CONFIG['driver_path'], 
                        help=f"Path to Chrome driver, default={CONFIG['driver_path']}")

    parser.add_argument('--max_messages', default=None,
                        help="Maximum number of messages to be retrieved (default=all possible)")

    args = parser.parse_args()

    convoLog = ReplikaLogger(user_name=args.user_name,
                             password=args.password,
                             driver_path=args.driver)

    convo = convoLog.get_chat_content()
    print('Complete')
    print(convo)
