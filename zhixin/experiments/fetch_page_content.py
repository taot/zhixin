from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from jinja2 import Template
from pydantic import BaseModel, Field
from typing import List, Type, Optional

from crewai import Agent


def get_page_content(url: str) -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    text = response.text
    return text


class GetPageContentToolInput(BaseModel):
    url: str = Field(..., description="The url of the page")


class GetPageContentTool(BaseTool):
    name: str = "get_page_content"
    description: str = "Given a url, get the content of the corresponding web page"
    args_schema: Type[BaseModel] = GetPageContentToolInput

    def _run(self, url: str) -> str:
        content = get_page_content(url)
        return content


class Link(BaseModel):
    url: str
    text: str
    is_external: bool


def extract_links_from_page(url: str) -> list[Link]:
    content = get_page_content(url)

    soup = BeautifulSoup(content, 'html.parser')

    links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Convert relative URLs to absolute URLs
        absolute_url = urljoin(url, href)

        # Get link text (clean whitespace)
        link_text = link.get_text(strip=True)

        is_external = urlparse(absolute_url).netloc != urlparse(url).netloc
        page_link = Link(
            url=absolute_url,
            text=link_text,
            is_external=is_external
        )
        links.append(page_link)

    return links


class News(BaseModel):
    is_news: bool
    date: str
    title: str
    url: str


class NewsWithSummary(News):
    summary: str


class NewsExtractorResponse(BaseModel):
    news: list[News]


JINJA2_TEMPLATE = """
# Articles

{% for item in objects -%}
## [{{ item.title }}]({{ item.url }})

Date: {{ item.date }}

{{ item.summary }}

{% if not loop.last %}---{% endif %}

{% endfor %}
"""


def main() -> None:
    url = "https://deepmind.google/"

    content = get_page_content(url)

    news_extractor = Agent(
        role="News extractor",
        goal=f"Extract the news from the web page content of base url {url}",
        backstory=f"""You are a meticulous html parser. You will find news or research and extract their information from the web page content.
Extract the title, date and absolute link url of the news or research. If it's not an absolute url, then create an absolute url by concatenate the relative url with base url {url}.""",
        verbose=True
    )

    result = news_extractor.kickoff(content, response_format=NewsExtractorResponse)

    news_with_summary_list = []

    if result.pydantic is None:
        print("##### Cannot get pydantic model from LLM response")
    else:
        assert isinstance(result.pydantic, NewsExtractorResponse)
        for news in result.pydantic.news:
            print("\n######")
            print(news)
            news_content = get_page_content(news.url)

            summarizer = Agent(
                role="News summarizer",
                goal="Summarize the news",
                backstory="""Given the content of the news web page, summarize it to one paragraph with 2 to 3 sentences.""",
                verbose=True
            )

            summary_result = summarizer.kickoff(news_content)
            summary = summary_result.raw
            print(summary)

            with_summary = NewsWithSummary(
                is_news=True,
                date=news.date,
                title=news.title,
                url=news.url,
                summary=summary
            )

            news_with_summary_list.append(with_summary)

    template = Template(JINJA2_TEMPLATE)
    markdown_output = template.render(objects=news_with_summary_list)
    print(markdown_output)


if __name__ == "__main__":
    main()
