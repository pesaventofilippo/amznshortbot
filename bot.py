from time import sleep
from telepotpro import Bot, glance
from telepotpro.namedtuple import InlineQueryResultArticle, InputTextMessageContent
from threading import Thread
from json import load as jsload
from os.path import abspath, dirname, join
from hashlib import sha256
from requests import post
from requests.utils import requote_uri

with open(join(dirname(abspath(__file__)), "settings.json")) as settings_file:
    settings = jsload(settings_file)

bot = Bot(settings["token"])


def expandUrl(url: str):
    header = {
        "Authorization": settings["bitlyAuth"],
        "Content-Type": "application/json"
    }
    params = {
        "bitlink_id": requote_uri(url)
    }
    try:
        response = post("https://api-ssl.bitly.com/v4/expand", json=params, headers=header)
        data = response.json()
        long = data["long_url"]
    except Exception:
        long = url
    return long


def stripUrl(url: str):
    # Extract full link
    if "amzn.to/" in url:
        url = expandUrl(url.replace("http://", "").replace("https://", ""))

    # Remove extra tags
    tags = ["ref", "dchild", "keywords", "qid", "sr", "tag"]
    for tag in tags:
        tag_index = url.find(tag + "=")
        while tag_index > 0:
            next_parameter_index = url[tag_index:].find("&")
            if (next_parameter_index + tag_index + 1 >= len(url)) \
                    or (next_parameter_index < 0):
                url = url[:(tag_index - 1)]
            else:
                if url[tag_index - 1] != "&":
                    url = url[:tag_index] + \
                          url[(next_parameter_index + tag_index + 1):]
                else:
                    url = url[:(tag_index - 1)] + \
                          url[(next_parameter_index + tag_index):]
            tag_index = url.find(tag + "=")

    # Remove extra item description
    urlAmazonSplit = url.split("amazon.", 1)
    afterAmazonParts = urlAmazonSplit[1].split("/")
    nat = afterAmazonParts[0]
    urlParts = afterAmazonParts[1:]
    while urlParts[0] != "dp":
        urlParts.pop(0)

    # Rebuild url
    return f"amazon.{nat}/{'/'.join(urlParts)}?tag={settings['referral']}"


def shortUrl(url: str):
    if ("https://" not in url) and ("http://" not in url):
        escaped = "http://" + url
    else:
        escaped = url

    header = {
        "Authorization": settings["bitlyAuth"],
        "Content-Type": "application/json"
    }
    params = {
        "long_url": requote_uri(escaped)
    }
    try:
        response = post("https://api-ssl.bitly.com/v4/shorten", json=params, headers=header)
        data = response.json()
        short = data["id"]
    except Exception:
        short = url
    return short


def isAmazonUrl(url: str):
    prefixList = [
        "http://www.amazon.",
        "https://www.amazon.",
        "http://amazon.",
        "https://amazon.",
        "www.amazon.",
        "amazon.",
        "http://www.amzn.to",
        "https://www.amazn.to",
        "http://amzn.to",
        "https://amzn.to",
        "www.amzn.to",
        "amzn.to"
    ]
    return url.startswith(tuple(prefixList))


def reply(msg):
    chatId = msg['chat']['id']
    if "text" in msg:
        text = msg['text']
    elif "caption" in msg:
        text = msg['caption']
    else:
        text = ""

    if isAmazonUrl(text):
        bot.sendMessage(chatId, shortUrl(stripUrl(text)), disable_web_page_preview=True)

    else:
        longUrl = settings['exampleStartLink']
        strippedUrl = stripUrl(longUrl)
        shortedUrl = shortUrl(strippedUrl)
        bot.sendMessage(chatId, f"<b>Hi!</b> 👋\n"
                                f"You can use me in any chat to short Amazon URLs before sending them.\n"
                                f"Just type @amznshortbot in the text field, followed by the URL you want to send!\n\n"
                                f"ℹ️ <b>Example:</b>\n"
                                f"<b>Link before:</b> {longUrl}\n"
                                f"<b>Stripped link:</b> {strippedUrl}\n"
                                f"<b>Shorted link:</b> {shortedUrl}\n\n"
                                f"<i>Hint: you can also just send me a link here and I will short it for you!</i>"
                                f"", parse_mode="HTML", disable_web_page_preview=True)


def query(msg):
    queryId, chatId, queryString = glance(msg, flavor='inline_query')
    if isAmazonUrl(queryString):
        amzSha256 = sha256(("amz" + queryString).encode()).hexdigest()
        bitSha256 = sha256(("bit" + queryString).encode()).hexdigest()
        strippedUrl = stripUrl(queryString)
        shortedUrl = shortUrl(strippedUrl)

        results = [
            InlineQueryResultArticle(
                id=bitSha256,
                title="Shorted URL",
                input_message_content=InputTextMessageContent(
                    message_text=shortedUrl, disable_web_page_preview=True),
                description="Short link with bit.ly",
                thumb_url="https://i.imgur.com/UXDqKay.jpg"
            ),
            InlineQueryResultArticle(
                id=amzSha256,
                title="Stripped URL",
                input_message_content=InputTextMessageContent(
                    message_text=strippedUrl, disable_web_page_preview=True),
                description="Original amazon link without extra tags",
                thumb_url="https://i.imgur.com/7eAooJr.jpg"
            )
        ]
        bot.answerInlineQuery(queryId, results, cache_time=3600, is_personal=False)

    # Invalid link
    elif queryString.strip() != "":
        linkSha256 = sha256(queryString.encode()).hexdigest()
        results = [InlineQueryResultArticle(
            id=linkSha256,
            title="Invalid link",
            input_message_content=InputTextMessageContent(
                message_text=queryString, disable_web_page_preview=True),
            description="Invalid link. Type an Amazon link to short it (or tap to send anyway)",
            thumb_url="https://i.imgur.com/7eAooJr.jpg"
            )]
        bot.answerInlineQuery(queryId, results, cache_time=3600, is_personal=False)


def incoming_message(msg):
    Thread(target=reply, args=[msg]).start()

def incoming_query(msg):
    Thread(target=query, args=[msg]).start()

bot.message_loop({'chat': incoming_message, 'inline_query': incoming_query})
while True:
    sleep(60)
