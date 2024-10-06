import json
import re
import traceback

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from json import dump


# This code is written by the help of Amir Mohammad Fakhimi and Taha Akbari
class PaperCrawler:

    def initialize_driver(self):
        driver = webdriver.Chrome(executable_path='E:/programs/chromedriver.exe')
        driver.maximize_window()
        return driver

    def __init__(self):
        self.driver = self.initialize_driver()

    def get_abstract(self):
        try:
            button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH,
                                                                                      '//button[@aria-label="Expand truncated text" and @data-test-id="text-truncator-toggle"]')))
            actions = ActionChains(self.driver)
            actions.move_to_element(button).perform()
            button.click()
        except:
            pass
        return BeautifulSoup(self.driver.page_source, 'html.parser').find('meta', attrs={'name': 'description'})[
            'content']

    def get_references(self):
        base_url = 'https://www.semanticscholar.org/'
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@id="cited-papers"]')))
        return [urljoin(base_url, paper.get('href')) for paper in
                BeautifulSoup(self.driver.page_source, 'html.parser').find('div', {'id': 'cited-papers'}).find_all('a',
                                                                                                                   attrs={
                                                                                                                       'data-heap-id': 'citation_title'})]

    def get_reference_titles(self):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@id="cited-papers"]')))
        return [paper.find('h3').text for paper in
                BeautifulSoup(self.driver.page_source, 'html.parser').find('div', {'id': 'cited-papers'}).find_all('a',
                                                                                                                   attrs={
                                                                                                                       'data-heap-id': 'citation_title'})]

    def get_authors(self):
        try:
            button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH,
                                                                                      '//button[@data-test-id="author-list-expand" and @aria-expanded="false"]')))
            actions = ActionChains(self.driver)
            actions.move_to_element(button).perform()
            button.click()
        except:
            pass
        results = BeautifulSoup(self.driver.page_source, 'html.parser').find_all('span',
                                                                                 attrs={
                                                                                     'data-heap-id': 'heap_author_list_item',
                                                                                     'data-test-id': 'author-list'})
        return [result.find('a').find('span').find('span').text for result in results if result.find('a')]

    def get_related_topics(self):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@data-test-id="related-papers-list"]')))
        return ', '.join([t.find(string=True, recursive=False) for t in
                          BeautifulSoup(self.driver.page_source, 'html.parser').find_all('a', attrs={
                              'data-test-id': re.compile(r'topic-\d+')})])

    def scroll_down(self, url):
        self.driver.get(url)
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(1)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def get_id(self):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//li[@data-test-id="corpus-id"]')))
        return \
            BeautifulSoup(self.driver.page_source, 'html.parser').find('li',
                                                                       attrs={'data-test-id': 'corpus-id'}).text.split(
                ': ')[1]

    def get_title(self):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//h1[@data-test-id="paper-detail-title"]')))
        return BeautifulSoup(self.driver.page_source, 'html.parser').find('h1',
                                                                          attrs={
                                                                              'data-test-id': 'paper-detail-title'}).text

    def get_publication_year(self):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//span[@data-test-id="paper-year"]')))
        return \
        BeautifulSoup(self.driver.page_source, 'html.parser').find('span', attrs={'data-test-id': 'paper-year'}).find(
            'span').find('span').text.split(' ')[-1]

    def return_or_none(self, function, val):
        try:
            return function()
        except Exception as e:
            return val

    def get_citation_count(self):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//a[@data-heap-nav="citing-papers"]')))
        return \
            BeautifulSoup(self.driver.page_source, 'html.parser').find('a',
                                                                       attrs={'data-heap-nav': 'citing-papers'}).find(
                'span').text.split(' ')[0]

    def get_references_count(self):
        try:
            return int(
                self.driver.find_element(By.CSS_SELECTOR, 'a[data-heap-nav="cited-papers"]').text.split()[
                    0].strip().replace(
                    ',',
                    ''))
        except:
            return None

    def extract(self):
        return {
            'id': self.return_or_none(self.get_id, ''),
            'title': self.return_or_none(self.get_title, ''),
            'abstract': self.return_or_none(self.get_abstract, ''),
            'publication year': self.return_or_none(self.get_publication_year, ''),
            'authors': self.return_or_none(self.get_authors, []),
            'related topics': self.return_or_none(self.get_related_topics, ''),
            'citation count': self.return_or_none(self.get_citation_count, ''),
            'reference count': self.return_or_none(self.get_references_count, ''),
            'references': self.return_or_none(self.get_reference_titles, '')
        }

    def start_crawling(self):
        professors = ['Soleymani']
        with open('crawled_paper.txt', 'r') as f:
            total_papers = json.loads(f.read())

        for professor in professors:
            queue = []
            with open(f"{professor}.txt", 'r') as f:
                queue += [link.strip() for link in f.readlines()]
            papers = []
            for k in range(200):
                print(k)
                sleep(0.5)
                try:
                    self.scroll_down(queue[0])
                    references = self.return_or_none(self.get_references, [])
                    queue += references
                    papers.append(self.extract())
                    total_papers.append(papers[-1])
                    queue = queue[1:]
                except Exception as e:
                    traceback.format_exc()
                dump(papers, open(f'crawled_paper_{professor}.txt', 'w'))
                dump(total_papers, open(f'crawled_paper.txt', 'w'))
                dump(queue, open('last_queue.txt', 'w'))


crawler = PaperCrawler()
crawler.start_crawling()
