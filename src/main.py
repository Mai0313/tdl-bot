import pandas as pd

from tdl.processor import TDLManager


def get_urls(path: str) -> list[str]:
    data = pd.read_csv(path)
    # 型態是 Dataframe
    # 但我們需要透過 `.values` 轉換成 `list` 來迴圈
    urls = data["url"].values.tolist()
    return urls

def get_videos(urls: list[str]) -> None:
    tdl = TDLManager(
        func="download",
        serve=False,
        skip_same=True,
        limit=4,
        pool=0,
        threads=8,
        output_path="./data",
    )

    tdl.run(urls=urls)


if __name__ == "__main__":
    urls = get_urls("./data/example.csv")
    get_videos(urls)
