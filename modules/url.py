from hashlib import sha256

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

    def removeTag(self, tag: str):
        length = len(self.url)
        tag_index = self.url.find(tag + "=")

        while tag_index > 0:
            next_parameter_index = self.url[tag_index:].find("&")
            if (next_parameter_index + tag_index + 1 >= length) or (next_parameter_index < 0):
                self.url = self.url[:(tag_index - 1)]
            else:
                if self.url[tag_index - 1] != "&":
                    self.url = self.url[:tag_index] + self.url[(next_parameter_index + tag_index + 1):]
                else:
                    self.url = self.url[:(tag_index - 1)] + self.url[(next_parameter_index + tag_index):]
            length = len(self.url)
            tag_index = self.url.find(tag + "=")

        if self.isAmazonUrl:
            if sum([required_tag in self.url for required_tag in ["dp", "product", "gp"]]):
                urlAmazonSplit = self.url.split("amazon.", 1)
                afterAmazonParts = urlAmazonSplit[1].split("/")
                nat = afterAmazonParts[0]
                urlParts = afterAmazonParts[1:]
                if len(urlParts) > 0:
                    while urlParts[0] not in ["dp", "product"]:
                        urlParts.pop(0)
                if len(urlParts) > 0 and urlParts[0] == "dp":
                    urlParts.pop(0)

                self.url = f"https://amazon.{nat}/dp/{'/'.join(urlParts)}"
            else:
                if tag not in self.url:
                    return self.url
                else:
                    tag_start = self.url.find(tag)
                    tag_end = self.url.find("&", tag_start)
                    if tag_end == -1:
                        tag_end = len(self.url)
                    self.url = self.url[:tag_start] + self.url[tag_end:]

        return self.url

    def clean(self):
        tags = ["ref", "tag", "linkId", "keywords", "qid", "s", "ascsubtag"]
        for tag in tags:
            self.removeTag(tag)

    def applyReferral(self, referral: str):
        self.clean()
        separator = "&" if "?" in self.url > 0 else "?"
        self.url += f"{separator}tag={referral}"

    def sha256(self) -> str:
        return sha256(self.url.encode()).hexdigest()

    def __str__(self):
        return self.url
