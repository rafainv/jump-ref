import os
import requests
import base64
from nacl import encoding, public

# --- Configurações ---
URL = os.getenv("URL_API")
GOOGLE_ID_TOKEN = os.getenv("TOKEN")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
GITHUB_PAT = os.getenv("TOKEN_PAT")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")

HEADERS = {
    "User-Agent": "Android/10 JT/1.4.4",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/json; charset=utf-8"
}

# --- Função para salvar secret no GitHub ---
def save_secret_to_github(nome, valor):
    """Salva secret criptografada usando PAT"""
    # Pega a public key do repo
    r = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/actions/secrets/public-key",
        headers={"Authorization": f"Bearer {GITHUB_PAT}", "Accept": "application/vnd.github+json"}
    )
    r.raise_for_status()
    key_data = r.json()

    # Criptografa valor
    sealed_box = public.SealedBox(public.PublicKey(key_data["key"].encode("utf-8"), encoding.Base64Encoder()))
    encrypted_value = sealed_box.encrypt(valor.encode("utf-8"))
    encrypted_value_b64 = base64.b64encode(encrypted_value).decode("utf-8")

    # Atualiza secret
    r2 = requests.put(
        f"https://api.github.com/repos/{GITHUB_REPO}/actions/secrets/{nome}",
        headers={"Authorization": f"Bearer {GITHUB_PAT}", "Accept": "application/vnd.github+json"},
        json={"encrypted_value": encrypted_value_b64, "key_id": key_data["key_id"]}
    )
    r2.raise_for_status()
    print(f"✅ Secret {nome} atualizado no GitHub")

# --- Função para renovar ACCESS_TOKEN via refresh_token ---
def refresh_access_token(refresh_token):
    r = requests.post(f"{URL}/auth/jwt/refresh", headers=HEADERS, json={"refresh_token": refresh_token})
    if r.status_code == 200:
        return r.json()["data"]["jwt"]
    return None

# --- Função para login via Google ID Token ---
def login_with_google(id_token):
    r = requests.post(f"{URL}/auth/jwt/google/tokens", headers=HEADERS, json={"id_token": id_token})
    if r.status_code == 200:
        data = r.json()["data"]
        if "refresh_token" in data:
            save_secret_to_github("REFRESH_TOKEN", data["refresh_token"])
        return data.get("jwt")
    return None

# --- Função principal para obter ACCESS_TOKEN ---
def get_access_token():
    token = None
    if REFRESH_TOKEN:
        token = refresh_access_token(REFRESH_TOKEN)
        if token:
            return token
    if GOOGLE_ID_TOKEN:
        token = login_with_google(GOOGLE_ID_TOKEN)
        if token:
            return token
    raise Exception("❌ Não foi possível obter ACCESS_TOKEN.")

# --- Execução ---
if __name__ == "__main__":
    access_token = get_access_token()
    save_secret_to_github("ACCESS_TOKEN", access_token)

    # Faz request segura imediatamente
    endpoint = f"{URL}/some_endpoint"
    r = requests.get(endpoint, headers={"Authorization": f"Bearer {access_token}"})
    if r.status_code == 200:
        print("✅ Request realizada com sucesso.")
    else:
        print(f"⚠️ Erro na request: {r.status_code} -> {r.text}")
