import scrapy


class NocturneSpiderSpider(scrapy.Spider):
    name = "nocturne_spider"
    allowed_domains = ["novel18.syosetu.com"]
    start_urls = ["https://novel18.syosetu.com"]

    def parse(self, response):
        pass
