from pathlib import Path

import pandas as pd
import logfire
from pydantic import Field, BaseModel
from rich.console import Console

from tdl.processor import TDLManager

logfire.configure()
console = Console()


class TelegramDownloader(BaseModel):
    path: str | None = Field(
        default=None,
        title="Path to the CSV or Excel file",
        description="Path to the CSV or Excel file",
        examples=["./data/example.csv", "./data/example.txt", "./data/example.xlsx"],
    )

    def get_urls(self) -> list[str]:
        if not self.path:
            self.path = console.input("Please provide the path to the CSV or Excel file: ")
        filepath = Path(self.path)
        try:
            data = pd.read_csv(filepath.as_posix())
        except UnicodeDecodeError:
            data = pd.read_excel(filepath.as_posix())
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
