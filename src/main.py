from pathlib import Path

import pandas as pd
from pydantic_settings import BaseSettings

from tdl.processor import TDLManager


class TelegramDownloader(BaseSettings):
    path: Path

    def get_urls(self) -> list[str]:
        try:
            data = pd.read_csv(self.path.as_posix())
        except UnicodeDecodeError:
            data = pd.read_excel(self.path.as_posix())
        urls = data["url"].to_numpy().tolist()
        return urls

    def get_videos(self, urls: list[str]) -> None:
        tdl = TDLManager(
            func="download",
            serve=False,
            skip_same=True,
            limit=4,
            pool=0,
            threads=8,
            output_path="./data/tmp",
        )
        tdl.run(urls=urls)


if __name__ == "__main__":
    td = TelegramDownloader(path="./data/example.xlsx")
    urls = td.get_urls()
    td.get_videos(urls)
