import os
from collections import Counter
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from konlpy.tag import Okt
from wordcloud import WordCloud

CUR_DIR = (Path(__file__).parent).absolute()
STATIC_DIR = CUR_DIR.parent / "static"
IMAGE_DIR = STATIC_DIR / "img"


def get_nouns(text: str, limit: int = 50) -> list:
    h = Okt()

    nouns = h.nouns(text)
    count = Counter(nouns)
    words = count.most_common(limit)

    return words


def create_wordcloud(words: dict, img_path: str):
    font_path = os.path.join(CUR_DIR, "malgun.ttf")
    word_cloud = WordCloud(font_path=font_path).generate_from_frequencies(words)
    word_cloud.to_file(img_path)


def word_counter(url: str, file_name: str) -> list:
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "lxml")
    words = get_nouns(soup.text, 50)

    img_path = os.path.join(IMAGE_DIR, file_name)
    if words:
        create_wordcloud(dict(words), img_path)

    result = dict()
    objects = []
    for word, count in words:
        objects.append({"word": word, "count": count})

    result["url_path"] = os.path.join("/static", "img", file_name)
    result["objects"] = objects

    return result


if __name__ == "__main__":
    url = "https://www.donga.com/news/article/all/20200603/101350076/1"
    word_counter(url, "wordcloud.png")
