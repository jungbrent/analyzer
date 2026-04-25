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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
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

        image_count = len(soup.find_all("img"))
        link_count = len(soup.find_all("a"))

        title = soup.title.string.strip() if soup.title else ""

        h1_count = len(soup.find_all("h1"))
        h2_count = len(soup.find_all("h2"))
        h3_count = len(soup.find_all("h3"))

        char_count = len(text)
        char_no_space = len(text.replace(" ", ""))

        words = re.findall(r'\w+', text.lower())
        word_count = len(words)

        keyword_count = text.lower().count(data.keyword.lower()) if data.keyword else 0

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
            "keyword_count": keyword_count,
            "common_words": common_words,
            "preview": text[:300]
        }

    except Exception as e:
        return {"error": str(e)}
