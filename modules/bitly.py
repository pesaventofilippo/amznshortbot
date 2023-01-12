from requests import post
from requests.utils import requote_uri
from modules.url import URL

class BitlyApi:
    def __init__(self, apikey: str):
        self._apikey = apikey
        self._baseurl = "https://api-ssl.bitly.com/v4"

    def shortUrl(self, url: URL) -> URL:
        if ("https://" not in url.url) and ("http://" not in url.url):
            url.url = "http://" + url.url
        header = {
            "Authorization": self._apikey,
            "Content-Type": "application/json"
        }
        params = {
            "long_url": requote_uri(url.url)
        }
        try:
            response = post(f"{self._baseurl}/shorten", json=params, headers=header)
            short = URL(response.json()["id"])
        except Exception:
            short = url
        return short

    def expandUrl(self, url: URL) -> URL:
        if ("https://" not in url.url) and ("http://" not in url.url):
            url.url = "http://" + url.url
        header = {
            "Authorization": self._apikey,
            "Content-Type": "application/json"
        }
        params = {
            "bitlink_id": requote_uri(url.url)
        }
        try:
            response = post(f"{self._baseurl}/expand", json=params, headers=header)
            long = URL(response.json()["long_url"])
        except Exception:
            long = url
        return long
