from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import webbrowser
import os
import re
from datetime import datetime

def clean_announcement_title(text):
    """지저분한 텍스트에서 핵심 공고 제목만 추출하는 함수"""
    # 1. 불필요한 접두어/접미어 제거
    text = re.sub(r'IRIS 공고|접수중|접수마감|접수예정|D-\d+', '', text)
    # 2. 접수기간 및 날짜 형식 제거 (2026-00-00 등)
    text = re.sub(r'\d{4}-\d{2}-\d{2}.*', '', text)
    # 3. 번호(숫자만 있는 경우) 제거
    text = re.sub(r'^\d+$', '', text)
    return text.strip()

def get_refined_integrated_report():
    print(f"🚀 [정밀 정제 스캐너] 공고별로 깔끔하게 구분하여 수집을 시작합니다...")
    
    target_sites = {
        "KEIT(산업기술)": "https://srome.keit.re.kr/srome/biz/perform/opnnPrpsl/retrieveTaskAnncmListView.do?prgmId=XPG201040000&rcveStatus=A",
        "NTIS(종합)": "https://www.ntis.go.kr/rndgate/eg/un/ra/mng.do",
        "SMTECH(중기부)": "https://www.smtech.go.kr/front/ifg/no/notice02_list.do",
        "KATECH(자동차연)": "https://www.katech.re.kr/page/1b9d4cae-2708-4290-8638-d1133afb6c5a",
        "MOTIR(전략기획단)": "https://www.motir.go.kr/kor/article/ATCLc01b2801b"
    }

    target_keywords = ['자동차', '자동차부품', '2차전지', '배터리', '로봇', 'R&D']

    options = Options()
    options.add_argument("--headless")
    options.add_argument("window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    total_data = []

    try:
        for name, url in target_sites.items():
            print(f"🔎 {name} 정밀 스캔 중...")
            driver.get(url)
            time.sleep(8) 

            # KEIT 같은 사이트는 주로 <a> 태그나 특정 클래스에 제목이 몰려있음
            # 모든 요소를 보되, '제목' 역할을 하는 요소 위주로 수집
            elements = driver.find_elements(By.XPATH, "//a | //td[contains(@class, 'left')] | //p[contains(@class, 'tit')]")
            
            for el in elements:
                raw_text = el.text.strip()
                if not raw_text: continue
                
                # 핵심 제목만 정제
                title = clean_announcement_title(raw_text)
                
                # 필터링: 키워드 포함 + 너무 짧거나 긴 노이즈 제거
                if any(kw in title for kw in target_keywords) and 10 < len(title) < 150:
                    if not any(d['title'] == title for d in total_data):
                        total_data.append({'site': name, 'title': title, 'url': url})

        # --- HTML 리포트 생성 (가독성 극대화) ---
        if total_data:
            report_name = "refined_report.html"
            with open(report_name, "w", encoding="utf-8") as f:
                f.write(f"""
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: 'Segoe UI', 'Malgun Gothic', sans-serif; background: #f0f4f8; padding: 20px; }}
                        .card {{ background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); padding: 20px; max-width: 1000px; margin: auto; }}
                        h2 {{ color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 10px; }}
                        .item {{ border-bottom: 1px solid #e5e7eb; padding: 15px 0; display: flex; align-items: center; }}
                        .item:last-child {{ border-bottom: none; }}
                        .badge {{ min-width: 120px; padding: 5px 10px; border-radius: 5px; font-size: 0.8em; font-weight: bold; text-align: center; margin-right: 20px; }}
                        .KEIT {{ background: #dcfce7; color: #166534; }}
                        .NTIS {{ background: #fee2e2; color: #991b1b; }}
                        .SMTECH {{ background: #fef9c3; color: #854d0e; }}
                        .KATECH {{ background: #e0f2fe; color: #075985; }}
                        .MOTIR {{ background: #f3e8ff; color: #6b21a8; }}
                        .title-link {{ text-decoration: none; color: #1f2937; font-weight: 600; flex-grow: 1; }}
                        .title-link:hover {{ color: #2563eb; text-decoration: underline; }}
                        .keyword-tag {{ color: #3b82f6; font-size: 0.85em; margin-right: 5px; }}
                    </style>
                </head>
                <body>
                    <div class="card">
                        <h2>📋 기업 핵심 전략과제 통합 리포트 ({datetime.now().strftime('%Y-%m-%d')})</h2>
                        <p style="font-size: 0.9em; color: #6b7280;">수집 키워드: 자동차, 2차전지, 배터리, 로봇, R&D</p>
                """)
                
                for d in total_data:
                    site_key = d['site'].split('(')[0] # KEIT, NTIS 등 이름만 추출
                    f.write(f"""
                        <div class="item">
                            <span class="badge {site_key}">{d['site']}</span>
                            <a href="{d['url']}" class="title-link" target="_blank">{d['title']}</a>
                            <span style="font-size: 0.8em; color: #9ca3af;">{datetime.now().strftime('%m-%d')}</span>
                        </div>
                    """)
                
                f.write("</div></body></html>")
            
            webbrowser.open("file://" + os.path.abspath(report_name))
            print(f"✨ 정밀 수집 완료! 총 {len(total_data)}건의 공고를 구분하여 출력했습니다.")
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    get_refined_integrated_report()