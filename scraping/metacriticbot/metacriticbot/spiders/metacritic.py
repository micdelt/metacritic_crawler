import string
from scrapy.spiders import Spider
from scrapy.selector import Selector
from scrapy.http import Request

from metacriticbot.items import Game

#Helper functions
def safe_extract(selector, xpath_query):
    """
    Helper function that extracts info from selector object
    using the xpath query constrains. 
    If nothing can be extracted, NA is returned.
    """
    val = selector.xpath(xpath_query).extract()
    return val[0].strip() if val else ''
  
    
class MetacriticSpider(Spider):
    """
    Goal: Scrape all PC games
    1. Start with all pc games with noletter starting
    2. Get links for page 1..n for letter
    3. Go to next letter [a-z].
    4. Repeat.
    
    
    scrapy crawl myspider -a category=electronics -a domain=system

    class MySpider(scrapy.Spider):
    name = 'myspider'

    def __init__(self, platform='pc', *args, **kwargs):
        super(MySpider, self).__init__(*args, **kwargs)
        self.platform = platform
        self.domain = domain
        # ...    
    
    """
    
    name = "metacritic"
    allowed_domains = ["metacritic.com"]
    game_no = 0

    def __init__(self, platform='pc', *args, **kwargs):
        super(MetacriticSpider, self).__init__(*args, **kwargs)
        self.platform = platform
        self.start_urls = ['http://www.metacritic.com/browse/games/title/%s/' % platform]

    #Get genre list from start_url, generate requests to parse genre pages later
    def parse(self, response):
        letter_links = [self.start_urls[0] + letter for letter in string.ascii_lowercase]
	    	
        requests = [Request(url = URL, callback = self.parse_letter) for URL in letter_links]
        requests.extend(self.parse_letter(response))
        #requests = self.parse_letter(response)
        self.log("###INITIAL PARSING ### " + str(len(letter_links)) + " Letters IN THIS TOTAL LIST " + response.url)
        return requests

    #Get all pages for a letter, send them to page parser
    def parse_letter(self, response):
        try:
            page_links = [response.url + "?page=" + str(i) for i in range(int(response.xpath('//li[@class="page last_page"]/a/text()').extract()[0]))]
        except IndexError:
            page_links = []
            
        requests = [Request(url = URL, callback = self.parse_page) for URL in page_links]
        requests.extend(self.parse_page(response))
        self.log("###PARSING LETTER### " + str(len(page_links)) + " PAGES IN THIS LETTER " + response.url)
        return requests

    #Get all games for a page
    def parse_page(self, response):
        game_links = ["http://metacritic.com" + postfix for postfix in response.xpath('//ol[@class="list_products list_product_condensed"]/li/div/div/a/@href').extract()]
        meta_genre = response.xpath('//div[@class="module products_module list_product_condensed_module "]/div/div/h2[@class="module_title"]/text()').extract()[0].strip()
        requests = [Request(url = URL, callback = self.parse_game) for URL in game_links]
        self.log("###PARSING PAGE### " + str(len(game_links)) + " GAMES IN THIS PAGE " + response.url)
        return requests

    def parse_game(self, response):
        sel = Selector(response, type = 'html')
        game = Game()
        # General info
        game['title'] = safe_extract(sel, '//h1[@class="product_title"]/a/span[@itemprop="name"]/text()')
        game['link'] = response.url
        game['release_date'] = safe_extract(sel, '//span[@itemprop="datePublished"]/text()')
        game['developer'] = safe_extract(sel, '//li[@class="summary_detail developer"]/span[@class="data"]/text()')
        game['publisher'] = safe_extract(sel, '//li[@class="summary_detail publisher"]/span[@class="data"]/a/span/text()')
        #game['platform'] = safe_extract(sel, '//span[@class="platform"]/a/span[@itemprop="device"]/text()')
        game['maturity_rating'] = safe_extract(sel, '//span[@itemprop="contentRating" and @class="data"]/text()')
        #game['genre'] = response.meta['genre'] #Getting genre from original 18 genre-like sections
        game['genre_tags'] = safe_extract(sel, '//span[@itemprop="genre" and @class="data"]/text()')
        #scores
        game['metascore'] = safe_extract(sel, '//span[@itemprop="ratingValue"]/text()')
        game['critics_reviews_count'] = safe_extract(sel, '//span[@itemprop="reviewCount"]/text()')
        game['user_score'] = safe_extract(sel, '//div[@class="userscore_wrap feature_userscore"]/a/div/text()')
        game['user_reviews_count'] = safe_extract(sel, '//div[@class="userscore_wrap feature_userscore"]/div/p/span/a/text()')
        print("%d\t%s" % (self.game_no, game['title']))
        self.game_no += 1
        yield game
