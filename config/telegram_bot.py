import requests
#this is optional if you want to get notification in Telegram app when certain events are heppend like buying or selling of stock

#create telegram BOT. get token and chat_id provided by telegram.
# got to url https://core.telegram.org/bots to know how to create BOT.

token = 'bot17891918647:AAF4fajdkakdfLFKWLp-Cgoab13DHkzi89G65w'
chat_id = 221597864


def htmlReqGETBot(message):
    requests.get(
        f'https://api.telegram.org/{token}/sendMessage?chat_id={chat_id}&text={message}'
    )
    return None
