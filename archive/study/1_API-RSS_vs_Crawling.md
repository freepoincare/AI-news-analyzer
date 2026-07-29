# 파이썬으로 뉴스 데이터를 수집하는 가장 효율적인 방법

Prompt: 
```
외부 뉴스 API(또는 RSS)와 크롤링으로 뉴스 데이터를 수집하는 방법을 파이썬으로 알려주세용.
```

파이썬으로 뉴스 데이터를 수집하는 가장 효율적인 방법은 무료 뉴스 API(또는 RSS 피드)를 우선 활용하고, 데이터가 부족할 때 BeautifulSoup이나 Selenium으로 웹 크롤링을 결합하는 것입니다.
각 방식의 구현 방법과 샘플 코드를 정리해 드립니다.

---

## 1. 뉴스 API 활용하기 (가장 추천)

외부 뉴스 API를 사용하면 구조화된 JSON 데이터를 가장 빠르고 안정적으로 가져올 수 있습니다. 대표적인 무료 API인 [NewsAPI](https://newsapi.org/)를 활용한 예시입니다.

```python
import requests
def get_news_via_api(query):
    # 발급받은 본인의 API Key 입력
    api_key = "YOUR_NEWS_API_KEY" 
    url = f"https://newsapi.org{query}&apiKey={api_key}&language=ko"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        articles = data.get("articles", [])
        
        for idx, article in enumerate(articles[:5], 1):
            print(f"[{idx}] {article['title']}")
            print(f"출처: {article['source']['name']} | 링크: {article['url']}\n")
    else:
        print("API 요청 실패:", response.status_code)
# '인공지능' 관련 뉴스 5개 출력
get_news_via_api("인공지능")
```

---

## 2. RSS 피드 수집하기

언론사나 포털(예: 구글 뉴스)에서 제공하는 RSS 주소를 이용하면 feedparser 라이브러리로 쉽게 데이터를 파싱할 수 있습니다.

* 설치: `pip install feedparser`

```python
import feedparser

def get_news_via_rss():
    # 구글 뉴스 RSS (키워드: 인공지능)
    rss_url = "https://google.com"
    
    feed = feedparser.parse(rss_url)
    
    for idx, entry in enumerate(feed.entries[:5], 1):
        print(f"[{idx}] {entry.title}")
        print(f"발행일: {entry.published} | 링크: {entry.link}\n")

get_news_via_rss()
```

---

## 3. 웹 크롤링 (정적 페이지 - BeautifulSoup)

API나 RSS가 없을 때는 `requests`와 `BeautifulSoup`을 사용해 뉴스 페이지의 HTML을 직접 긁어옵니다. 네이버 뉴스 검색 결과를 예시로 든 코드입니다.

* 설치: `pip install requests beautifulsoup4`

```python
import requests
from bs4 import BeautifulSoup

def crawl_naver_news(query):
    url = f"https://naver.com{query}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 네이버 뉴스 검색 결과의 제목 element 선택 (선택자는 사이트 변경에 따라 바뀔 수 있음)
    news_titles = soup.select("a.news_tit")
    
    for idx, title in enumerate(news_titles[:5], 1):
        news_name = title.text
        news_url = title["href"]
        print(f"[{idx}] {news_name}")
        print(f"링크: {news_url}\n")

crawl_naver_news("인공지능")
```

---

## 4. 웹 크롤링 (동적 페이지 - Selenium)

페이지를 아래로 스크롤해야 뉴스 리스트가 추가되거나, 자바스크립트로 로딩되는 사이트는 Selenium을 사용해야 합니다. 

* 설치: `pip install selenium`

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def crawl_dynamic_news():
    # 웹드라이버 실행 (최신 셀레니움은 크롬드라이버 자동 관리)
    driver = webdriver.Chrome()
    
    # 예시: 특정 동적 로딩 뉴스 페이지 이동
    driver.get("https://naver.com")
    time.sleep(2) # 페이지 로딩 대기
    
    # 스크롤을 아래로 내리는 예시
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
    
    # 헤드라인 뉴스 엘리먼트 가져오기
    headlines = driver.find_elements(By.CLASS_NAME, "cjs_t")
    
    for idx, headline in enumerate(headlines[:5], 1):
        print(f"[{idx}] {headline.text}")
        
    driver.quit()

crawl_dynamic_news()
```

---

## 💡 데이터 수집 시 주의할 점 (수집 에티켓)

* `robots.txt` 확인: 크롤링 전 해당 사이트 도메인 뒤에 `/robots.txt`를 붙여(예: `://naver.com`) 크롤링 허용 범위를 반드시 확인하세요.
* 요청 간격 지키기: 짧은 시간 내에 너무 많은 요청을 보내면 IP가 차단되거나 디도스(DDoS) 공격으로 오인받을 수 있습니다. 코드 중간에 `time.sleep(1)` 같은 휴식기를 꼭 넣어주세요.
* 저작권 유의: 수집한 뉴스 데이터를 상업적으로 이용하거나 본문을 그대로 재배포하면 저작권법 위반 소지가 있습니다. 개인 연구나 분석 용도로만 활용하는 것을 권장합니다.

## https://semiconductorpackagingnews.com/robots.txt

Result (example):
```
User-agent: *
Disallow: /test/
```

* `User-agent: *`

This target statement applies to all web crawlers and automated bots (like Googlebot, Bingbot, or AI scrapers). The asterisk (`*`) is a wildcard meaning "everyone."

* `Disallow: /test/`

This specifies the restriction. It tells all the bots that they are not allowed to crawl, index, or visit any URLs or folders that start with `/test/` (e.g., https://semiconductorpackagingnews.com).

## Why is it there?

Websites use a `robots.txt` file to manage web traffic and keep certain parts of their site private from search engines.

In this specific case, the website owner is likely hiding a staging, testing, or development folder (`/test/`) so that incomplete pages do not accidentally show up in public Google search results.

Since it only restricts `/test/`, all other public parts of the website are completely open for search engines to index.

Read: [What is robots.txt?](https://www.cloudflare.com/learning/bots/what-is-robots-txt/)


# API/RSS 방식 vs 웹 크롤링

API/RSS 방식과 웹 크롤링 방식은 데이터 수집의 안정성과 자유도 측면에서 명확한 차이가 있다.
가장 큰 차이는 "제공자가 공식적으로 열어둔 문을 통과하느냐(API/RSS), 내가 직접 집 안을 들여다보며 찾아내느냐(크롤링)"의 차이임.


## 1. API / RSS 방식의 핵심 특징

* 장점 (안정성과 속도): 언론사나 포털에서 규격화된 데이터(JSON, XML)를 공식 제공하므로 수집 속도가 매우 빠르고 에러가 거의 없음. 사이트 디자인이 바뀌어도 코드를 수정할 필요가 없음.
* 단점 (제한된 데이터): 제공해 주는 데이터(제목, 요약본, 링크 등) 외에 뉴스 본문 전체나 댓글 같은 상세 데이터는 가져올 수 없는 경우가 많음. 무료 이용 시 하루 요청 횟수 제한이 걸리기도 함.

## 2. 웹 크롤링 방식의 핵심 특징

* 장점 (높은 자유도): 화면에 보이는 모든 정보를 긁어올 수 있음. 뉴스 본문 전체는 물론, 기자 이름, 등록 시간, 댓글 수, 좋아요 수까지 원하는 모든 데이터를 수집 가능.
* 단점 (유지보수의 어려움과 차단 위험): 해당 뉴스 사이트의 레이아웃이나 HTML 태그가 조금만 바뀌어도 코드가 작동하지 않아 지속적으로 수정해야 함. 또한, 단시간에 많은 요청을 보내면 고의적인 공격으로 간주되어 IP가 차단될 수 있음.


## 📊 API/RSS vs 웹 크롤링 장단점 비교표

| 비교 항목 | API / RSS 방식 | 웹 크롤링 (BeautifulSoup / Selenium) |
|---|---|---|
| 데이터 수집 범위 | ⚠️ 제한됨 (제목, 요약, 링크 위주) | 🔗 무제한 (본문 전체, 댓글, 이미지 등 전체) |
| 수집 속도 | ⚡ 매우 빠름 (구조화된 데이터 즉시 다운로드) | 🐢 상대적으로 느림 (HTML 전체 로딩 및 해석 필요) |
| 구현 및 유지보수 | 🛠️ 매우 쉬움 (사이트가 바뀌어도 코드 유지 가능) | ⚙️ 어려움 (사이트 개편 시 크롤링 코드 재작성 필요) |
| 차단 및 제재 위험 | 🟢 안전함 (공식 제공 경로 이용) | 🔴 높음 (IP 차단 가능성, robots.txt 규정 준수 필요) |
| 비용 | 💰 부분 유료 (대량 수집 시 비용 발생 가능) | 🆓 무료 (컴퓨터 자원과 시간만 소요) |
| 추천 활용 상황 | 실시간 트렌드 파악, 대량의 뉴스 헤드라인 수집 | 특정 언론사 뉴스 본문 텍스트 마이닝, 댓글 감성 분석 |

---

# 원본 raw / 정제 clean 분리 저장

뉴스 데이터를 수집하여 원본(Raw)과 정제(Clean) 데이터로 분리 저장하는 아키텍처는 데이터 엔지니어링의 기본이자 가장 효율적인 방식이다.
네트워크 오류, 데이터 유실, 정제 로직 변경에 유연하게 대응하려면 아래와 같이 파이프라인을 구성해야 한다.


## 1. 데이터 저장소 전략: 투-트랙(Two-Track) 구성

원본과 정제 데이터는 데이터의 성격과 활용 목적이 완전히 다르므로 저장 공간을 분리해야 한다.

```
[수집: API/크롤러] ──> [Raw 스토리지 (기록용)] ──> [정제 로직] ──> [Clean 스토리지 (서비스용)]
```

* Raw 데이터 (데이터 레이크/Data Lake)
    * 목적: API 응답 및 크롤링한 HTML 원본을 가공 없이 그대로 백업 (추후 정제 로직이 바뀌면 다시 정제하기 위함)
    * 추천 저장소: Object Storage (AWS S3, Google Cloud Storage) 또는 MongoDB와 같은 NoSQL

* Clean 데이터 (데이터 웨어하우스/Data Warehouse)
    * 목적: 중복 제거, 텍스트 정제, 형태소 분석 등이 완료되어 실제 서비스나 AI 모델에 즉시 사용될 데이터
    * 추천 저장소: 관계형 데이터베이스(MySQL, PostgreSQL) 또는 검색 엔진(Elasticsearch)


## 2. 스키마 및 데이터 구조 설계

### 📂 Raw 데이터 저장 형식 (JSON 파일 또는 NoSQL 추천)

가장 중요한 점은 수집 시점의 메타데이터를 함께 기록하는 것이다.

```json
{
  "raw_id": "uuid_or_hash_value",
  "collected_at": "2026-07-29T19:20:00Z", 
  "source_type": "API",                 // API, RSS, CRAWLING 구분
  "source_name": "newsapi_org",         // 출처 이름
  "target_url": "https://news.com",     // 크롤링 대상인 경우 URL
  "payload": {                          // 서버에서 받은 응답 전체를 그대로 삽입
    "title": "...",
    "author": "...",
    "publishedAt": "2026-07-29T10:00:00Z",
    "content": "..." 
  }
}
```

### 📊 Clean 데이터 저장 형식 (RDBMS/Elasticsearch 스키마 예시)

정제 데이터는 구조화된 테이블 형태로 관리하며, 중복 방지를 위한 `Unique Key`가 필수이다.

```sql
CREATE TABLE clean_news (
    news_id VARCHAR(64) PRIMARY KEY,   -- 중복 방지용 고유 키 (예: URL의 SHA-256 해시값)
    raw_ref_id VARCHAR(64),            -- 원본 데이터 추적용 FK (Traceability)
    title VARCHAR(500) NOT NULL,       -- 기사 제목 (공백 및 특수문자 정제 완료)
    content TEXT NOT NULL,             -- 기사 본문 (HTML 태그, 광고 문구 제거 완료)
    summary TEXT,                      -- (선택) AI 요약본
    reporter VARCHAR(100),             -- 기자 이름 추출
    provider VARCHAR(100),             -- 언론사 이름 통합 표준화 (예: 'NYT', '조선일보')
    published_at TIMESTAMP,            -- 발행일 (UTC 또는 KST 표준 타임스존 통일)
    created_at TIMESTAMP DEFAULT NOW() -- 정제 및 저장된 시점
);
```

## 3. 분리 저장 핵심 프로세스 및 팁

* 중복 제거(De-duplication): 뉴스 API, RSS, 크롤링을 동시에 쓰면 같은 기사가 중복 수집된다. Clean 테이블 저장 시 target_url이나 제목+언론사를 해시(Hash)값으로 만들어 고유 ID로 지정하고, `INSERT IGNORE` 또는 `ON DUPLICATE KEY UPDATE`를 사용해 중복을 원천 차단해야 함.
* 멱등성(Idempotency) 유지: 정제 프로그램이 도중에 멈춰서 재실행하더라도 데이터가 두 번 쌓이지 않고 항상 같은 상태를 유지하도록 로직을 설계해야 함.
* 증분 수집 파이프라인:
    1. 수집기가 Raw에 데이터를 밀어 넣습니다.
    2. 배치(Batch) 프로그램이나 이벤트 트리거가 "Raw에는 있지만 Clean에는 아직 없는 데이터"만 가져와 정제 로직(HTML 태그 제거, 텍스트 파싱 등)을 거친 후 Clean에 적재합니다.

---

현재 구상 중인 시스템의 데이터 규모나 인프라 환경(로컬 PC 환경, AWS 클라우드 등)을 결정하셨나요?
상황을 알려주시면 가장 가성비 좋은 오픈소스 기술 조합(예: Python + PostgreSQL + S3)을 구체적으로 매칭해 드리겠습니다.

---

## 🛠️ CLI 기반 뉴스 AI 파이프라인 추천 기술 조합

뉴스 데이터를 자동 수집, AI 요약, 시각화 후 리포트까지 출력하는 CLI 기반 파이프라인이라면 경량화, 빠른 개발 속도, 로컬 실행 편의성이 핵심이다.
아래는 CLI 환경에서 가장 안정적이고 효율적으로 동작하는 최적의 가성비 오픈소스 기술 조합이다.

| 단계 | 추천 기술 | 선택 이유 |
|---|---|---|
| 개발 언어 & CLI | Python + Typer | 데이터 처리에 가장 최적화된 언어이며, Typer를 사용하면 세련된 UI의 CLI 커맨드를 매우 쉽게 구현할 수 있음. |
| 데이터 수집 | Requests + BeautifulSoup4 | 뉴스 API(NewsAPI.org 등) 및 RSS 피드 파싱, 특정 언론사 HTML 본문 크롤링을 위한 가장 표준적이고 가벼운 조합임. |
| Raw 스토리지 | 로컬 파일 시스템 (JSONL) | 대규모 클라우드가 아닌 CLI 토이 프로젝트 수준에서는 날짜별 .jsonl (JSON Lines) 파일로 원본을 저장하는 것이 직관적이고 비용이 들지 않음. |
| Clean 스토리지 | SQLite | 파일 기반의 경량 관계형 데이터베이스로, 별도의 서버 설치 없이 Python 기본 라이브러리만으로 강력한 SQL 및 중복 제거 처리가 가능. |
| AI 요약 & 분석 | LangChain + OpenAI API (또는 Ollama) | LangChain을 활용해 뉴스 본문 요약 Prompt 체인을 쉽게 구성할 수 있으며, 비용 부담이 있다면 로컬 LLM(Ollama - Llama 3 등)을 엮어 완전 무료로 구성할 수도 있음. |
| 데이터 시각화 | Plotly (또는 Rich) | 터미널 안에서 텍스트 기반 차트를 그리려면 Rich 라이브러리를, 브라우저 팝업이나 이미지 파일(PNG)로 고품질 차트를 저장하려면 Plotly가 적합. |
| 리포트 생성 | Markdown / FPDF2 | CLI 서비스 특성상 분석 리포트를 깔끔한 Markdown(.md) 파일로 내보내거나, FPDF2 라이브러리를 이용해 규격화된 PDF 파일로 자동 생성하는 것이 가장 깔끔함. |

---

## 🔄 전체 데이터 파이프라인 흐름 (Flow)

구현하실 CLI 서비스는 다음과 같은 순차적 명령(Command) 구조로 설계하면 데이터 엔지니어링 흐름을 완벽히 경험할 수 있다.

```
[1. 수집] python app.py fetch  --> 외부 API/RSS 호출 -> Raw 스토리지(JSONL 파일) 저장
[2. 정제] python app.py clean  --> HTML 태그 제거, 중복 체크 -> Clean 스토리지(SQLite) 적재
[3. 분석] python app.py analyze --> 요약되지 않은 뉴스 추출 -> LLM API 연동 -> 요약문 및 키워드 업데이트
[4. 리포트] python app.py report --> 주제별 통계 시각화 및 리포트 파일(MD/PDF) 최종 발행
```

1. fetch 단계: API/RSS를 통해 가져온 JSON 응답 전체를 data/raw/2026-07-29.jsonl 형태의 파일에 그대로 기록한다.
2. clean 단계: Raw 파일을 읽어 제목과 본문의 특수문자·공백을 제거하고, 뉴스 URL의 해시값을 생성합니다. SQLite 데이터베이스에 INSERT OR IGNORE 명령을 사용하여 기사 중복을 완벽히 차단한다.
3. analyze 단계: SQLite에서 summary IS NULL인 상태의 정제된 본문을 가져와 LLM에 전달합니다. LLM이 반환한 핵심 요약과 카테고리(정치, 경제 등) 정보를 다시 DB에 업데이트(UPDATE)한다.
4. report 단계: DB에 쌓인 데이터를 기반으로 언론사별 비중, 주요 키워드 빈도수 등을 계산하여 차트 이미지로 저장하고, 요약문들을 모아 최종 리포트 파일을 생성한다.

---

이 파이프라인 구축을 시작하기 위해 첫 단계로 무엇을 먼저 프로토타이핑해보고 싶으신가요?

* 우선 뉴스 API와 크롤러를 연동하여 Raw 파일로 저장하는 수집부 스크립트부터 짜보시겠습니까?
* 아니면 수집된 데이터가 있다고 가정하고 LangChain을 이용해 LLM 뉴스 요약 프롬프트를 테스트해보시겠습니까?




## 💡 가장 이상적인 데이터 수집 전략

실무에서는 보통 두 방식을 섞어서 사용. API나 RSS를 통해 최신 뉴스 리스트와 URL 주소를 빠르게 수집한 뒤, 본문 내용이 꼭 필요한 뉴스만 해당 URL로 접속해 크롤링으로 본문을 긁어오는 방식이 가장 효율적이고 안전.

---

원하는 수집 목적에 맞춰서 개발을 진행해 보세요! 혹시 진행하시면서 아래 단계가 필요하신가요?

* 수집한 데이터를 판다스(Pandas) 데이터프레임으로 변환하고 엑셀 파일로 저장하는 코드
* 크롤링 차단을 피하기 위한 우회 기법(User-Agent 설정, 딜레이 부여) 적용 방법
