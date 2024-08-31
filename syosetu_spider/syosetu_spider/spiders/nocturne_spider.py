import scrapy
from syosetu_spider.items import WebnoveltoaudiotxtItem

from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
import logging

from syosetu_spider.middlewares import CustomRedirectMiddleware

# Reduce the verbosity of the logs
# logging.basicConfig(level=logging.INFO)
# logging.getLogger("urllib3").setLevel(logging.WARNING)
# logging.getLogger("selenium").setLevel(logging.WARNING)
# logging.getLogger("WDM").setLevel(logging.WARNING)


class NocturneSpider(scrapy.Spider):
    name = "nocturne_spider"
    allowed_domains = ["novel18.syosetu.com"]
    handle_httpstatus_list = [301, 302]

    start_urls = [
        "https://novel18.syosetu.com/n4913gc/",
    ]

    def __init__(self, *args, **kwargs):
        super(NocturneSpider, self).__init__(*args, **kwargs)

        # Initialize Selenium WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Reduce logging output
        logging.getLogger("selenium").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(
            logging.WARNING
        )

        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()), options=options
        )

    # def __init__(self, *args, **kwargs):
    #     super(NocturneSpider, self).__init__(*args, **kwargs)
    #     # Set up Selenium WebDriver with headless option and logging preferences
    #     options = Options()
    #     options.add_argument("--headless")  # Run in headless mode
    #     options.add_argument("--disable-gpu")  # Applicable to Windows OS only
    #     options.add_argument("--no-sandbox")  # Bypass OS security model
    #     options.add_argument(
    #         "--disable-dev-shm-usage"
    #     )  # Overcome limited resource problems
    #     options.add_argument("--log-level=3")  # Suppress logs
    #     options.add_argument("--silent")  # Additional option to suppress logs
    #     options.set_capability(
    #         "goog:loggingPrefs", {"performance": "OFF", "browser": "OFF"}
    #     )

    #     # Reduce logging output
    #     logging.getLogger("selenium").setLevel(logging.WARNING)
    #     logging.getLogger("urllib3").setLevel(logging.WARNING)
    #     logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(
    #         logging.WARNING
    #     )

    #     self.driver = webdriver.Chrome(
    #         service=ChromeService(ChromeDriverManager().install()), options=options
    #     )

    custom_settings = {
        "FEEDS": {
            # os.path.join(home_path, "output1.jsonl"): {
            # os.path.join(download_path, "output1.jsonl"): {
            # os.path.join(home_path, "Desktop", "output1.jsonl"): {
            f"{name}.jsonl": {
                "format": "jsonlines",
                "encoding": "utf8",
                "store_empty": False,
                "indent": None,
            },
        },
        "DOWNLOADER_MIDDLEWARES": {
            "syosetu_spider.middlewares.CustomRedirectMiddleware": 600,
        },
        # "LOG_LEVEL": "INFO",  # default logging level=Debug, Set logging level to reduce terminal output
    }

    # def parse(self, response):
    #     self.driver.get(response.url)

    #     # Handle the age verification page if present
    #     if "novel18.syosetu.com" in response.url:
    #         time.sleep(2)  # Wait for the page to load
    #         try:
    #             enter_button = self.driver.find_element(By.ID, "yes18")
    #             enter_button.click()
    #             time.sleep(2)  # Wait for the page to load after clicking
    #         except Exception as e:
    #             self.logger.error(f"Error during age verification: {e}")

    #     # Get the page source after possible verification
    #     page_source = self.driver.page_source
    #     # logging.info(f"page_source: {page_source}")

    #     # Pass the page source to Scrapy for further parsing
    #     response = HtmlResponse(
    #         url=self.driver.current_url, body=page_source, encoding="utf-8"
    #     )

    #     return self.parse_main_page(response)

    def start_requests(self):
        # Assign the WebDriver to the CustomRedirectMiddleware before starting requests
        for mw in self.crawler.engine.downloader.middleware.middlewares:
            if isinstance(mw, CustomRedirectMiddleware):
                mw.driver = self.driver
                break
        else:
            self.logger.error("CustomRedirectMiddleware not found in middleware stack.")
            return

        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)

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
                    # "dont_redirect": True,
                },
            )

    # Parse novel main page first before parsing chapter content
    def parse_main_page(self, response):
        """
        Parses the main page of the novel and extracts the novel description and link to the first chapter.
        Args:
            response: The response object representing the main page of the novel.
        Returns:
            None. Sends a request to the first chapter's page.
        """
        logging.info(f"url: {response.url}")
        main_page = response.xpath('//div[@class="index_box"]')

        logging.info(f"main_page: {main_page}")
        if main_page is not None:
            novel_description = "\n".join(
                response.xpath('//div[@id="novel_ex"]/text()').getall()
            )
            # first chapter link example: '/n1313ff/74/'
            first_chapter_link = response.xpath(
                '//dl[@class="novel_sublist2"]/dd[@class="subtitle"]/a/@href'
            )[0].get()
            logging.info(f"first_chapter_link: {first_chapter_link}")

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

    # def parse(self, response):
    #     # Check if we are on the age verification page
    #     if "ageauth" in response.url:
    #         self.logger.info("Handling age verification redirect")
    #         # Extract the actual target URL from the redirect
    #         target_url = response.xpath('//a[@id="yes18"]/@href').get()
    #         if target_url:
    #             yield scrapy.Request(
    #                 url=target_url,
    #                 callback=self.parse_main_page,
    #                 meta={"dont_redirect": True},
    #             )
    #         else:
    #             self.logger.error("Failed to find the age verification link.")
    #     else:
    #         # Handle the actual content page
    #         yield from self.parse_main_page(response)

    # def parse_main_page(self, response):
    #     # Now we assume we have passed the age verification
    #     logging.info(f"url: {response.url}")
    #     main_page = response.xpath('//div[@class="index_box"]')
    #     if main_page:
    #         novel_description = "\n".join(
    #             response.xpath('//div[@id="novel_ex"]/text()').getall()
    #         )
    #         first_chapter_link = response.xpath(
    #             '//dl[@class="novel_sublist2"]/dd[@class="subtitle"]/a/@href'
    #         ).get()
    #         if first_chapter_link:
    #             starting_page = response.urljoin(first_chapter_link)
    #             yield scrapy.Request(
    #                 starting_page,
    #                 callback=self.parse_chapters,
    #                 meta={
    #                     "novel_description": novel_description,
    #                     "start_time": time.perf_counter(),
    #                     "dont_redirect": True,
    #                 },
    #             )
    #         else:
    #             self.logger.error("Failed to find the first chapter link.")
    #     else:
    #         self.logger.error("Main page structure not found.")

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
                    # "dont_redirect": True,
                },
            )

    def closed(self, reason):
        # Make sure to close the Selenium WebDriver
        self.driver.quit()
        self.logger.info("Selenium WebDriver closed successfully.")
