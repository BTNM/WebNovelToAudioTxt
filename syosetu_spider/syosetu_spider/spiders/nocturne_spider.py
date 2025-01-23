import scrapy
import time
import logging
from bs4 import BeautifulSoup
from ..items import WebnoveltoaudiotxtItem
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urljoin


class NocturneSpider(scrapy.Spider):
    name = "nocturne_spider"
    allowed_domains = ["novel18.syosetu.com"]

    custom_settings = {
        "LOG_LEVEL": "INFO",
        "FEEDS": {
            f"{name}.jsonl": {
                "format": "jsonlines",
                "encoding": "utf8",
                "store_empty": False,
                "overwrite": True,
            }
        },  # Will be set dynamically in __init__
    }

    # start_urls = [
    #     "https://novel18.syosetu.com/n0153ce/",
    # ]

    def __init__(self, start_urls=None, start_chapter=None, *args, **kwargs):
        super(NocturneSpider, self).__init__(*args, **kwargs)
        self.start_chapter = start_chapter
        if start_urls:
            self.start_urls = [start_urls]
            # ncode = start_urls.split("/")[-2]
        else:
            self.start_urls = ["https://novel18.syosetu.com/n0153ce/"]
            # ncode = "n4750dy"

    # Parse novel main page first before parsing chapter content
    def parse(self, response):
        logging.info("Start nocturne spider parse main_page crawl\n")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--log-level=3")  # Suppress logs
        options.add_argument("--disable-logging")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(5)

        driver.get(response.url)
        enter_button = driver.find_element(By.ID, "yes18")
        enter_button.click()

        soup_parser = BeautifulSoup(driver.page_source, "html.parser")
        main_page = soup_parser.select_one("div#novel_ex.p-novel__summary").text

        if main_page is not None:
            novel_description = soup_parser.select_one(
                "div#novel_ex.p-novel__summary"
            ).text
            # first chapter link example '/n1313ff/74/'
            first_chapter_link = soup_parser.select_one("div.p-eplist__sublist > a")[
                "href"
            ]
            # logging.info(f"first_chapter_link: {first_chapter_link}")
            # "https://ncode.syosetu.com / n1313ff / 74 /"
            novel_code = first_chapter_link.split("/")[1]
            # logging.info(f"novel_code: {novel_code}")
            # start_chapter = "55"
            if self.start_chapter:
                chapter_link: str = f"/{novel_code}/{self.start_chapter}/"
            else:
                chapter_link = first_chapter_link

            # get the first chapter link and pass novel desc to the parse_chapters method
            starting_page = urljoin("https://novel18.syosetu.com/", chapter_link)
            logging.info(f"Starting page: {starting_page}\n")
            yield scrapy.Request(
                starting_page,
                callback=self.parse_chapters,
                meta={
                    "novel_description": novel_description,
                    "start_time": time.perf_counter(),
                    "driver": driver,
                },
            )

    def parse_chapters(self, response):
        driver = response.meta.get("driver")
        driver.get(response.url)
        enter_button = driver.find_element(By.ID, "yes18")
        enter_button.click()

        soup_parser = BeautifulSoup(driver.page_source, "html.parser")
        # Calculate the time taken to crawl the chapter from request to end of processing
        time_start = response.meta.get("start_time")

        # novel_description retrieved from meta dictionary, and passed to next parse_chapters
        novel_item = WebnoveltoaudiotxtItem()
        novel_item["novel_title"] = soup_parser.select(
            "div.c-announce-box div.c-announce a"
        )[1].text

        novel_description = response.meta.get("novel_description")
        novel_item["novel_description"] = novel_description
        volume_title = soup_parser.select_one("div.c-announce-box span")
        novel_item["volume_title"] = volume_title.text if volume_title else ""

        chapter_start_end = soup_parser.select_one("div.p-novel__number").text
        novel_item["chapter_start_end"] = chapter_start_end
        novel_item["chapter_number"] = chapter_start_end.split("/")[0]
        novel_item["chapter_title"] = soup_parser.select_one(
            "h1.p-novel__title.p-novel__title--rensai"
        ).text

        foreword = soup_parser.select_one(
            "div.p-novel__body div.js-novel-text.p-novel__text--preface"
        )
        if foreword:
            novel_item["chapter_foreword"] = "\n".join(
                p.text for p in foreword.select("p")
            )
        novel_item["chapter_text"] = "\n".join(
            p.text
            for p in soup_parser.select_one(
                "div.p-novel__body div.js-novel-text.p-novel__text"
            ).select("p[id^='L']")
        )
        afterword = soup_parser.select_one(
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

        next_page_element = soup_parser.select_one("div.c-pager a.c-pager__item--next")
        if next_page_element is not None:
            next_page_href = next_page_element["href"]
            # logging.info(f"Next page href: {next_page_href}")
            # next_page = response.urljoin(next_page_href)
            next_page = urljoin("https://novel18.syosetu.com/", next_page_href)
            yield scrapy.Request(
                next_page,
                callback=self.parse_chapters,
                meta={
                    "novel_description": novel_description,
                    "start_time": time.perf_counter(),
                    "driver": driver,
                },
            )
