# -*- coding: utf-8 -*-

from config import *

import praw #wrapper for connecting to reddit
from time import sleep  #for sleeping
from pyimgur import Imgur #wrapper for uploading to imgur
from ghost import Ghost
from json import dump,load,JSONEncoder
from os import path
from sys import exc_info


class Uploader():
    def __init__(self):
        self.uploader = Imgur(client_id=imgur_key, client_secret=imgur_secret)
    
    def upload_screenshot(path,text):
        '''Uploads screenshot from url to imgur.
        
        :param url: url of uploaded picture
        :param text: text to describe the image
        '''
    
        uploaded_image = self.uploader.upload_image(path_to_picture, title=text)
        return uploaded_image.link.encode('ascii','ignore')

class Browser():
    def __init__(self):
        self.browser = Ghost()
        self.browser.set_viewport_size(1024,800)
    
    def take_screenshot(self, url, path_to_picture):
        self.browser.open(url)
        self.browser.capture_to(path_to_picture, selector='.noncollapsed')


class Bot():
    def __init__(self, checked_comments, directory):
        self.browser = Browser()
        self.uploader = Uploader()
        self.client = praw.Reddit(user_agent="Screenshotter 0.8 by /u/dionys")
        self.client.login(reddit_username, reddit_password)
        self.checked_comments = set()
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
    def save_already_done(checked_comments, directory):
        '''Saves checked_comments into json file
        
        :param checked_comments: IDs to save
        :param directory: output path for json
        '''
    
        if len(checked_comments):
            with open(directory,'w') as done:
                dump(checked_comments, done, cls=SetEncoder)


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
            subreddit_comments = self.client.get_subreddit(multi_reddit).get_comments(limit = None)#limit = None means fetch as many comments as possible
            for comment in subreddit_comments:
                if comment.id in self.checked_comments:
                    sleep(300)
                    break #we hit a wall at this point we can get new batch of comments
                self.checked_comments.add(comment.id)
                if self.is_indented_by_spaces(comment.body,3):
                    self.browser.take_screenshot(comment.permalink, self.path_to_picture)
                    screenshot = self.uploader.upload_screenshot(self.path_to_picture,"Author: "+comment.author.name+" from reddit.")
                    #print screenshot
                    #print comment
                    comment.reply('[Screenshot for mobile users!]('+screenshot+")\n\n[FAQ](http://www.reddit.com/r/ScreenshotsYourPost/comments/1rshcd/faq/)")
                    sleep(120)
                    comment.upvote()
            sleep(150)


if __name__ == "__main__":
    directory = path.dirname(path.realpath(__file__))
    bot = Bot(Bot.load_already_done(directory+'/already_done.json'), directory)
    try:
        bot.loop()
    except praw.errors.RateLimitExceeded:
        sleep(600)
        bot.loop()
    except Exception:
        print 'Something went horribly wrong... I will try to save already_done_comments. Exception occured: ', exc_info()[0]
        Bot.save_already_done(bot.checked_comments,path_to_done)
        raise