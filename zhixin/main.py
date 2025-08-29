import logging
import os
from datetime import datetime
from pathlib import Path

import markdown
import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from crewai import Agent

from zhixin.config import ZhixinConfig
from zhixin.constants import PROJECT_SRC_PATH

logger = logging.getLogger(__file__)


class News(BaseModel):
    date: str
    title: str
    url: str


class NewsSummary(News):
    summary: str
    source: str = ""


class NewsExtractorResponse(BaseModel):
    news: list[News]


def get_page_content(url: str) -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    text = response.text
    return text


def extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text and clean up whitespace
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    return text


def send_email(html: str) -> None:
    api_key = os.getenv('MAILGUN_API_KEY', 'MAILGUN_API_KEY')
    url = "https://api.mailgun.net/v3/sandboxab208ee038fe4204a9040f96fef181d4.mailgun.org/messages"

    time_str = datetime.now().astimezone().replace(microsecond=0).isoformat()

    data = {
        "from": "Mailgun Sandbox <postmaster@sandboxab208ee038fe4204a9040f96fef181d4.mailgun.org>",
        "to": "Terry Tao <librakevin@gmail.com>",
        "subject": f"AI News Update ({time_str})",
        "html": html
    }

    resp = requests.post(url, auth=("api", api_key), data=data)
    resp.status_code

    logger.info(f"Mailgun response: status_code = {resp.status_code}, text = {resp.text}")


class Extractor:

    def __init__(self, config: ZhixinConfig, url: str) -> None:
        self._config = config
        self._url = url
        self._agent = Agent(
            role="News extractor",
            goal=f"Extract the news from the web page content of base url {url}",
            backstory=f"""You are a meticulous html parser. You will find news or research and extract their information from the web page content.
            Extract the title, date and absolute link url of the news or research. If it's not an absolute url, then create an absolute url by concatenate the relative url with base url {url}.""",
            max_rpm=config.crew_ai.max_rpm,
            verbose=config.crew_ai.verbose
        )

    def run(self) -> list[News]:
        logger.info(f"Extracting news from {self._url}")
        content = get_page_content(self._url)

        result = self._agent.kickoff(content, response_format=NewsExtractorResponse)

        if result.pydantic is None:
            logger.error(f"Failed to get pydantic model by extracting news from {self._url}")
            return []

        assert isinstance(result.pydantic, NewsExtractorResponse)

        if len(result.pydantic.news) == 0:
            logger.warning(f"No news extracted from {self._url}")
            return []

        return result.pydantic.news


class Summarizer:

    def __init__(self, config: ZhixinConfig) -> None:
        self._config = config
        self._agent = Agent(
            role="News summarizer",
            goal="Summarize the news",
            backstory="""Given the content of the news web page, summarize it to one paragraph with 2 to 3 sentences.""",
            max_rpm=config.crew_ai.max_rpm,
            verbose=config.crew_ai.verbose,
        )

    def run(self, news: News) -> NewsSummary:
        logger.info(f"Summarizing {news}")
        html_content = get_page_content(news.url)
        text_content = extract_text_from_html(html_content)

        result = self._agent.kickoff(text_content)
        summary = result.raw

        news_summary = NewsSummary(
            summary=summary,
            **news.model_dump()
        )

        return news_summary


def generate_markdown(news_summary_list: list[NewsSummary]) -> str:
    env = Environment(loader=FileSystemLoader(PROJECT_SRC_PATH / 'templates'))
    template = env.get_template('markdown.j2')
    markdown_output = template.render(objects=news_summary_list)
    return markdown_output


def main() -> None:
    config = ZhixinConfig()
    sources = config.load_sources()
    
    if not sources:
        logger.error("No enabled sources found in sites.toml")
        return
    
    summarizer = Summarizer(config)
    all_results = []
    
    for source in sources:
        print(f"Processing {source.name}...")
        extractor = Extractor(config, source.url)

        news_list = extractor.run()
        
        for news in news_list:
            news_summary = summarizer.run(news)
            news_summary.source = source.name
            all_results.append(news_summary)
    
    md = generate_markdown(all_results)
    print(md)
    html = markdown.markdown(md)
    print(html)
    send_email(html)


if __name__ == "__main__":
    main()
