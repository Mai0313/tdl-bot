import asyncio
from pathlib import Path
import secrets

from bs4 import BeautifulSoup
import httpx
import pandas as pd
import logfire
from pydantic import Field, BaseModel
from rich.console import Console
from rich.progress import TaskID, Progress
from fake_useragent import UserAgent

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

    async def _get_names(self, url: str) -> dict[str, str]:
        ua = UserAgent()  # 用於生成隨機 User-Agent
        headers = {
            "User-Agent": ua.random,  # 隨機生成 User-Agent
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        try:
            async with httpx.AsyncClient(headers=headers, timeout=10) as client:
                # 添加隨機延遲模仿真實用戶行為
                await asyncio.sleep(secrets.randbelow(3))

                # 發送請求
                response = await client.get(url=url)

                # 模擬通過簡單的反爬機制（如網站需要的 Cookies）
                if "captcha" in response.text.lower():
                    raise Exception("Blocked by captcha")

                soup = BeautifulSoup(response.text, "html.parser")
                h1_text = soup.find("h1").text if soup.find("h1") else "No Title Found"
                logfire.info("Title has been retrieved successfully", title=h1_text, url=url)
        except Exception as e:
            logfire.error(f"Failed to get the title of the URL: {e!s}", url=url)
            h1_text = "Error"

        url_name_dict = {"title": h1_text, "url": url}
        return url_name_dict

    async def _fetch_with_semaphore(
        self, url: str, progress: Progress, task_id: TaskID
    ) -> dict[str, str]:
        async with self.semaphore:
            result = await self._get_names(url)
            progress.update(task_id, advance=1)
            return result

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

    async def get_names(self) -> list[dict[str, str]]:
        urls = self.get_urls()
        semaphore = asyncio.Semaphore(5)  # 控制同時執行的任務數量
        results = []

        async def sem_task(url: str) -> dict[str, str]:
            async with semaphore:  # 確保同時最多有 5 個任務執行
                return await self._get_names(url)

        with Progress() as progress:
            # 添加進度條
            task_id = progress.add_task("[cyan]Fetching URLs...", total=len(urls))

            async def wrapped_task(url: str) -> dict[str, str]:
                result = await sem_task(url)
                progress.update(task_id, advance=1)  # 每完成一個任務進度條前進
                return result

            # gather 所有任務
            results = await asyncio.gather(*(wrapped_task(url) for url in urls))

        return results


if __name__ == "__main__":
    import fire

    fire.Fire(TelegramDownloader)
