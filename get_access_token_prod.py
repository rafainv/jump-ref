import requests
import json
import os
import base64
from nacl import encoding, public

# Headers padrão JumpTask
HEADERS = {
    "User-Agent": "Android/10 JT/1.4.4",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/json; charset=utf-8"
}

# Pega o ID token do Google do GitHub Secret
GOOGLE_ID_TOKEN = os.getenv("GOOGLE_ID_TOKEN")
if not GOOGLE_ID_TOKEN:
    raise Exception("Variável de ambiente GOOGLE_ID_TOKEN não definida.")

# GitHub info
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")  # existente ou vazio

# -------------------------------
# Funções GitHub
# -------------------------------
def save_secret_to_github(secret_name, secret_value):
    """Salva qualquer secret no GitHub repo via API"""
    r = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/actions/secrets/public-key",
                     headers={"Authorization": f"Bearer {GITHUB_TOKEN}"})
    r.raise_for_status()
    key_data = r.json()
    key_id = key_data["key_id"]
    public_key = key_data["key"]

    sealed_box = public.SealedBox(public.PublicKey(public_key.encode("utf-8"), encoder=encoding.Base64Encoder))
    encrypted_value = sealed_box.encrypt(secret_value.encode("utf-8"))
    encrypted_value_b64 = base64.b64encode(encrypted_value).decode("utf-8")

    put_url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/secrets/{secret_name}"
    r2 = requests.put(put_url,
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
        json={"encrypted_value": encrypted_value_b64, "key_id": key_id}
    )
    r2.raise_for_status()

# -------------------------------
# Funções JumpTask
# -------------------------------
def refresh_access_token(refresh_token):
    url = "https://api.jumptask.io/auth/jwt/refresh"
    payload = {"refresh_token": refresh_token}
    r = requests.post(url, headers=HEADERS, data=json.dumps(payload))
    if r.status_code == 200:
        return r.json().get("data", {}).get("jwt")
    return None

def login_with_google(id_token):
    url = "https://api.jumptask.io/auth/jwt/google/tokens"
    payload = {"id_token": id_token}
    r = requests.post(url, headers=HEADERS, data=json.dumps(payload))
    if r.status_code == 200:
        data = r.json().get("data", {})
        if "refresh_token" in data:
            save_secret_to_github("REFRESH_TOKEN", data["refresh_token"])
        return data.get("jwt")
    return None

def get_access_token():
    global REFRESH_TOKEN
    if REFRESH_TOKEN:
        token = refresh_access_token(REFRESH_TOKEN)
        if token:
            return token
    token = login_with_google(GOOGLE_ID_TOKEN)
    if token:
        return token
    raise Exception("Não foi possível obter access_token.")

# -------------------------------
# Execução principal
# -------------------------------
if __name__ == "__main__":
    token = get_access_token()
    print(token)  # opcional para debug
    save_secret_to_github("ACCESS_TOKEN", token)  # salva no GitHub Secrets



# import requests
# import json
# import os
# import base64
# from nacl import encoding, public

# # Headers padrão JumpTask
# HEADERS = {
#     "User-Agent": "Android/10 JT/1.4.4",
#     "Accept-Encoding": "gzip",
#     "Content-Type": "application/json; charset=utf-8"
# }

# # Seu ID token embutido (apenas na primeira execução)
# GOOGLE_ID_TOKEN = os.getenv("TOKEN")
# # GitHub info
# GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
# REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")  # existente ou vazio

# # -------------------------------
# # Funções JumpTask
# # -------------------------------
# def save_refresh_token_to_github(new_token):
#     # Pega chave pública
#     r = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/actions/secrets/public-key",
#                      headers={"Authorization": f"Bearer {GITHUB_TOKEN}"})
#     r.raise_for_status()
#     key_data = r.json()
#     key_id = key_data["key_id"]
#     public_key = key_data["key"]

#     # Criptografa valor
#     sealed_box = public.SealedBox(public.PublicKey(public_key.encode("utf-8"), encoder=encoding.Base64Encoder))
#     encrypted_value = sealed_box.encrypt(new_token.encode("utf-8"))
#     encrypted_value_b64 = base64.b64encode(encrypted_value).decode("utf-8")

#     # Atualiza secret
#     put_url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/secrets/REFRESH_TOKEN"
#     r2 = requests.put(put_url,
#         headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
#         json={"encrypted_value": encrypted_value_b64, "key_id": key_id}
#     )
#     r2.raise_for_status()
#     print(f"REFRESH_TOKEN atualizado no GitHub Secrets: {new_token}")  # imprime token para debug

# def refresh_access_token(refresh_token):
#     url = "https://api.jumptask.io/auth/jwt/refresh"
#     payload = {"refresh_token": refresh_token}
#     r = requests.post(url, headers=HEADERS, data=json.dumps(payload))
#     if r.status_code == 200:
#         return r.json().get("data", {}).get("jwt")
#     return None

# def login_with_google(id_token):
#     url = "https://api.jumptask.io/auth/jwt/google/tokens"
#     payload = {"id_token": id_token}
#     r = requests.post(url, headers=HEADERS, data=json.dumps(payload))
#     if r.status_code == 200:
#         data = r.json().get("data", {})
#         if "refresh_token" in data:
#             print(f"NEW_REFRESH_TOKEN={data['refresh_token']}")  # debug
#             save_refresh_token_to_github(data["refresh_token"])
#         return data.get("jwt")
#     return None

# def get_access_token():
#     global REFRESH_TOKEN
#     if REFRESH_TOKEN:
#         token = refresh_access_token(REFRESH_TOKEN)
#         if token:
#             print("Access token renovado com refresh_token existente.")
#             return token
#         else:
#             print("Refresh_token expirado. Usando login Google...")

#     token = login_with_google(GOOGLE_ID_TOKEN)
#     if token:
#         print("Login com Google realizado com sucesso.")
#         return token

#     raise Exception("Não foi possível obter access_token.")

# if __name__ == "__main__":
#     token = get_access_token()
#     print("ACCESS_TOKEN=" + token)
