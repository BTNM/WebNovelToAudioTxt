from turtle import st
import scrapy

# from scrapy.crawler import CrawlerProcess
# from ..items import WebnoveltoaudiotxtItem
from syosetu_spider.items import WebnoveltoaudiotxtItem
from scrapy.utils.log import configure_logging
from bs4 import BeautifulSoup
import logging
import time
import os
import re

# from multiprocessing import Process
# import os
# import sys
# from pathlib import Path

# run scrapy shell to test scrapy extract which content
# scrapy shell 'https://ncode.syosetu.com/n4750dy/1/'
# Need to move inside the project directory where scrapy.cfg file exists to run the spider
# cd SyosetsuScraper/src/scraper , cd scraper
# scrapy crawl syosetsu -o test2.json
# scrapy crawl syosetsu -o testjl.jl

# C:\Users\Bao Thien\.Bao Thien_todo.json
# DEFAULT_DB_FILE_PATH = Path.home().joinpath("." + Path.home().stem + "_todo.json")

# C:\Users\Bao Thien\Downloads
# Home directory path
# home_path = os.path.expanduser("~")
# download_path = os.path.expanduser("~").join("Downloads")
# drive_t = "T:\\"


class SyosetuSpider(scrapy.Spider):
    name = "syosetu_spider"
    allowed_domains = ["ncode.syosetu.com"]

    def __init__(self, start_urls=None, start_chapter=None, *args, **kwargs):
        super(SyosetuSpider, self).__init__(*args, **kwargs)
        self.start_chapter = start_chapter

    start_urls = [
        "https://ncode.syosetu.com/n4750dy/",
    ]

    # custom_settings = {
    #     "FEEDS": {
    #         os.path.join(home_path, "Desktop", "output1.jsonl"): {
    #             "format": "jsonlines",
    #             "encoding": "utf8",
    #             "store_empty": False,
    #             "indent": None,
    #         },
    #     },
    #     "LOG_LEVEL": "INFO",
    # }
    ncode = start_urls[0].split("/")[-2]

    custom_settings = {
        "FEEDS": {
            f"{ncode}.jsonl": {
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
        logging.info("Start syosetsu spider parse main_page crawl")
        soup_parser = BeautifulSoup(response.text, "html.parser")

        main_page = soup_parser.select_one("div#novel_ex.p-novel__summary").text

        if main_page is not None:
            novel_description = soup_parser.select_one(
                "div#novel_ex.p-novel__summary"
            ).text
            # first chapter link example '/n1313ff/74/'
            first_chapter_link = soup_parser.select_one("div.p-eplist__sublist > a")[
                "href"
            ]
            # "https://ncode.syosetu.com / n1313ff / 74 /"
            novel_code = first_chapter_link.split("/")[1]
            # start_chapter = "55"
            if self.start_chapter:
                chapter_link: str = f"/{novel_code}/{self.start_chapter}/"
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
        soup = BeautifulSoup(response.text, "html.parser")
        # Calculate the time taken to crawl the chapter from request to end of processing
        time_start = response.meta.get("start_time")

        # novel_description retrieved from meta dictionary, and passed to next parse_chapters
        novel_item = WebnoveltoaudiotxtItem()
        novel_item["novel_title"] = soup.select("div.c-announce-box div.c-announce a")[
            1
        ].text
        novel_description = response.meta.get("novel_description")
        novel_item["novel_description"] = novel_description
        volume_title = soup.select_one("div.c-announce-box span")
        novel_item["volume_title"] = volume_title.text if volume_title else ""

        chapter_start_end = soup.select_one("div.p-novel__number").text
        novel_item["chapter_start_end"] = chapter_start_end
        novel_item["chapter_number"] = chapter_start_end.split("/")[0]
        novel_item["chapter_title"] = soup.select_one(
            "h1.p-novel__title.p-novel__title--rensai"
        ).text

        foreword = soup.select_one(
            "div.p-novel__body div.js-novel-text.p-novel__text--preface"
        )
        if foreword:
            novel_item["chapter_foreword"] = "\n".join(
                p.text for p in foreword.select("p")
            )
        novel_item["chapter_text"] = "\n".join(
            p.text
            for p in soup.select_one(
                "div.p-novel__body div.js-novel-text.p-novel__text"
            ).select("p[id^='L']")
        )
        afterword = soup.select_one(
            "div.p-novel__body div.js-novel-text.p-novel__text--afterword"
        )
        if afterword:
            novel_item["chapter_afterword"] = "\n".join(
                p.text for p in afterword.select("p")
            )

        yield novel_item

        # Log the time taken to crawl the chapter
        time_end = time.perf_counter()
        crawl_time = time_end - time_start
        self.logger.info(
            f"Crawled chapter {novel_item['chapter_number']} in {crawl_time:.2f} seconds\n"
        )

        next_page_element = soup.select_one("div.c-pager a.c-pager__item--next")
        if next_page_element is not None:
            next_page_href = next_page_element["href"]
            next_page = response.urljoin(next_page_href)
            yield scrapy.Request(
                next_page,
                callback=self.parse_chapters,
                meta={
                    "novel_description": novel_description,
                    "start_time": time.perf_counter(),
                },
            )
