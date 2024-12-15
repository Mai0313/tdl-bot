from pathlib import Path

import gradio as gr
from src.tdl.processor import TDLManager


def greet(file_url: str, limit: int, pool: int, threads: int) -> str:
    td = TDLManager(
        func="download", serve=False, skip_same=True, limit=limit, pool=pool, threads=threads
    )
    td.run(url=file_url)
    output_path = Path("downloads")
    downloaded = (
        "downloads/" + sorted(output_path.iterdir(), key=lambda x: x.stat().st_ctime)[-1].name
    )
    return downloaded


demo = gr.Interface(fn=greet, inputs=["text", "slider", "slider", "slider"], outputs=[gr.Video()])

demo.launch()
