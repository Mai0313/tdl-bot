import asyncio
from pathlib import Path
import secrets

from bs4 import BeautifulSoup
import httpx
import pandas as pd
import logfire
from pydantic import Field, BaseModel
from rich.console import Console
from rich.progress import Progress

from tdl.processor import TDLManager

logfire.configure()
console = Console()


class TitleParser(BaseModel):
    title: str
    url: str


class TelegramDownloader(BaseModel):
    path: str | None = Field(
        default=None,
        title="Path to the CSV or Excel file",
        description="Path to the CSV or Excel file",
        examples=["./data/example.csv", "./data/example.txt", "./data/example.xlsx"],
    )

    def get_urls(self) -> list[str]:
        if not self.path:
            input_path = console.input("Please provide the path to the CSV or Excel file: ")
        else:
            input_path = self.path
        filepath = Path(input_path)
        try:
            data = pd.read_csv(filepath.as_posix())
        except UnicodeDecodeError:
            data = pd.read_excel(filepath.as_posix())
        urls = data["url"].to_numpy().tolist()
        return urls

    async def _get_names(self, url: str) -> TitleParser:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url=url)
                soup = BeautifulSoup(response.text, "html.parser")
                h1_text = soup.find("h1").text
        except Exception:
            h1_text = "Error"
        url_name_dict = TitleParser(title=h1_text, url=url)
        await asyncio.sleep(secrets.randbelow(3))
        return url_name_dict

    def get_videos(self) -> None:
        tdl = TDLManager(output_path="./data/tmp")
        urls = self.get_urls()
        try:
            tdl.download(urls=urls)
        except RuntimeError:
            logfire.info("You need to login to your Telegram account.")
            logfire.info("Please run `tdl login` in first.")
            # tdl.login()
            # tdl.download(urls=urls)

    async def get_names(self) -> list[TitleParser]:
        urls = self.get_urls()
        semaphore = asyncio.Semaphore(5)  # 控制同時執行的任務數量
        results = []

        async def sem_task(url: str) -> TitleParser:
            async with semaphore:  # 確保同時最多有 5 個任務執行
                return await self._get_names(url)

        with Progress() as progress:
            # 添加進度條
            task_id = progress.add_task("[cyan]Fetching URLs...", total=len(urls))

            async def wrapped_task(url: str) -> TitleParser:
                result = await sem_task(url)
                progress.update(task_id, advance=1, description=result.title)
                return result

            # gather 所有任務
            results = await asyncio.gather(*(wrapped_task(url) for url in urls))

        return results


if __name__ == "__main__":
    import fire

    fire.Fire(TelegramDownloader)
