import os
import json
import asyncio
import aiohttp
import click
from bs4 import BeautifulSoup
from typing import Dict, List


url = 'https://www.urionlinejudge.com.br/judge/pt/login'

with open('./page_properties.json', 'r') as data:
    page_codes = json.load(data)

answer_types = page_codes['answer_types']
sort_options = page_codes['sort_options']
languages_dict = page_codes['languages']

@click.command()
@click.argument('email', required=True, type=str)
@click.argument('password', required=True, type=str)
@click.option('--languages', default='', help='The code languages that you want to download')
@click.option('--answer_id', default=1, help='The answer code that your solution got.')
def query_builder(email, password, languages, answer_id):
    payload = {
        '_csrfToken': '',
        'email': email,
        'password': password,
    }
    query = {
        'answer_id': answer_id,
        'language_id': languages,
        'sort': 'problem_id',
        'direction': 'asc',
    }
    asyncio.run(fetch_async(payload, query))

async def sign_in(session_log: aiohttp.ClientSession, payload: Dict):
    url = "https://www.urionlinejudge.com.br/"
    async with session_log.get(url) as response:
        response_text = await response.read()
        soup = BeautifulSoup(response_text, 'html.parser')
        csrfToken = soup.find(name='input', attrs={'name':'_csrfToken'}).get('value')
        payload['_csrfToken'] = csrfToken
        response = await session_log.post(response.url, data=payload)
        return response.url.human_repr().find('login') == -1

async def fetch_async(payload: Dict, query: Dict):
    async with aiohttp.ClientSession() as session:
        is_logged = await sign_in(session, payload)
        if not is_logged:
            print("Failed login attempt. Check your credentials and try again.")
        else:
            runs = await session.get('https://www.urionlinejudge.com.br/judge/runs',
                            params=query)
            runs = await runs.read()
            soup_page = BeautifulSoup(runs, 'html.parser')
            resultados = soup_page.select('.semi-wide.answer.a-1 > a[href]')
            links = []
            for resultado in resultados:
                links.append(resultado.get("href"))

            await fetch_all(session, links)

async def fetch_all(session: aiohttp.ClientSession, links: List[str]):
    tasks = []
    for link in links:
        task = asyncio.ensure_future(fetch(session, link))
        tasks.append(task)
    await asyncio.gather(*tasks)

async def fetch(session, link):
    async with session.get("https://www.urionlinejudge.com.br" + link) as code:
        code_text = await code.text()
        soup_page= BeautifulSoup(code_text, 'html.parser', multi_valued_attributes=None)
        problem_id, code_body, language_id = get_problem_attributes(soup_page)
        write_code_to_file(problem_id, code_body, language_id)


def write_code_to_file(problem_id, code_body, language_id):
    code_language, code_extension = get_code_properties(language_id)
    path = f'./codes/{code_language}/'
    try:
        os.makedirs(path)
    except FileExistsError:
        print('Directory found - ', end='')
    else:
        print(f'Directory not found, creating folder for {code_language} at {path}')
    finally:
        with open(path+problem_id+code_extension, 'w+') as code_file:
            print(f'Writing {code_language} solution for - {problem_id} - at {path}.')
            code_file.write(code_body.replace('\n', ''))


def get_problem_attributes(soup_page: BeautifulSoup):
    problem_id = soup_page.select_one("#information-code a").contents[0]
    code_body = soup_page.find(name='pre').contents[0]
    language_id = soup_page.find(name='pre')['class']
    language_id = int(language_id.split('-')[-1])
    return (problem_id, code_body, language_id)

def get_code_properties(language_id):
    code_dict = next(filter(lambda x: x["id"] == language_id, languages_dict))
    code_language = code_dict.get('language')
    code_extension = code_dict.get('extension')
    return code_language, code_extension

###################################################################

if __name__ == '__main__':
    query_builder()