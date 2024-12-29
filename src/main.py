from pathlib import Path

import pandas as pd
import logfire
from pydantic import Field
from pydantic_settings import BaseSettings

from tdl.processor import TDLManager

logfire.configure()


class TelegramDownloader(BaseSettings):
    path: Path = Field(default="./data/example.csv")

    def get_urls(self) -> list[str]:
        try:
            data = pd.read_csv(self.path.as_posix())
        except UnicodeDecodeError:
            data = pd.read_excel(self.path.as_posix())
        urls = data["url"].to_numpy().tolist()
        return urls

    def get_videos(self, urls: list[str]) -> None:
        tdl = TDLManager(output_path="./data/tmp")
        try:
            tdl.download(urls=urls)
        except RuntimeError:
            logfire.info("You need to login to your Telegram account.")
            logfire.info("Please run `tdl login` in first.")
            # tdl.login()
            # tdl.download(urls=urls)

    def __call__(self) -> None:
        urls = self.get_urls()
        self.get_videos(urls)


if __name__ == "__main__":
    import fire

    fire.Fire(TelegramDownloader)
