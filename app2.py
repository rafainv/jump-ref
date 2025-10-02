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
r.html.render(timeout=20, sleep=2, keep_page=True, scrolldown=3)


# Mostra uma prévia do HTML renderizado
print("Trecho do HTML renderizado:\n", r.html.html)
