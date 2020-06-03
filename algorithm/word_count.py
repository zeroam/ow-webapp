from collections import Counter

import requests
from bs4 import BeautifulSoup
from konlpy.tag import Okt


def get_nouns(text):
    h = Okt()

    nouns = h.nouns(text)
    count = Counter(nouns)
    print(count)


def main():
    resp = requests.get("https://www.donga.com/news/article/all/20200603/101350076/1")
    soup = BeautifulSoup(resp.text, "lxml")
    get_nouns(soup.text)


if __name__ == "__main__":
    main()
