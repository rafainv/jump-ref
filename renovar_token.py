import os
import requests
import base64
import json
import time
from datetime import datetime, timedelta
from nacl import encoding, public

# --- Configurações ---
URL = os.getenv("URL_API")
GOOGLE_ID_TOKEN = os.getenv("TOKEN")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
GITHUB_PAT = os.getenv("TOKEN_PAT")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
TOKEN_EXPIRATION_MARGIN = 5  # minutos antes de expirar para renovar
MAX_RETRIES = 3
RETRY_DELAY = 5  # segundos entre tentativas

HEADERS = {
    "User-Agent": "Android/10 JT/1.4.4",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/json; charset=utf-8"
}

# --- Função para salvar secret no GitHub ---
def save_secret_to_github(nome, valor):
    try:
        r = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/actions/secrets/public-key",
            headers={"Authorization": f"Bearer {GITHUB_PAT}", "Accept": "application/vnd.github+json"}
        )
        r.raise_for_status()
        key_data = r.json()
        sealed_box = public.SealedBox(public.PublicKey(key_data["key"].encode("utf-8"), encoding.Base64Encoder()))
        encrypted_value = sealed_box.encrypt(valor.encode("utf-8"))
        encrypted_value_b64 = base64.b64encode(encrypted_value).decode("utf-8")
        r2 = requests.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/actions/secrets/{nome}",
            headers={"Authorization": f"Bearer {GITHUB_PAT}", "Accept": "application/vnd.github+json"},
            json={"encrypted_value": encrypted_value_b64, "key_id": key_data["key_id"]}
        )
        r2.raise_for_status()
        print(json.dumps({"status": "success", "secret": nome, "message": "Secret atualizado"}))
    except Exception as e:
        print(json.dumps({"status": "error", "secret": nome, "message": str(e)}))

# --- Renovar ACCESS_TOKEN via REFRESH_TOKEN ---
def refresh_access_token(refresh_token):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.post(f"{URL}/auth/jwt/refresh", headers=HEADERS, json={"refresh_token": refresh_token})
            if r.status_code == 200:
                data = r.json()["data"]
                exp_minutes = data.get("expires_in", 60)
                expiration_time = datetime.utcnow() + timedelta(minutes=exp_minutes)
                return data.get("jwt"), expiration_time
            elif r.status_code >= 500:
                print(f"⚠️ Tentativa {attempt} falhou, retry em {RETRY_DELAY}s")
                time.sleep(RETRY_DELAY)
            else:
                print(json.dumps({"status": "fail", "method": "refresh_token", "code": r.status_code, "text": r.text}))
                break
        except Exception as e:
            print(f"Erro na tentativa {attempt} de refresh_token:", e)
            time.sleep(RETRY_DELAY)
    return None, None

# --- Gerar ACCESS_TOKEN via GOOGLE_ID_TOKEN ---
def login_with_google(id_token):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.post(f"{URL}/auth/jwt/google/tokens", headers=HEADERS, json={"id_token": id_token})
            if r.status_code == 200:
                data = r.json()["data"]
                if "refresh_token" in data:
                    save_secret_to_github("REFRESH_TOKEN", data["refresh_token"])
                exp_minutes = data.get("expires_in", 60)
                expiration_time = datetime.utcnow() + timedelta(minutes=exp_minutes)
                return data.get("jwt"), expiration_time
            elif r.status_code >= 500:
                print(f"⚠️ Tentativa {attempt} falhou, retry em {RETRY_DELAY}s")
                time.sleep(RETRY_DELAY)
            else:
                print(json.dumps({"status": "fail", "method": "google_login", "code": r.status_code, "text": r.text}))
                break
        except Exception as e:
            print(f"Erro na tentativa {attempt} de login Google:", e)
            time.sleep(RETRY_DELAY)
    return None, None

# --- Checa se token precisa renovar ---
def token_expirando(expiration_time):
    if not expiration_time:
        return True
    now = datetime.utcnow()
    return (expiration_time - now) <= timedelta(minutes=TOKEN_EXPIRATION_MARGIN)

# --- Obter ACCESS_TOKEN automaticamente ---
def get_access_token():
    token = None
    expiration_time = None
    if REFRESH_TOKEN:
        token, expiration_time = refresh_access_token(REFRESH_TOKEN)
        if token:
            print(json.dumps({"status": "success", "method": "refresh_token", "message": "ACCESS_TOKEN renovado"}))
            return token, expiration_time
    if GOOGLE_ID_TOKEN:
        token, expiration_time = login_with_google(GOOGLE_ID_TOKEN)
        if token:
            print(json.dumps({"status": "success", "method": "google_login", "message": "ACCESS_TOKEN gerado"}))
            return token, expiration_time
    raise Exception("❌ Não foi possível obter ACCESS_TOKEN. Verifique REFRESH_TOKEN e GOOGLE_ID_TOKEN.")

# --- Executa request segura ---
def safe_request(endpoint, access_token):
    try:
        r = requests.get(f"{URL}{endpoint}", headers={"Authorization": f"Bearer {access_token}"})
        if r.status_code == 200:
            print(json.dumps({"status": "success", "endpoint": endpoint, "message": "Request realizada"}))
            return r.json()
        else:
            print(json.dumps({"status": "fail", "endpoint": endpoint, "code": r.status_code, "text": r.text}))
    except Exception as e:
        print(json.dumps({"status": "error", "endpoint": endpoint, "message": str(e)}))
    return None

# --- Main ---
if __name__ == "__main__":
    try:
        access_token, expiration_time = get_access_token()

        # Atualiza ACCESS_TOKEN somente se estiver expirando
        if token_expirando(expiration_time):
            save_secret_to_github("ACCESS_TOKEN", access_token)

        # Exemplo de request segura (substitua pelo endpoint real)
        safe_request("/tasks/list", access_token)

    except Exception as e:
        print(json.dumps({"status": "critical_error", "message": str(e)}))
