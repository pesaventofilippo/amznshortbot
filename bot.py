from telepotpro import Bot, glance, api as tgapi
from telepotpro.namedtuple import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from time import sleep
from requests import get
from threading import Thread
from json import load as jsload
from os.path import abspath, dirname, join
from modules.bitly import BitlyApi
from modules.url import URL

with open(join(dirname(abspath(__file__)), "settings.json")) as settings_file:
    settings = jsload(settings_file)
    if settings.get("api_server"):
        tgapi.set_api_url(settings["api_server"])

bot = Bot(settings["bot_token"])
bitly = BitlyApi(settings["bitly_token"])


def expandUrl(url: URL) -> URL:
    if not (url.url.startswith("http://") or url.url.startswith("https://")):
        url.url = "http://" + url.url
    req = get(url.url)
    return URL(req.url)


def generateUrl(url: URL) -> URL:
    if url.isAmazonUrl:
        url.applyReferral(settings["referral_code"])

    return bitly.shortUrl(url)


def reply(msg):
    chatId = msg['chat']['id']
    text = msg.get("text", "") or msg.get("caption", "")
    url = URL(text)

    try:
        url_ex = expandUrl(url)
        if url.isAmazonUrl:
            shortUrl = generateUrl(url_ex)
            bot.sendMessage(chatId, shortUrl.url, disable_web_page_preview=True)
            return
    except Exception:
        pass

    longUrl = "https://www.amazon.com/Apple-MWP22AM-A-AirPods-Pro/dp/B07ZPC9QD4/ref=sr_1_41?dchild=1&keywords=product&qid=1598027938&sr=8-41&tag=revolutrewa03-21&ascsubtag=df64b4d88a084b80b0d083b1ce868ec7"
    bot.sendMessage(chatId, f"<b>Hi!</b> 👋\n"
                            f"You can use me in any chat to short Amazon URLs before sending them.\n"
                            f"Just type @amznshortbot in the text field, followed by the URL you want to send!\n\n"
                            f"ℹ️ <b>Example:</b>\n"
                            f"<b>Link before:</b> {longUrl}\n"
                            f"<b>Shorted link:</b> amzn.to/3W6DyVO\n\n"
                            f"<i>Hint: you can also just send me a link here and I will short it for you!</i>"
                            f"", parse_mode="HTML", disable_web_page_preview=True,
                            reply_markup=InlineKeyboardMarkup(
                                            inline_keyboard=[[
                                                InlineKeyboardButton(text="💬 Try me!", switch_inline_query="https://www.amazon.com/Apple-iPhone-128GB-Space-Black/dp/B0BN95FRW9")
                                            ]]))


def query(msg):
    queryId, chatId, queryString = glance(msg, flavor='inline_query')
    url = URL(queryString)
    try:
        url_ex = expandUrl(url)
        if url_ex.isAmazonUrl:
            shortUrl = generateUrl(url_ex)
            results = [
                InlineQueryResultArticle(
                    id=shortUrl.sha256(),
                    title="Send Shorted URL",
                    input_message_content=InputTextMessageContent(
                        message_text=shortUrl.url, disable_web_page_preview=True),
                    description="Short link with bit.ly",
                    thumb_url="https://i.imgur.com/UXDqKay.jpg"
                )
            ]
            bot.answerInlineQuery(queryId, results, cache_time=3600, is_personal=False)
            return
    except Exception:
        pass

    # Invalid link
    if queryString.strip() != "":
        results = [InlineQueryResultArticle(
            id=url.sha256(),
            title="Invalid link",
            input_message_content=InputTextMessageContent(
                message_text=url.url, disable_web_page_preview=True),
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
