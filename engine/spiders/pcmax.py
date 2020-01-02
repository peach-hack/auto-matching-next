import scrapy

import time
# import datetime

from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import engine.env as env

from ..items.post import PostItem
from ..constants.common import USER_AGENT_PIXEL3

PCMAX_DOMAIN = 'pcmax.jp'
PCMAX_BASE_URL = 'https://pcmax.jp'
PCMAX_LOGIN_URL = "https://pcmax.jp/pcm/index.php"
PCMAX_ENTRY_URL = PCMAX_LOGIN_URL
PCMAX_BOARD_URL = ""
PCMAX_AREA_URL = ""


class PcmaxSpider(scrapy.Spider):
    name = 'pcmax'
    allowed_domains = [PCMAX_DOMAIN]
    start_urls = [PCMAX_LOGIN_URL]

    def __init__(self, area="神奈川県", days=7, *args, **kwargs):
        super(PcmaxSpider, self).__init__(*args, **kwargs)
        self.area = area
        self.days = int(days)

        options = ChromeOptions()

        # options.add_argument("--headless")

        options.add_argument('--user-agent={}'.format(USER_AGENT_PIXEL3))

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")

        mobile_emulation = {"deviceName": "Nexus 5"}
        options.add_experimental_option("mobileEmulation", mobile_emulation)

        self.driver = Chrome(options=options)

    def parse(self, response):

        # Login
        self.driver.get(response.url)

        self.driver.find_element_by_id("login-tab").click()
        self.driver.find_element_by_id("login_id").send_keys(
            env.PCMAX_LOGIN_USER)
        self.driver.find_element_by_id("login_pw").send_keys(
            env.PCMAX_LOGIN_PASSWORD)
        self.driver.find_element_by_name("login").click()

        time.sleep(5)
        return

        # 掲示板へ移動
        self.driver.get(PCMAX_BOARD_URL)
        # その他掲示板を選択
        self.driver.find_elements_by_css_selector(
            'li.ds_link_tab_item_bill')[1].click()

        time.sleep(5)

        try:
            while True:
                # ブラウザ有効のときはこれをコメントアウトすると下にスクロールする。
                # headlessのときはエラーするので注意
                script = 'window.scrollTo(0, document.body.scrollHeight);'
                self.driver.execute_script(script)
                script = 'document.querySelector("div#load_list_billboard_200.list_load").click();'  # noqa
                self.driver.execute_script(script)
                time.sleep(3)
        except Exception:
            pass

        response = response.replace(body=self.driver.page_source)

        post_list = response.css("li.ds_user_post_link_item_bill")

        for item in post_list:
            post = PostItem()

            partial_url = item.css('a::attr(href)').extract_first()

            post['id'] = partial_url.split('tid=')[1]
            post["url"] = "https:" + partial_url

            post["name"] = item.css(
                '.ds_post_body_name_bill::text').extract_first().strip(
                    '♀\xa0')  # noqa
            post["prefecture"] = self.area

            post["genre"] = item.css('p.round-btn::text').extract_first()

            age_info = item.css(
                '.ds_post_body_age::text').extract_first().split(
                    '\xa0')  # noqa
            post["city"] = age_info[1]
            post["age"] = age_info[0]

            image_url = item.css(
                '.ds_thum_contain_s::attr(style)').extract_first().strip(
                    'background-image: url(').strip(')')

            if 'noimage' in image_url:
                post['image_url'] = "https:" + image_url
            elif 'avatar' in image_url:
                post['image_url'] = "https:" + image_url
            else:
                post['image_url'] = image_url

            post['title'] = item.css('.ds_post_title::text').extract_first()
            post['post_at'] = item.css('.ds_post_date::text').extract_first()

            yield post

    def closed(self, reason):
        self.driver.close()