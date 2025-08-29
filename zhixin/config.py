from typing import Optional
import tomllib
from pathlib import Path

from pydantic import Field, PositiveInt, BaseModel
from pydantic_settings import BaseSettings

from zhixin.constants import PROJECT_SRC_PATH


class CrewAIConfig(BaseSettings):
    verbose: bool = False
    max_rpm: Optional[PositiveInt] = 5


class NewsSource(BaseModel):
    name: str
    url: str
    enabled: bool = True



class ZhixinConfig(BaseSettings):
    crew_ai: CrewAIConfig = CrewAIConfig()
    
    def load_sources(self, config_file: Path = PROJECT_SRC_PATH / "sites.toml") -> list[NewsSource]:
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file {config_file} not found")
        
        with open(config_file, "rb") as f:
            data = tomllib.load(f)
        
        sources = [NewsSource(**source) for source in data.get("sources", [])]
        return [source for source in sources if source.enabled]
