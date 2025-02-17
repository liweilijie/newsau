import pickle
import re

from bs4 import BeautifulSoup
from scrapy.selector import Selector
from urllib.parse import urljoin

import logging

from newsau.items import AfrDataItem
from newsau.utils import common

logger = logging.getLogger('parse')

def afr_parse_home(html):

    home = "https://www.afr.com/"
    body = Selector(text=html)

    sections = body.xpath('//*[@id="content"]/section[2]//a/@href').extract()

    total = 0
    for a in sections:
        # for a in sections.xpath('//a/@href').extract():
        url = urljoin(home, a)
        if contains_date(url):
            logger.info(f'a:{url}')
            total += 1
    print(len(sections), total)

    print(sections)

def contains_date(url: str) -> bool:
    pattern = r'\b(\d{4})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\b'
    return bool(re.search(pattern, url))


def afr_parse_detail(html):

    body = Selector(text=html)

    post_content = ""

    post_title = body.xpath('//*[@id="content"]/header//h1/text()').extract_first('').strip()
    if post_title == '' or post_title is None:
        return

    logger.info(f'post_title:{post_title}')

    # //*[@id="content"]/header/div[1]/p
    post_sub_title = body.xpath('//*[@id="content"]/header/p[2]/text()').extract_first('').strip()
    logger.info(f'post_sub_title:{post_sub_title}')
    if post_sub_title == '' or post_sub_title is None:
        post_sub_title = body.xpath('//*[@id="content"]/header/div[1]/p').extract_first('').strip()
    if post_sub_title == '' or post_sub_title is None:
        post_sub_title = body.xpath('//*[@id="content"]/header/p').extract_first('').strip()

    if post_sub_title == '' or post_sub_title is None:
        logger.info(f'post_sub_title is empty.')
    else:
        post_content = post_sub_title

    post_time = body.xpath('//*[@id="content"]//time[@data-testid="ArticleTimestamp-time"]/text()').extract_first('').strip()
    logger.info(f'post_time:{post_time}')
    if post_time == '' or post_time is None:
        # //*[@id="content"]/div[1]/section/section/section/div[1]/time
        post_time = body.xpath('//*[@id="content"]/div[2]/section/div[1]/time/text()').extract_first('').strip()

    post_author = body.xpath('//*[@data-testid="AuthorURL"]/text()').extract_first('').strip()
    logger.info(f'post_author:{post_author}')
    if post_author == '' or post_author is None:
        post_author = body.xpath('*[@data-testid="AuthorNames"]/span/text()').extract_first('').strip()

    # first find the data-testid="beyondwords-player-wrapper" and the brother's <p>
    # body.xpath('//input[@data-test="username"]//following-sibling::*[name()="svg"][@data-prefix="fas"]')
    post_content_before = body.xpath('//div[@id="beyondwords-player"]//parent::div/following-sibling::*[name()="p"]').extract()
    if not post_content_before:
        logger.info(f'post_content_before is empty by beyondwords-player.')
        # //*[@id="content"]/div[2]
        post_content_before = body.xpath('//*[@id="content"]/div[2]').extract_first('').strip()
        if post_content_before == "" or post_content_before is None:
            # //*[@id="content"]/div[1]/section
            post_content_before = body.xpath('//*[@id="content"]/div[1]/section').extract_first('').strip()
            logger.info(f'post_content_before is empty.')
        else:
            post_content += post_content_before

        logger.info(f'post_content_before:{post_content_before}')

    else:
        post_content_before = ''.join(post_content_before)
        post_content += post_content_before

    post_content_end = body.xpath('//*[@id="endOfArticle"]').extract_first('').strip()
    if post_content_end == "" or post_content_end is None:
        # //*[@id="endOfArticle"]
        logger.info(f'post_content_end is empty.')
    else:
        post_content = post_content + post_content_end

    # if //*[@id="content"]/div[2]/div[1]'s id == "endOfArticle" and just xpath endOfArticle
    idname = body.xpath('//*[@id="content"]/div[2]/div[9]').xpath('@id').extract_first('')
    if body.xpath('//*[@id="content"]/div[2]/div[1]').xpath('@id').extract_first('') == 'endOfArticle':
        logger.warning(f'post_content only one part.')
        post_content = body.xpath('//*[@id="endOfArticle"]').extract_first('').strip()

    logger.info(f'post_content_end:{post_content_end}')

    afr_item = AfrDataItem()
    afr_item["name"] = 'afr'

    afr_item["origin_title"] = post_title
    afr_item["topic"] = 'financial'
    afr_item["url"] = 'ttt'
    afr_item["url_object_id"] = common.get_md5(afr_item["url"])

    # 'Feb 12, 2025 – 10.41am'
    # afr_item["post_date"] = common.convert_to_datetime(post_time)
    afr_item["post_date"] = common.afr_convert_to_datetime(afr_item.get("post_time", ""))

    # self.mysqlObj.get_news_category(self.name, afr_item["topic"])
    afr_item["category"] = "投资、理财"

    afr_item["front_image_url"] = []

    logger.info(f'post_content:{post_content}')

    # process the content
    # find all the images src in the post_content
    # and store these images src
    # and replace the domain of the src in post_content
    soup = BeautifulSoup(post_content, "html.parser")

    # delete source element TODO: need optimization
    for picture in soup.find_all('picture'):
        for source in picture.find_all('source'):
            source.decompose()

    for img in soup.find_all('img'):
        if img['src'].startswith("https") or img['src'].startswith("http"):
            afr_item["front_image_url"].append(img['src'])  # append origin url to download
            img['src'] = common.get_finished_image_url('afr', afr_item["url_object_id"], img['src'])  # replace our website image url from cdn
            if "srcset" in img.attrs:
                del img.attrs["srcset"]
            if "data-pb-im-config" in img.attrs:
                del img.attrs["data-pb-im-config"]
        else:
            img.decompose()

    # find all a label
    for a in soup.find_all('a'):
        # replace all a label with its text
        a.replace_with(a.text)

    # trim data-testid="beyondwords-player-wrapper"
    for div in soup.find_all('div', {"data-testid": "beyondwords-player-wrapper"}):
        div.decompose()

    # trim div id="beyondwords-player"
    for div in soup.find_all('div', {"id": "beyondwords-player"}):
        div.decompose()

    # trim div data-experiment-target="relatedStory"
    for div in soup.find_all('div', {"data-experiment-target": "relatedStory"}):
        div.decompose()

    # trim span data-component="Loading" data-print="inline-media"
    for span in soup.find_all('span', {"data-component": "Loading"}):
        span.decompose()

    # trim <small class="acd99af3e011c9b90ee4" style="display: block;">Advertisement</small>
    for small in soup.find_all('small', string="Advertisement"):
        small.decompose()

    # aria-label="Advertisement"
    for label in soup.find_all('iframe', {"aria-label": "Advertisement"}):
        label.decompose()

    # num_text_element = bsobj.find('span', {'class': 'nums_text'})
    # nums = filter(lambda s: s == ',' or s.isdigit(), num_text_element.text)
    # elements = soup.find_all('div', {'class': re.compile('c-container')})
    # for element in elements:
    #     title = element.h3.a.text.strip() if element.h3 and element.h3.a else ""
    #     link = element.h3.a['href'] if element.h3 and element.h3.a else ""

    post_content = str(soup)
    afr_item["origin_content"] = post_content

    logger.info(f'afr_item:{afr_item}')

    soup = BeautifulSoup(html, "html.parser")
    return soup

def url_join_t():
    home = "https://www.afr.com/"
    sub = "/world/central-america"
    rt = urljoin(home, sub)
    print(rt)


if __name__ == "__main__":
    content = pickle.load(open("../../p1.html", "rb"))
    rt = afr_parse_detail(content)
    logger.info(rt)
    # url_join_t()
    # content = pickle.load(open("../../home.html", "rb"))
    # rt = afr_parse_home(content)
    # logger.info(rt)
