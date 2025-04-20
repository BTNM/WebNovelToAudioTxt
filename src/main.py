import asyncio
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from syosetu_spider.spiders.syosetu_spider import SyosetuSpider
from syosetu_spider.spiders.nocturne_spider import NocturneSpider


def start_syosetu_crawler(start_url=None, start_chapter=None):
    """Start the SyosetuSpider crawler with optional start URL and chapter"""
    # Force use of SelectorEventLoop on Windows
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    process = CrawlerProcess(get_project_settings())
    process.crawl(SyosetuSpider, start_urls=start_url, start_chapter=start_chapter)
    process.start()


def start_nocturne_crawler(start_url=None, start_chapter=None):
    """Start the NocturneSpider crawler with optional start URL and chapter"""
    # Force use of SelectorEventLoop on Windows
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    process = CrawlerProcess(get_project_settings())
    process.crawl(NocturneSpider, start_urls=start_url, start_chapter=start_chapter)
    process.start()


def run_spiders(spiders_list):
    """Run multiple spiders sequentially"""
    # Force use of SelectorEventLoop on Windows
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    process = CrawlerProcess(get_project_settings())

    # Add all spiders to the process
    for spider_cls, url, chapter in spiders_list:
        process.crawl(spider_cls, start_urls=url, start_chapter=chapter)

    # Run all spiders
    process.start()


if __name__ == "__main__":
    # spiders_list = [
    #     (SyosetuSpider, "https://ncode.syosetu.com/n4750dy/", None),
    #     (NocturneSpider, "https://novel18.syosetu.com/n0153ce/", 60),
    # ]

    # print("Starting list of spiders...")
    # run_spiders(spiders_list)

    # Example usage:
    print("Starting Syosetu Spider...")
    start_syosetu_crawler("https://ncode.syosetu.com/n5194gp/")
    # start_syosetu_crawler("https://ncode.syosetu.com/n0763jx/")
    # print("Starting Nocturne Spider...")
    # start_nocturne_crawler("https://novel18.syosetu.com/n0153ce/", 60)
