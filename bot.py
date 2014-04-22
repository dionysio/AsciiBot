# -*- coding: utf-8 -*-

'''
The MIT License (MIT)

Copyright (c) 2014 Dionyz Lazar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

from config import *

import praw #wrapper for connecting to reddit
from time import sleep  #for sleeping
from pyimgur import Imgur #wrapper for uploading to imgur
from ghost import Ghost
from json import dump,load,JSONEncoder
from os import path
from sys import exc_info
from datetime import now

class Uploader():
    def __init__(self):
        self.uploader = Imgur(client_id=imgur_key, client_secret=imgur_secret)


    def upload_screenshot(self, path_to_picture,text):
        '''Uploads screenshot from url to imgur.
        
        :param url: url of uploaded picture
        :param text: text to describe the image
        '''
    
        uploaded_image = self.uploader.upload_image(path_to_picture, title=text)
        return uploaded_image.link.encode('ascii','ignore')


class Browser():
    def __init__(self,width=1024,height=800):
        self.browser = Ghost()
        self.browser.set_viewport_size(width,height)


    def take_screenshot(self, url, path_to_picture):
        self.browser.open(url)
        self.browser.capture_to(path_to_picture, selector='.noncollapsed')


class Bot():
    def __init__(self, done_comments, directory):
        self.browser = Browser()
        self.uploader = Uploader()
        self.client = praw.Reddit(user_agent="Screenshotter 0.8 by /u/dionys")
        self.client.login(reddit_username, reddit_password)
        self.done_comments = set()
        self.path_to_picture = directory+'/current.png'


    class SetEncoder(JSONEncoder):
        def default(self, obj):
            if isinstance(obj, set):
                return list(obj)
            return JSONEncoder.default(self, obj)


    @staticmethod
    def load_already_done(directory):
        '''Loads json with already done comment IDs
        
        :param directory: path to json file
        '''
    
        try:
            with open(directory,'r') as done:
                return load(done)
        except IOError:
            return set()


    @staticmethod
    def save_already_done(done_comments, directory):
        '''Saves done_comments into json file
        
        :param done_comments: IDs to save
        :param directory: output path for json
        '''
    
        if len(done_comments):
            with open(directory,'w') as done:
                dump(done_comments, done, cls=Bot.SetEncoder)


    @staticmethod
    def save_log(path_to_log,error):
        with open(path_to_log,'a+') as log:
            log.write(now()+" - exception occurred({0}): {1}\n\n".format(error.errno, error.strerror))


    @staticmethod
    def is_indented_by_spaces(comment, min_lines=4):
        '''Decides whether the comment is indented.
    
        :param comment: comment to check indentation in
        :param min_lines: minimum amount of indented lines comment must have to be suspected of having ASCII/shibe/code... -- default is 4
        '''
    
        indented_line = 0
        for line in comment.split('\n\n'):
            if len(line)>4:
                if line[0:4]=="    ":
                    indented_line += 1
                else:
                    indented_line = 0
                    continue
            else:
                indented_line = 0
                continue
        return indented_line >= min_lines


    def loop(self):
        while(True): #never ending bot
            self.run()
            sleep(150)


    def run(self):
        try:
            checked_comments = set()
            subreddit_comments = self.client.get_subreddit(multi_reddit).get_comments(limit = None)#limit = None means fetch as many comments as possible
            for comment in subreddit_comments:
                if comment.id in self.done_comments or comment.id in checked_comments:
                    break
                checked_comments.add(comment.id)
                if self.is_indented_by_spaces(comment.body,3):
                    self.done_comments.add(comment.id)
                    self.browser.take_screenshot(comment.permalink, self.path_to_picture)
                    screenshot = self.uploader.upload_screenshot(self.path_to_picture,"Author: "+comment.author.name+" from reddit.")
                    comment.reply('[Screenshot for mobile users!]('+screenshot+")\n\n[FAQ](http://www.reddit.com/r/ScreenshotsYourPost/comments/1rshcd/faq/)")
                    comment.upvote()
                    sleep(120)


if __name__ == "__main__":
    directory = path.dirname(path.realpath(__file__))
    bot = Bot(Bot.load_already_done(directory+'/already_done.json'), directory)
    try:
        bot.run()
    except Exception as e:
        Bot.save_log(directory+'bot_errors.log',e)
        Bot.save_already_done(bot.done_comments,directory+'/already_done.json')