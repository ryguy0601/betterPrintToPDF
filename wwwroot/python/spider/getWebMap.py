

import sys
import asyncio

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from twisted.internet import asyncioreactor
asyncioreactor.install()

import base64
from crochet import setup, wait_for
from scrapy import signals
from scrapy.crawler import CrawlerRunner
from scrapy.signalmanager import dispatcher
from urllib.parse import urlparse, urldefrag
import scrapy

setup()
runner = CrawlerRunner()

spider_results = {}

class WebMapSpider(scrapy.Spider):
    name = "webmap_spider"

    def __init__(self, start_url=None, username=None, password=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_url = start_url
        self.username = username
        self.password = password
        self.visited_urls = []
        self.seen = set()

        if username and password:
            credentials = f"{username}:{password}"
            encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
            self.auth_headers = {'Authorization': f'Basic {encoded_credentials}'}
        else:
            self.auth_headers = {}

        parsed = urlparse(self.start_url)
        self.allowed_domain = parsed.netloc

    def start_requests(self):
        yield scrapy.Request(
            url=self.start_url,
            headers=self.auth_headers,
            callback=self.parse
        )

    def parse(self, response):
        page_url = response.url

        if page_url not in self.seen:
            # self.visited_urls.append(page_url)
            self.seen.add(page_url)

        links = response.css('a::attr(href)').getall()
        absolute_links = [response.urljoin(link) for link in links]
        for link in absolute_links:
            clean_link, _ = urldefrag(link)
            if self.is_allowed(clean_link) and clean_link not in self.seen:
                #### PRINT HERE #####
                #print('clean ', clean_link,'\nfound on page', page_url,'\n')
                #### PRINT HERE #####
                self.visited_urls.append(clean_link)
                self.seen.add(clean_link)
                yield scrapy.Request(url=clean_link, headers=self.auth_headers, callback=self.parse)

    def is_allowed(self, url):
        parsed = urlparse(url)

        # Skip mailto:, javascript:, tel:, etc.
        if (
            parsed.scheme not in ["http", "https"]
            or url in self.visited_urls
            or url+'/' in self.visited_urls
            or url+'.aspx' in self.visited_urls
            or url.replace('.aspx','') in self.visited_urls
            or (url[:-1] if url.endswith("/") else url) in self.visited_urls
            or url.lower().endswith((".png", ".jpeg", ".jpg", ".pdf"))
            or 'index' in url.lower()
        ):
            return False

        return parsed.netloc == self.allowed_domain



def spider_closed(spider, reason):
    spider_results["urls"] = [spider.start_url]+list(spider.visited_urls)
    # spider_results["urls"] = [url for url in spider_results["urls"] if not url.lower().endswith(('.png', '.jpeg', '.pdf'))]
    # print(spider_results["urls"])
    # print(len(spider_results["urls"]))


@wait_for(timeout=60)
def run_spider(start_url, username=None, password=None):
    spider_results.clear()
    
    runner = CrawlerRunner()
    dispatcher.connect(spider_closed, signal=signals.spider_closed)
    d = runner.crawl(WebMapSpider, start_url=start_url, username=username, password=password)

    def _cleanup(_):
        dispatcher.disconnect(spider_closed, signal=signals.spider_closed)
        return _
    
    d.addBoth(_cleanup)
    return d


