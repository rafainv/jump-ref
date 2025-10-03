import requests
import json
import os
from time import sleep
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("URL_API")
url_app = os.getenv("URL_APP")
url_x = os.getenv("URL_X")
token = os.getenv("ACCESS_TOKEN")
user_id = os.getenv("USER_ID")
user_agent = os.getenv("USER_AGENT")

headers = {
    "authorization": f"Bearer {token}",
    "user-agent": user_agent,
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": url_app,
    "x-requested-with": url_x,
    "referer": f"{url_app}/",
    # "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
}

data = {
    "user_id": user_id
}

balance = requests.get(f"{url}/accounting/balances", headers=headers)

if balance.status_code == 200:
    print(balance.json()["data"]["total"])
    claim = requests.post(f"{url}/accounting/device-share-rewards", headers=headers, json=data)
    i = 0
    while claim.json().get("title") and i < 5:
        sleep(60)
        claim = requests.post(f"{url}/accounting/device-share-rewards", headers=headers, json=data)
        if claim.json().get("title") is None:
            break
        i += 1
    print(claim.json())
    sleep(300)
    print(balance.json()["data"]["total"])
else:
    print("Erro ao acessar a API")


