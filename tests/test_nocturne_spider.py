import pytest
import time
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
from scrapy.http import HtmlResponse, Request
from src.syosetu_spider.spiders.nocturne_spider import NocturneSpider

TEST_URL = "https://novel18.syosetu.com"
TEST_URL_CODE = "/n7483cp/1/"
TEST_URL_LINK = "https://novel18.syosetu.com/n7483cp/1/"


@pytest.fixture
def mock_driver():
    with patch(
        "src.syosetu_spider.spiders.nocturne_spider.webdriver.Chrome"
    ) as MockWebDriver:
        mock_driver = MagicMock()
        MockWebDriver.return_value = mock_driver
        yield mock_driver


@pytest.fixture
def main_page_response(mock_driver):
    with open("tests/test_data/novel18_main_page.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    mock_driver.page_source = html_content
    request = Request(url=TEST_URL)
    response = HtmlResponse(
        url=TEST_URL, request=request, body=html_content, encoding="utf-8"
    )
    return response


@pytest.fixture
def chapter_page_response(mock_driver):
    with open("tests/test_data/novel18_chapter_page.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    mock_driver.page_source = html_content
    request = Request(
        url=f"{TEST_URL_LINK}",
        meta={"start_time": time.perf_counter()},
    )
    response = HtmlResponse(
        url=f"{TEST_URL_LINK}",
        request=request,
        body=html_content,
        encoding="utf-8",
    )
    return response


@pytest.fixture
def parsed_results_main_page(main_page_response):
    spider = NocturneSpider()
    return list(spider.parse(main_page_response))


@pytest.fixture
def parse_main_page(main_page_response):
    spider = NocturneSpider()
    results = list(spider.parse(main_page_response))

    soup = BeautifulSoup(main_page_response.text, "html.parser")
    return results, soup


@pytest.fixture
def parse_chapter_page(chapter_page_response):
    spider = NocturneSpider()
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
    assert results[0].url == f"{TEST_URL_LINK}"

    novel_code = results[0].url.split("/")[3]
    expected_novel_code = expected_link.split("/")[1]
    assert novel_code == "n7483cp"
    assert novel_code == expected_novel_code


def test_parse_main_page_meta_callback(main_page_response):
    spider = NocturneSpider()
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


def test_parse_chapters_volume_title(parse_chapter_page):
    novel_item, soup = parse_chapter_page
    # Test volume title
    volume_title = soup.select_one("div.c-announce-box span")
    expected_volume = volume_title.text if volume_title else ""
    assert novel_item["volume_title"] == expected_volume


def test_parse_chapters_start_end_numbers(parse_chapter_page):
    novel_item, soup = parse_chapter_page
    # Test chapter fields
    chapter_start_end = soup.select_one("div.p-novel__number").text
    assert novel_item["chapter_start_end"] == "1/288"
    assert novel_item["chapter_start_end"] == chapter_start_end
    assert novel_item["chapter_number"] == "1"


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
    # selects all paragraph (<p>) elements where the id attribute starts with 'L' and concatenates the text
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
    spider = NocturneSpider()
    results = list(spider.parse_chapters(chapter_page_response))

    soup = BeautifulSoup(chapter_page_response.text, "html.parser")
    next_page = soup.select_one("div.c-pager a.c-pager__item--next")

    assert (
        str(next_page)
        == '<a class="c-pager__item c-pager__item--next" href="/n7483cp/2/">次へ</a>'
    )

    next_request = results[1]
    expected_url = next_page["href"]

    assert next_request.url == "https://novel18.syosetu.com/n7483cp/2/"
    assert next_request.url == f"{TEST_URL}{expected_url}"

    assert next_request.callback == spider.parse_chapters
