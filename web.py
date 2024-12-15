import gradio as gr
from src.tdl.processor import TDLManager


def greet(file_url: str, limit: int, pool: int, threads: int) -> str:
    td = TDLManager(
        func="download", serve=False, skip_same=True, limit=limit, pool=pool, threads=threads
    )
    td.run(url=file_url)
    return "downloads/1128501931_36835_调教漂亮反差小女友，捆绑绑手戴上口球，跳蛋玩弄无助的扭动，口交深喉，主动上位超用力淫叫_今天6.mp4"


demo = gr.Interface(fn=greet, inputs=["text", "slider", "slider", "slider"], outputs=[gr.Video()])

demo.launch()
