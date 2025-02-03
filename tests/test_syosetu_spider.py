import logging
import pytest
import time
from unittest.mock import patch
from bs4 import BeautifulSoup
from scrapy.http import HtmlResponse, Request
from src.syosetu_spider.spiders.syosetu_spider import SyosetuSpider

TEST_URL = "https://ncode.syosetu.com"


@pytest.fixture
def main_page_response():
    with open("tests/test_data/main_page.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HtmlResponse(url=TEST_URL, body=content, encoding="utf-8")


@pytest.fixture
def chapter_page_response():
    with open("tests/test_data/chapter_page.html", "r", encoding="utf-8") as f:
        content = f.read()
    request = Request(
        url=f"{TEST_URL}/n8611bv/4/",
        meta={"start_time": time.perf_counter()},
    )
    return HtmlResponse(
        url=f"{TEST_URL}/n8611bv/4/",
        body=content,
        encoding="utf-8",
        request=request,
    )


@pytest.fixture
def parsed_results_main_page(main_page_response):
    spider = SyosetuSpider()
    return list(spider.parse(main_page_response))


@pytest.fixture
def parse_main_page(main_page_response):
    spider = SyosetuSpider()
    results = list(spider.parse(main_page_response))

    soup = BeautifulSoup(main_page_response.text, "html.parser")
    return results, soup


@pytest.fixture
def parse_chapter_page(chapter_page_response):
    spider = SyosetuSpider()
    results = list(spider.parse_chapters(chapter_page_response))
    novel_item = results[0]

    soup = BeautifulSoup(chapter_page_response.text, "html.parser")
    return novel_item, soup


def test_parse_main_page_novel_description(parse_main_page):
    results, soup = parse_main_page

    # Check that correct novel description is extracted
    expected_description = soup.select_one("div#novel_ex.p-novel__summary").text
    assert "novel_description" in results[0].meta
    assert results[0].meta["novel_description"] == expected_description


def test_parse_main_page_first_chapter_link(parse_main_page):
    results, soup = parse_main_page

    # Check that correct first chapter link is used
    expected_link = soup.select_one("div.p-eplist__sublist > a")["href"]
    assert results[0].url == "https://ncode.syosetu.com/n8611bv/1/"
    assert results[0].url == f"{TEST_URL}{expected_link}"

    novel_code = results[0].url.split("/")[3]
    expected_novel_code = expected_link.split("/")[1]
    assert novel_code == "n8611bv"
    assert novel_code == expected_novel_code


def test_parse_main_page_meta_callback(main_page_response):
    spider = SyosetuSpider()
    results = list(spider.parse(main_page_response))

    soup = BeautifulSoup(main_page_response.text, "html.parser")
    # Verify request metadata
    assert "start_time" in results[0].meta
    assert isinstance(results[0].meta["start_time"], float)

    # Verify callback is set correctly
    assert results[0].callback == spider.parse_chapters


def test_parse_chapters_novel_title(parse_chapter_page):
    novel_item, soup = parse_chapter_page
    # Test novel title
    expected_title = soup.select("div.c-announce-box div.c-announce a")[1].text
    assert novel_item["novel_title"] == expected_title


def test_parse_chapters_volum_title(parse_chapter_page):
    novel_item, soup = parse_chapter_page
    # Test volume title
    volume_title = soup.select_one("div.c-announce-box span")
    expected_volume = volume_title.text if volume_title else ""
    assert novel_item["volume_title"] == expected_volume


def test_parse_chapters_start_end_numbers(parse_chapter_page):
    novel_item, soup = parse_chapter_page
    # Test chapter fields
    chapter_start_end = soup.select_one("div.p-novel__number").text
    assert novel_item["chapter_start_end"] == chapter_start_end
    assert novel_item["chapter_number"] == chapter_start_end.split("/")[0]


def test_parse_chapters_title_chapter(parse_chapter_page):
    novel_item, soup = parse_chapter_page

    expected_chapter_title = soup.select_one(
        "h1.p-novel__title.p-novel__title--rensai"
    ).text
    assert novel_item["chapter_title"] == expected_chapter_title


def test_parse_chapters_content_foreword(parse_chapter_page):
    novel_item, soup = parse_chapter_page

    # Test chapter content fields
    foreword = soup.select_one(
        "div.p-novel__body div.js-novel-text.p-novel__text--preface"
    )
    if foreword:
        expected_foreword = "\n".join(p.text for p in foreword.select("p"))
        assert novel_item["chapter_foreword"] == expected_foreword


def test_parse_chapters_content_text(parse_chapter_page):
    novel_item, soup = parse_chapter_page

    chapter_text = soup.select_one("div.p-novel__body div.js-novel-text.p-novel__text")
    expected_text = "\n".join(p.text for p in chapter_text.select("p[id^='L']"))
    assert novel_item["chapter_text"] == expected_text


def test_parse_chapters_content_afterword(parse_chapter_page):
    novel_item, soup = parse_chapter_page

    afterword = soup.select_one(
        "div.p-novel__body div.js-novel-text.p-novel__text--afterword"
    )
    if afterword:
        expected_afterword = "\n".join(p.text for p in afterword.select("p"))
        assert novel_item["chapter_afterword"] == expected_afterword


def test_parse_chapters_next_page_link(chapter_page_response):
    spider = SyosetuSpider()
    results = list(spider.parse_chapters(chapter_page_response))

    soup = BeautifulSoup(chapter_page_response.text, "html.parser")
    next_page = soup.select_one("div.c-pager a.c-pager__item--next")

    assert (
        str(next_page)
        == '<a class="c-pager__item c-pager__item--next" href="/n8611bv/5/">次へ</a>'
    )

    next_request = results[1]
    expected_url = next_page["href"]

    assert next_request.url == f"https://ncode.syosetu.com/n8611bv/5/"
    assert next_request.url.endswith(expected_url)

    assert next_request.callback == spider.parse_chapters
