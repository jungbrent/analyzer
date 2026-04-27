from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import trafilatura
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
        res = requests.get(data.url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        html = res.text

        soup = BeautifulSoup(html, "html.parser")

        iframe = soup.find("iframe", id="mainFrame")
        if iframe and iframe.get("src"):
            iframe_url = urljoin(data.url, iframe["src"])
            res = requests.get(iframe_url, headers=HEADERS, timeout=10)
            res.raise_for_status()
            html = res.text
            soup = BeautifulSoup(html, "html.parser")

        text = trafilatura.extract(html) or ""
        visible_text = soup.get_text(" ", strip=True)

        image_count = len(soup.find_all("img"))
        link_count = len(soup.find_all("a"))

        title = soup.title.string.strip() if soup.title else ""

        h1_count = len(soup.find_all("h1"))
        h2_count = len(soup.find_all("h2"))
        h3_count = len(soup.find_all("h3"))

        char_count = len(text)
        char_no_space = len(text.replace(" ", ""))

        words = re.findall(r'\\w+', text.lower())
        word_count = len(words)

        keyword_count_body = 0
        keyword_count_page = 0

        if data.keyword:
            pattern = rf'\\b{re.escape(data.keyword.lower())}\\b'
            keyword_count_body = len(re.findall(pattern, text.lower()))
            keyword_count_page = len(re.findall(pattern, visible_text.lower()))

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
            "preview": text[:300]
        }

    except Exception as e:
        return {"error": str(e)}
