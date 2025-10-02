from requests_html import HTMLSession

# Cria a sessão
session = HTMLSession()

# URL alvo (JS dinâmico)
url = "https://quotes.toscrape.com/js/"

# Faz a requisição
r = session.get(url)

# Renderiza o JS em modo headless
# timeout aumenta limite de espera
# sleep dá um tempo extra para carregar scripts
r.html.render(timeout=30, sleep=2)

# Mostra uma prévia do HTML renderizado
print("Trecho do HTML renderizado:\n", r.html.html[:500])

# Extrai dados dinâmicos
quotes = r.html.find("span.text")
authors = r.html.find("small.author")

for q, a in zip(quotes, authors):
    print(f"{q.text} — {a.text}")
