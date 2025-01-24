import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scraping_ranking import Company, JobCategory, Job

def export_to_csv():
    engine = create_engine('sqlite:///type_jp_jobs.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        with open('jobs.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 修正後のヘッダー
            headers = [
                'job_id', 'company_name', 'category_name', 'rank',
                'title', 'url', 'employment_type', 'salary_summary',
                'location_summary', 'page_title', 'job_content', 
                'company_profile', 'company_info', 'application_process',
                'other_occupations', 'search_index', 'created_at', 
                'updated_at'
            ]
            writer.writerow(headers)
            
            jobs = session.query(Job).all()
            
            for job in jobs:
                company = session.query(Company).filter_by(id=job.company_id).first()
                category = session.query(JobCategory).filter_by(id=job.category_id).first()
                
                row = [
                    job.id,
                    company.name if company else '',
                    category.name if category else '',
                    job.rank,
                    job.title,
                    job.url,
                    job.employment_type,
                    job.salary_summary,
                    job.location_summary,
                    job.page_title,
                    job.job_content,
                    job.company_profile,
                    job.company_info,
                    job.application_process,
                    job.other_occupations,
                    job.search_index,
                    job.created_at,
                    job.updated_at
                ]
                writer.writerow(row)
        
        print("CSVファイルの出力が完了しました。")
        
        job_count = session.query(Job).count()
        print(f"出力した求人数: {job_count}")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    
    finally:
        session.close()

if __name__ == "__main__":
    export_to_csv()