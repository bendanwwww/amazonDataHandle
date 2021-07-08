# 亚马逊数据处理工具
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

class handle(object):
    driver = webdriver.Chrome("/Users/lsy/Downloads/chromedriver")

    def run(self, key):
        # 打开网页
        self.driver.get("https://xp.sellermotor.com/selection/index/market-insight")
        # 判断是否未登录
        # 等待扫码
        while not self.check_login():
            print("等待登陆")
            # 隔1s检查一次
            time.sleep(1)
        print("登陆完成")
        # 输入关键字
        input_element = self.driver.find_element_by_id("search-keyword")
        input_element.send_keys(key)
        input_element.send_keys(Keys.ENTER)
        # 循环10次取出url
        url_list = []
        for i in range(9):
            table_element = self.get_element_retry("top100-list")
            tbody_element = self.get_element_by_tag_name_retry(table_element, "tbody")
            tr_element = self.get_elements_by_tag_name_retry(tbody_element, "tr")
            for tr in tr_element:
                url = tr.find_element_by_class_name("text-left").find_element_by_tag_name("a").get_attribute("href")
                print(url)
                url_list.append(url)
            # 点击下一页
            next_page_element = self.driver.find_element_by_class_name("page-next")
            a_element = next_page_element.find_element_by_tag_name("a")
            a_element.click()
        # 爬取亚马逊信息
        goods_data = []
        for url in url_list:
            goods_data.append(self.get_amazon_good_info(url))

        print(goods_data)
        # driver.close()

    # 检查登陆
    def check_login(self):
        try:
            self.driver.find_element_by_id("qrcode-img")
            return False
        except:
            return True

    # 不断尝试获取元素 阻塞
    def get_element_retry(self, id):
        #
        for i in range(1000000):
            try:
                element = self.driver.find_element_by_id(id)
                return element
            except:
                print("页面未加载完成 等待")
                time.sleep(1)

    # 不断尝试获取元素 阻塞
    def get_elements_by_tag_name_retry(self, element, id):
        for i in range(1000000):
            try:
                el = element.find_elements_by_tag_name(id)
                if len(el) == 0:
                    time.sleep(1)
                    continue
                return el
            except:
                print("页面未加载完成 等待")
                time.sleep(1)

    # 不断尝试获取元素 阻塞
    def get_element_by_tag_name_retry(self, element, id):
        for i in range(1000000):
            try:
                el = element.find_element_by_tag_name(id)
                return el
            except:
                print("页面未加载完成 等待")
                time.sleep(1)

    # 获取亚马逊商品信息
    def get_amazon_good_info(self, url):
        # 打开一个新的浏览器
        amazon_driver = webdriver.Chrome("/Users/lsy/Downloads/chromedriver")
        amazon_driver.get(url)
        data = []
        amazon_driver.close()
        return data
s = handle()
s.run("chairs")