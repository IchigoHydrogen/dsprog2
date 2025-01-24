import requests
from bs4 import BeautifulSoup
import time
import logging
import csv
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from urllib.parse import urljoin

Base = declarative_base()

class Company(Base):
   __tablename__ = 'companies'
   
   id = Column(Integer, primary_key=True)
   name = Column(String(255), nullable=False)
   created_at = Column(DateTime, default=datetime.now)
   updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
   jobs = relationship("Job", back_populates="company")

class JobCategory(Base):
   __tablename__ = 'job_categories'
   
   id = Column(Integer, primary_key=True)
   name = Column(String(50), nullable=False)
   created_at = Column(DateTime, default=datetime.now)
   jobs = relationship("Job", back_populates="category")

class Job(Base):
   __tablename__ = 'jobs'
   
   id = Column(Integer, primary_key=True)
   company_id = Column(Integer, ForeignKey('companies.id'))
   category_id = Column(Integer, ForeignKey('job_categories.id'))
   rank = Column(Integer)
   title = Column(String(500))
   url = Column(String(500))
   employment_type = Column(String(100))
   salary_summary = Column(String(200))
   location_summary = Column(String(500))
   page_title = Column(Text)
   job_content = Column(Text)
   company_profile = Column(Text)
   company_info = Column(Text)
   application_process = Column(Text)
   other_occupations = Column(Text)
   search_index = Column(Text)
   created_at = Column(DateTime, default=datetime.now)
   updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
   
   company = relationship("Company", back_populates="jobs")
   category = relationship("JobCategory", back_populates="jobs")

@dataclass
class RankingPage:
   name: str
   url: str

class TypeJpScraper:
   RANKING_PAGES = [
       RankingPage("総合", "https://type.jp/rank/"),
       RankingPage("開発", "https://type.jp/rank/development/"),
       RankingPage("PM", "https://type.jp/rank/pm/"),
       RankingPage("インフラ", "https://type.jp/rank/infrastructure/"),
       RankingPage("エンジニア", "https://type.jp/rank/engineer/"),
       RankingPage("営業", "https://type.jp/rank/sales/"),
       RankingPage("サービス", "https://type.jp/rank/service/"),
       RankingPage("オフィス", "https://type.jp/rank/office/"),
       RankingPage("その他", "https://type.jp/rank/others/"),
   ]
   
   BASE_URL = "https://type.jp"

   def __init__(self, db_url: str = 'sqlite:///type_jp_jobs.db'):
       self.engine = create_engine(db_url)
       Base.metadata.create_all(self.engine)
       self.Session = sessionmaker(bind=self.engine)
       
       self.headers = {
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
       }
       self.setup_logging()

   def setup_logging(self):
       logging.basicConfig(
           level=logging.INFO,
           format='%(asctime)s - %(levelname)s - %(message)s'
       )
       self.logger = logging.getLogger(__name__)

   def fetch_page(self, url: str) -> Optional[str]:
       try:
           response = requests.get(url, headers=self.headers)
           response.raise_for_status()
           return response.text
       except requests.RequestException as e:
           self.logger.error(f"ページ取得エラー ({url}): {e}")
           return None

   def extract_section_content(self, section) -> str:
       if not section:
           return ""
       return " ".join(section.stripped_strings)

   def extract_detail_info(self, detail_url: str) -> Dict:
       content = self.fetch_page(detail_url)
       if not content:
           return {}
       
       soup = BeautifulSoup(content, 'html.parser')
       detail_info = {}

       main_area = soup.find('main')
       if main_area:
           header = main_area.find('header', class_='mod-page-title')
           detail_info['page_title'] = self.extract_section_content(header)

           job_content = main_area.find('section', class_='bosyuarea')
           detail_info['job_content'] = self.extract_section_content(job_content)

           company_profile = main_area.find('section', class_='sugaoarea')
           detail_info['company_profile'] = self.extract_section_content(company_profile)

           company_info = main_area.find('section', class_='kigyogaiyo')
           detail_info['company_info'] = self.extract_section_content(company_info)

           application_process = main_area.find('section', class_='aboutoubo')
           detail_info['application_process'] = self.extract_section_content(application_process)

           other_occupations = main_area.find('section', class_='mod-other-occupation')
           detail_info['other_occupations'] = self.extract_section_content(other_occupations)

           search_indices = main_area.find_all('section', class_='mod-search-index')
           detail_info['search_index'] = " | ".join([self.extract_section_content(idx) for idx in search_indices])

       time.sleep(3)
       return detail_info

   def process_ranking_page(self, ranking_page: RankingPage, session):
       content = self.fetch_page(ranking_page.url)
       if not content:
           return
       
       soup = BeautifulSoup(content, 'html.parser')
       articles = soup.select('#main-area section.job-list.left-column article')
       
       category = session.query(JobCategory).filter_by(name=ranking_page.name).first()
       if not category:
           category = JobCategory(name=ranking_page.name)
           session.add(category)
           session.commit()

       for article in articles:
           try:
               company_name = article.select_one('h3.company span').text.strip()
               company = session.query(Company).filter_by(name=company_name).first()
               if not company:
                   company = Company(name=company_name)
                   session.add(company)
                   session.commit()

               title_link = article.select_one('h4.title a')
               detail_url = urljoin(self.BASE_URL, title_link['href']) if title_link else ''
               
               rank_text = article.select_one('.rank-ribbon').text.strip()
               rank = int(rank_text) if rank_text.isdigit() else None
               
               job = Job(
                   company_id=company.id,
                   category_id=category.id,
                   rank=rank,
                   title=title_link.text.strip() if title_link else '',
                   url=detail_url,
                   employment_type=', '.join([ribbon.text.strip() 
                                           for ribbon in article.select('.icon.ribbon.black')]),
                   salary_summary=article.select_one('.salary').text.strip() if article.select_one('.salary') else '',
                   location_summary=article.select_one('.place').text.strip() if article.select_one('.place') else ''
               )

               if detail_url:
                   self.logger.info(f"詳細情報を取得中: {detail_url}")
                   detail_info = self.extract_detail_info(detail_url)
                   for key, value in detail_info.items():
                       setattr(job, key, value)

               session.add(job)
               session.commit()
               
           except Exception as e:
               self.logger.error(f"求人情報の処理エラー: {e}")
               session.rollback()
               continue

   def scrape_all_rankings(self):
       session = self.Session()
       try:
           for ranking_page in self.RANKING_PAGES:
               self.logger.info(f"{ranking_page.name}ランキングの取得を開始します...")
               self.process_ranking_page(ranking_page, session)
               time.sleep(3)
       finally:
           session.close()

def main():
   scraper = TypeJpScraper()
   scraper.scrape_all_rankings()

if __name__ == "__main__":
   main()