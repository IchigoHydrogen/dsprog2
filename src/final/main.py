import re
import csv
import time
import requests
from bs4 import BeautifulSoup

def scrape_and_save_to_csv(base_url, csv_filename, max_pages=50):
    """
    base_url: 
        ページ番号以外の共通部分。末尾に「?pageNo={page}」を付与して利用します。
        
    csv_filename: 
        CSV出力のファイル名。
        
    max_pages:
        安全のための最大ページ数。デフォルトは50ですが、必要に応じて増減してください。
    """
    
    results = []
    
    # 正規表現パターン: "1600" の直後に4桁の数字が続くか → "1600" に置換
    pattern_remove_1600 = re.compile(r'1600\d{4}')
    
    for page_no in range(1, max_pages+1):
        # ページURL生成
        url = f"{base_url}?pageNo={page_no}"
        
        print(f"Fetching page: {url}")
        
        # リクエスト 前に3秒待機
        time.sleep(3)
        
        # ページ取得
        response = requests.get(url)
        # エラーなどでページが存在しない場合はそこで終了
        if response.status_code != 200:
            print(f"Page {page_no} not found (status: {response.status_code}). Stop.")
            break
        
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # カード単位で求人情報を取得（構造によって変更してください）
        # 例: "section.jobOfferCard" など、実際のHTMLを確認して適宜変更。
        # 以下は汎用的に "section" を全部取ってきて、その中に会社名・時給があるかを探す例。
        cards = soup.find_all("section")
        
        # フラグ: 1ページ分のcardが0件 または 有効なcardが何もない → 次のページ無さそうなら終了
        valid_card_found = False  
        
        for card in cards:
            # 会社名を取得
            company_name_elem = card.select_one("div.shopNameWrap > h2")
            if not company_name_elem:
                continue
            company_name = company_name_elem.get_text(strip=True)
            
            # 時給を取得
            wage_elem = card.select_one("li.baseInformationSet.wage > div.baseInformationFirstContent")
            if not wage_elem:
                continue
            
            wage_text_original = wage_elem.get_text(strip=True)
            
            # "1600" のあとに4桁の数字 → "1600" に置換
            wage_text_fixed = re.sub(pattern_remove_1600, '1600', wage_text_original)
            
            # 数値抽出
            # 例: "時給1600～2000円" → ['1600','2000']
            # 最初の数字を最低時給とする
            nums = re.findall(r'\d+', wage_text_fixed)
            if not nums:
                continue
            
            min_wage = int(nums[0])  # 最初の数字を最低時給とみなす
            
            # 3桁以下(例: 100 ~ 999以下)は無視する
            if min_wage < 1000:
                # 例: 900とか700は日当表記などの可能性があるのでスキップ
                continue
            
            # ここまでこれたら有効データ
            valid_card_found = True
            
            results.append({
                "company_name": company_name,
                "wage_info": min_wage
            })
        
        # 有効なカードが0件の場合は「次のページはない」と判断して終了してもよい
        # ただし、中には他のページがまだある場合もあるので、判断が難しい場合は
        # ここでは card が見つからなくても break はしないことにします。
        # もし、次ページでは求人が本当にない、かつ 404 にもならないケースがあれば
        # 追加で条件を入れる必要があります。
        if not valid_card_found:
            print(f"No valid job found on page {page_no}. Stop.")
            break
    
    # すべてのページを取得後、CSV出力
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["company_name", "wage_info"])
        writer.writeheader()
        writer.writerows(results)
    
    # コンソールにも出力確認
    for row in results:
        print(f"{row['company_name']},{row['wage_info']}")


if __name__ == "__main__":
    # base_url は「?pageNo=」より前の部分
    # 例: "https://baito.mynavi.jp/tokyo/city-34/kd-11_3101/"
    base_url = "https://baito.mynavi.jp/tokyo/city-34/kd-11_3101/"
    csv_filename = "wage_info.csv"
    
    scrape_and_save_to_csv(base_url, csv_filename)
    print("==== CSV出力が完了しました ====")