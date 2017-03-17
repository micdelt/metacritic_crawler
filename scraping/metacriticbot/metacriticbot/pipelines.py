# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
import xlwt
from datetime import datetime
from scrapy.utils.project import get_project_settings
import os
from metacriticbot.items import Game

settings = get_project_settings()

def ton(num):
    try:
        return int(num)
    except ValueError:
        return ''

def get_year(test_date):
    DATE_FORMATS = ['%b %d, %Y','%B %Y','%Y']
    for date_format in DATE_FORMATS:
        try:
            my_date = datetime.strptime(test_date, date_format)
        except ValueError:
            pass
        else:
          break
    else:
      return ''
    return my_date.year
        
class MetacriticbotPipeline(object):
    def process_item(self, item, spider):
        #so that userscore resembles metascore 0..100 scale
        #some non-numeric values such as 'tbd' are left out 
        #for the sake of uniformity
        try:
            item['user_score'] = int(float(item['user_score'])*10)
        except ValueError:
            item['user_score'] = ''
        #convert to Year-month-day format
        item['release_date'] = get_year(item['release_date'])
        #leave only N out of "N Ratings" for user ratings
        user_ratings = item['user_reviews_count'].split()
        if len(user_ratings) > 0:
            item['user_reviews_count'] = user_ratings[0]
        if item['critics_reviews_count'] == '0':
            item['critics_reviews_count'] = ''
        return item
 
class XlsExportPipeline(object):

    def __init__(self):
        dispatcher.connect(self.spider_opened, signals.spider_opened)
        dispatcher.connect(self.spider_closed, signals.spider_closed)
        self.workbook = xlwt.Workbook()
        self.sheet = self.workbook.add_sheet("Metacritic") 
        self.row_number = 0
        self.columns = ['title','genre','maturity','year','user','critic','users_count','critics_count','developer','publisher']
        self.style_hyper = xlwt.easyxf('font: underline single,color 4')
        
    #write header
    def spider_opened(self, spider):
        for index,value in enumerate(self.columns):
            self.sheet.write(self.row_number, index, value) # row, column, value
        
    def spider_closed(self, spider):
        timestr = settings.get('TIMESTR')
        relpath = settings.get('RELPATH')
        xls_fname = os.path.join(relpath, 'data', "metacritic-" + timestr + ".xls")
        self.workbook.save(xls_fname) 
    
    def process_item(self, item, spider):
        self.row_number = self.row_number + 1
        #values = item.values()
        self.sheet.write(self.row_number, 0, xlwt.Formula('HYPERLINK("%s";"%s")' % (item['link'],item['title'].replace('"','""')) ), self.style_hyper)
        self.sheet.write(self.row_number, 1, item['genre_tags'])
        self.sheet.write(self.row_number, 2, item['maturity_rating'])
        self.sheet.write(self.row_number, 3, ton(item['release_date']))
        self.sheet.write(self.row_number, 4, ton(item['user_score']))
        self.sheet.write(self.row_number, 5, ton(item['metascore']))
        self.sheet.write(self.row_number, 6, ton(item['user_reviews_count']))
        self.sheet.write(self.row_number, 7, ton(item['critics_reviews_count']))
        self.sheet.write(self.row_number, 8, item['developer'])
        self.sheet.write(self.row_number, 9, item['publisher'])
        # for index, val in enumerate(values):
            # self.sheet.write(self.row_number, index, val) # row, column, value
        return item
