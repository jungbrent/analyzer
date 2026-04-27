from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import re
from collections import Counter
from urllib.parse import urljoin

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestData(BaseModel):
    url: str
    keyword: str = ""

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

@app.get("/")
def root():
    return {"message": "Blog Analyzer API Running"}

@app.post("/analyze")
def analyze(data: RequestData):
    try:
        # URL 요청
        res = requests.get(data.url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        html = res.text

        soup = BeautifulSoup(html, "html.parser")

        # 네이버 블로그 iframe 처리
        iframe = soup.find("iframe", id="mainFrame")
        if iframe and iframe.get("src"):
            iframe_url = urljoin(data.url, iframe["src"])
            res = requests.get(iframe_url, headers=HEADERS, timeout=10)
            res.raise_for_status()
            html = res.text
            soup = BeautifulSoup(html, "html.parser")

        # 본문 추출 (메모장 기준과 최대한 유사)
        text = soup.get_text(" ", strip=True)

        # 전체 페이지 텍스트
        visible_text = text

        # 이미지 개수
        image_count = len(soup.find_all("img"))

        # 링크 개수
        link_count = len(soup.find_all("a"))

        # 제목
        title = soup.title.string.strip() if soup.title else ""

        # 헤딩 태그 개수
        h1_count = len(soup.find_all("h1"))
        h2_count = len(soup.find_all("h2"))
        h3_count = len(soup.find_all("h3"))

        # 글자수
        char_count = len(text)
        char_no_space = len(text.replace(" ", ""))

        # 단어 수
        words = re.findall(r'\w+', text.lower())
        word_count = len(words)

        # 키워드 카운트
        keyword_count_body = 0
        keyword_count_page = 0

        if data.keyword:
            keyword = data.keyword.lower().strip()
            keyword_count_body = text.lower().count(keyword)
            keyword_count_page = visible_text.lower().count(keyword)

        # 상위 단어
        common_words = Counter(words).most_common(10)

        return {
            "title": title,
            "char_count": char_count,
            "char_no_space": char_no_space,
            "word_count": word_count,
            "image_count": image_count,
            "link_count": link_count,
            "h1_count": h1_count,
            "h2_count": h2_count,
            "h3_count": h3_count,
            "keyword_count_body": keyword_count_body,
            "keyword_count_page": keyword_count_page,
            "common_words": common_words,
            "preview": text[:500]
        }

    except Exception as e:
        return {"error": str(e)}
