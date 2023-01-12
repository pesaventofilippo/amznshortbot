from hashlib import sha256
from urllib.parse import urlencode, urlparse, parse_qs

class URL:
    def __init__(self, url: str):
        if ("https://" not in url) and ("http://" not in url):
            url = "http://" + url
        self.url = url

    @property
    def isBitlyUrl(self) -> bool:
        prefixList = [
            "http://amzn.to",
            "https://amzn.to",
            "amzn.to"
        ]
        return self.url.startswith(tuple(prefixList))

    @property
    def isAmazonUrl(self) -> bool:
        prefixList = [
            "http://www.amazon.",
            "https://www.amazon.",
            "http://amazon.",
            "https://amazon.",
            "www.amazon.",
            "amazon."
        ]
        return self.url.startswith(tuple(prefixList))

    def removeTags(self, tags: list):
        u = urlparse(self.url)
        query = parse_qs(u.query, keep_blank_values=True)
        for tag in tags:
            query.pop(tag, None)
        u = u._replace(query=urlencode(query, True))
        self.url = u.geturl()

    def clean(self):
        tags = ["ref", "tag", "linkId", "keywords", "qid", "s", "ascsubtag"]
        self.removeTags(tags)

    def applyReferral(self, referral: str):
        self.clean()
        separator = "&" if "?" in self.url > 0 else "?"
        self.url += f"{separator}tag={referral}"

    def sha256(self) -> str:
        return sha256(self.url.encode()).hexdigest()

    def __str__(self):
        return self.url
