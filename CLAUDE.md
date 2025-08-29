# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a news fetching system built with CrewAI that extracts news from websites, summarizes them using AI agents, and sends email reports. The system uses two main AI agents: an Extractor that parses web content to find news items, and a Summarizer that creates concise summaries.

## Key Commands

**Running the application:**
```bash
python -m zhixin.main
```

**Using UV for dependency management:**
```bash
uv install  # Install dependencies
uv run python -m zhixin.main  # Run with UV
```

## Architecture

The codebase follows a simple structure:

- `zhixin/main.py`: Core application logic with Extractor and Summarizer agent classes
- `zhixin/config.py`: Pydantic configuration classes for CrewAI settings
- `zhixin/templates/markdown.j2`: Jinja2 template for generating markdown reports
- `zhixin/experiments/`: Contains experimental scripts for testing features

**Key Components:**
- **Extractor class**: Uses a CrewAI agent to parse web pages and extract news items (title, date, URL)
- **Summarizer class**: Uses a CrewAI agent to generate summaries of individual news articles
- **News/NewsSummary models**: Pydantic models for structured data
- **Email functionality**: Sends HTML reports via Mailgun API

**Configuration:**
- Uses Pydantic Settings for configuration management
- CrewAI agent settings (verbose mode, max RPM) configurable via ZhixinConfig
- Requires OPENAI_API_KEY and MAILGUN_API_KEY environment variables

**Templates:**
- Uses Jinja2 for markdown generation from news summaries
- Converts markdown to HTML for email reports