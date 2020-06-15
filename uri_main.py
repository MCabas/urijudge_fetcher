import requests
from bs4 import BeautifulSoup

url = 'https://www.urionlinejudge.com.br/judge/pt/login'

payload = {
    '_csrfToken': '',
    'email': 'email',
    'password': 'senha',
}

with requests.Session() as s:
    p = s.get(url)
    soup = BeautifulSoup(p.text, 'html.parser')
    csrfToken = soup.find(name='input', attrs={'name':'_csrfToken'}).get('value')
    payload['_csrfToken'] = csrfToken
    p = s.post(url, payload)
    runs = s.get('https://www.urionlinejudge.com.br/judge/pt/runs?answer_id=1')
    soup_page = BeautifulSoup(runs.text, 'html.parser')
    resultados = soup_page.select('.semi-wide.answer.a-1 > a[href]')
    links = []
    for resultado in resultados:
        links.append(resultado.get("href"))

    for link in links:
        codigo = s.get("https://www.urionlinejudge.com.br"+link)
        soup_codigo = BeautifulSoup(codigo.text, 'html.parser')
        identidade = soup_codigo.find(target="_blank").contents[0]
        codigo_python_element = soup_codigo.find(name='pre').contents[0]
        with open('codes/'+identidade+'.py', 'w+') as code:
            code.write(codigo_python_element.replace('\n', ''))
