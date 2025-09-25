# import requests
# import json
# import os
# from time import sleep
# from dotenv import load_dotenv

# load_dotenv()

# url = os.getenv("URL_API")
# url_app = os.getenv("URL_APP")
# token = os.getenv("TOKEN")
# user_id = os.getenv("USER_ID")

# headers = {
#     "authorization": f"Bearer {token}",
#     "user-agent": "Mozilla/5.0 (Linux; Android 10; moto g(7) play Build/QPYS30.52-22-14; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/140.0.7339.51 Mobile Safari/537.36",
#     "accept": "application/json, text/plain, */*",
#     "content-type": "application/json",
#     "origin": url_app,
#     "x-requested-with": "io.jumptask.app",
#     "referer": f"{url_app}/",
#     "accept-encoding": "gzip, deflate, br, zstd",
#     "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
# }

# data = {
#     "user_id": user_id
# }

# balance = requests.get(f"{url}/accounting/balances", headers=headers)

# if balance.status_code == 200:
#     print(balance.json()["data"]["total"])
#     claim = requests.post(f"{url}/accounting/device-share-rewards", headers=headers, json=data)
#     i = 0
#     while claim.json().get("title") and i < 5:
#         sleep(60)
#         claim = requests.post(f"{url}/accounting/device-share-rewards", headers=headers, json=data)
#         print(claim.json())
#         if claim.json().get("title") is None:
#             break
#         i += 1
#     sleep(120)
#     print(balance.json()["data"]["total"])
# else:
#     print("Erro ao acessar a API")

import requests
import json
import os
from time import sleep
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("URL_API")
url_app = os.getenv("URL_APP")
token = os.getenv("TOKEN")
user_id = os.getenv("USER_ID")

headers = {
    "authorization": f"Bearer {token}",
    "user-agent": "Mozilla/5.0 (Linux; Android 10; moto g(7) play Build/QPYS30.52-22-14; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/140.0.7339.51 Mobile Safari/537.36",
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": url_app,
    "x-requested-with": "io.jumptask.app",
    "referer": f"{url_app}/",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
}

data = {
    "user_id": user_id
}

def safe_json(response):
    """Tenta converter resposta em JSON, se não conseguir mostra o texto"""
    try:
        return response.json()
    except ValueError:
        print("❌ Resposta não é JSON")
        print("🔹 Status:", response.status_code)
        print("🔹 Conteúdo bruto:", response.text[:500])  # limita a 500 chars
        return None

# --- Consulta saldo ---
balance = requests.get(f"{url}/accounting/balances", headers=headers)

balance_data = safe_json(balance)
if balance.status_code == 200 and balance_data:
    total = balance_data.get("data", {}).get("total", "N/A")
    print("💰 Saldo inicial:", total)

    # --- Tentativa de claim ---
    i = 0
    while i < 5:
        claim = requests.post(f"{url}/accounting/device-share-rewards", headers=headers, json=data)
        claim_data = safe_json(claim)

        if not claim_data:
            break  # se não for JSON, sai do loop

        print("📩 Claim response:", claim_data)

        # sai se não existir 'title'
        if claim_data.get("title") is None:
            break

        i += 1
        print(f"⏳ Esperando 60s antes da próxima tentativa ({i}/5)...")
        sleep(60)

    # --- Aguarda e mostra saldo final ---
    print("⏳ Aguardando 120s para saldo final...")
    sleep(120)

    balance = requests.get(f"{url}/accounting/balances", headers=headers)
    balance_data = safe_json(balance)
    if balance_data:
        print("💰 Saldo final:", balance_data.get("data", {}).get("total", "N/A"))
else:
    print("❌ Erro ao acessar a API - Status:", balance.status_code)
