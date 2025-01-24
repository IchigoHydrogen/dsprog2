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
    job_description = Column(Text)
    requirements = Column(Text)
    salary_detail = Column(Text)
    benefits = Column(Text)
    work_location = Column(Text)
    working_hours = Column(Text)
    page_title = Column(Text)
    local_nav = Column(Text)
    main_article = Column(Text)
    job_content = Column(Text)
    button_holder = Column(Text)
    company_profile = Column(Text)
    company_info = Column(Text)
    application_process = Column(Text)
    other_occupations = Column(Text)
    recommendations = Column(Text)
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

        # メインエリアの取得
        main_area = soup.find('main')
        if main_area:
            # ページタイトル
            header = main_area.find('header', class_='mod-page-title')
            detail_info['page_title'] = self.extract_section_content(header)

            # ローカルナビゲーション
            nav = main_area.find('nav', class_='detail-local-nav')
            detail_info['local_nav'] = self.extract_section_content(nav)

            # メイン記事エリア
            main_article = main_area.find('section', class_='main_kiji_area')
            detail_info['main_article'] = self.extract_section_content(main_article)

            # 募集エリア
            job_content = main_area.find('section', class_='bosyuarea')
            detail_info['job_content'] = self.extract_section_content(job_content)

            # ボタンホルダー
            button_holders = main_area.find_all('section', class_='mod-button-holder')
            detail_info['button_holder'] = " | ".join([self.extract_section_content(holder) for holder in button_holders])

            # 企業プロフィール
            company_profile = main_area.find('section', class_='sugaoarea')
            detail_info['company_profile'] = self.extract_section_content(company_profile)

            # 企業情報
            company_info = main_area.find('section', class_='kigyogaiyo')
            detail_info['company_info'] = self.extract_section_content(company_info)

            # 応募プロセス
            application_process = main_area.find('section', class_='aboutoubo')
            detail_info['application_process'] = self.extract_section_content(application_process)

            # その他の職種
            other_occupations = main_area.find('section', class_='mod-other-occupation')
            detail_info['other_occupations'] = self.extract_section_content(other_occupations)

            # おすすめ情報
            recommendations = main_area.find_all('section', class_='mod-recommend')
            detail_info['recommendations'] = " | ".join([self.extract_section_content(rec) for rec in recommendations])

            # 検索インデックス
            search_indices = main_area.find_all('section', class_='mod-search-index')
            detail_info['search_index'] = " | ".join([self.extract_section_content(idx) for idx in search_indices])

        # 既存の詳細情報の取得も維持
        sections = {
            'job_description': 'uq-detail-jobdescription',
            'requirements': 'uq-detail-requirements',
            'salary_detail': 'uq-detail-salary',
            'working_hours': 'uq-detail-workinghours',
            'benefits': 'uq-detail-benefits',
            'work_location': 'uq-detail-location'
        }

        for key, class_name in sections.items():
            section = soup.find('section', class_=class_name)
            if section:
                content_div = section.find('div', class_='box')
                detail_info[key] = self.extract_section_content(content_div if content_div else section)
            else:
                detail_info[key] = ''

        return detail_info

    def save_to_csv(self, job_data: Dict, filename: str = 'job_detail.csv'):
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Field', 'Content'])
            for key, value in job_data.items():
                writer.writerow([key, value])
        print(f"\nData saved to {filename}")

    def process_single_job(self, detail_url: str):
        detail_info = self.extract_detail_info(detail_url)
        self.save_to_csv(detail_info)
        return detail_info

def main():
    scraper = TypeJpScraper()
    test_url = "https://type.jp/job-11/1343474_detail/?pathway=39"
    scraper.process_single_job(test_url)

if __name__ == "__main__":
    main()