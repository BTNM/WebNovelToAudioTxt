import scrapy

# from scrapy.crawler import CrawlerProcess
# from ..items import WebnoveltoaudiotxtItem
from syosetu_spider.items import WebnoveltoaudiotxtItem
from multiprocessing import Process
from scrapy.utils.log import configure_logging
import logging
import time
import os
import sys
from pathlib import Path

# run scrapy shell to test scrapy extract which content
# scrapy shell 'https://ncode.syosetu.com/n4750dy/1/'
# Need to move inside the project directory where scrapy.cfg file exists to run the spider
# cd SyosetsuScraper/src/scraper , cd scraper
# scrapy crawl syosetsu -o test2.json
# scrapy crawl syosetsu -o testjl.jl

# C:\Users\Bao Thien\.Bao Thien_todo.json
# DEFAULT_DB_FILE_PATH = Path.home().joinpath("." + Path.home().stem + "_todo.json")


class SyosetuSpider(scrapy.Spider):
    name = "syosetu_spider"
    allowed_domains = ["ncode.syosetu.com"]

    def __init__(self, start_chapter=None, *args, **kwargs):
        super(SyosetuSpider, self).__init__(*args, **kwargs)
        self.start_chapter = start_chapter

    start_urls = [
        "https://ncode.syosetu.com/n4750dy/",
    ]

    custom_settings = {
        "FEEDS": {
            f"{name}.jsonl": {
                "format": "jsonlines",
                "encoding": "utf8",
                "store_empty": False,
                "indent": None,
            },
        },
        "LOG_LEVEL": "INFO",  # default logging level=Debug, Set logging level to reduce terminal output
    }

    # Parse novel main page first before parsing chapter content
    def parse(self, response):
        """
        Parses the main page of the novel and extracts the novel description and link to the first chapter.
        Args:
            response: The response object representing the main page of the novel.
        Returns:
            None. Sends a request to the first chapter's page.
        """
        # print("Start crawl main page: {}".format(default_timer()))
        main_page = response.xpath('//div[@class="index_box"]')
        if main_page is not None:
            novel_description = "\n".join(
                response.xpath('//div[@id="novel_ex"]/text()').getall()
            )
            # first chapter link example: '/n1313ff/74/'
            first_chapter_link = response.xpath(
                '//dl[@class="novel_sublist2"]/dd[@class="subtitle"]/a/@href'
            )[0].get()
            # "https://ncode.syosetu.com / n1313ff / 74 /"
            split_chapter_link = first_chapter_link.split("/")[1]
            # start_chapter = "55"
            if self.start_chapter:
                chapter_link = f"/{split_chapter_link}/{self.start_chapter}/"
            else:
                chapter_link = first_chapter_link

            # get the first chapter link and pass novel desc to the parse_chapters method
            starting_page = response.urljoin(chapter_link)
            yield scrapy.Request(
                starting_page,
                callback=self.parse_chapters,
                meta={
                    "novel_description": novel_description,
                    "start_time": time.perf_counter(),
                },
            )

    def parse_chapters(self, response):
        """
        Parses the content of a single chapter and yields a NovelItem object containing the extracted information.
        Args:
            response: The response object representing a chapter's page.
        Returns:
            A NovelItem object containing the extracted information from the chapter.
        """
        # Calculate the time taken to crawl the chapter from request to end of processing
        time_start = response.meta.get("start_time")

        # novel_description retrieved from meta dictionary, and passed to next parse_chapters
        novel_description = response.meta.get("novel_description")

        novel_item = WebnoveltoaudiotxtItem()
        novel_item["novel_title"] = response.xpath(
            '//div[@class="contents1"]/a[@class="margin_r20"]/text()'
        ).get()
        novel_item["novel_description"] = novel_description
        novel_item["volume_title"] = response.xpath(
            '//p[@class="chapter_title"]/text()'
        ).get()
        novel_item["chapter_start_end"] = response.xpath(
            '//div[@id="novel_no"]/text()'
        ).get()
        novel_item["chapter_number"] = (
            response.xpath('//div[@id="novel_no"]/text()').get().split("/")[0]
        )
        novel_item["chapter_title"] = response.xpath(
            '//p[@class="novel_subtitle"]/text()'
        ).get()
        novel_item["chapter_foreword"] = "\n".join(
            response.xpath(
                '//div[@id="novel_color"]/div[@id="novel_p"]/p/text()'
            ).getall()
        )
        novel_item["chapter_text"] = "\n".join(
            response.xpath(
                '//div[@id="novel_color"]/div[@id="novel_honbun"]/p/text()'
            ).getall()
        )
        novel_item["chapter_afterword"] = "\n".join(
            response.xpath(
                '//div[@id="novel_color"]/div[@id="novel_a"]/p/text()'
            ).getall()
        )
        yield novel_item

        # Log the time taken to crawl the chapter
        time_end = time.perf_counter()
        crawl_time = time_end - time_start
        self.logger.info(
            f"Crawled chapter {novel_item['chapter_number']} in {crawl_time:.2f} seconds"
        )

        next_page = response.xpath('//div[@class="novel_bn"]/a/@href')[1].get()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(
                next_page,
                callback=self.parse_chapters,
                meta={
                    "novel_description": novel_description,
                    "start_time": time.perf_counter(),
                },
            )
