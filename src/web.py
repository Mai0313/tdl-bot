from pathlib import Path

import gradio as gr

from tdl.processor import TDLManager


def tdl_download(file_url: str) -> str:
    file_urls = file_url.split("\n")
    for file_url in file_urls:
        td = TDLManager(func="download", serve=False, skip_same=True, limit=4, pool=0, threads=8)
        td.run(url=file_url)
    output_path = Path("downloads")
    downloaded = (
        "downloads/" + sorted(output_path.iterdir(), key=lambda x: x.stat().st_ctime)[-1].name
    )
    return downloaded


demo = gr.Interface(fn=tdl_download, inputs=["code"], outputs=[gr.Video()])

demo.launch()
