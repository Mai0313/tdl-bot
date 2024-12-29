from pathlib import Path

import gradio as gr

from tdl.processor import TDLManager


def tdl_download(file_url: str) -> str:
    # 使用自定義下載邏輯
    file_urls = file_url.split("\n")
    td = TDLManager(output_path="./data/tmp")
    td.download(urls=file_urls)

    return "下載完成"


def preview_file(file_path: str) -> tuple[bool, bool]:
    # 預覽檔案的處理邏輯
    file_extension = Path(file_path).suffix.lower()
    if file_extension in [".mp4", ".mov", ".avi"]:
        return gr.update(value=file_path, visible=True), gr.update(visible=False)
    if file_extension in [".png", ".jpg", ".jpeg", ".gif"]:
        return gr.update(visible=False), gr.update(value=file_path, visible=True)
    return gr.update(visible=False), gr.update(visible=False)


with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            gr.Markdown("**請輸入要下載的檔案網址（支援多行）**")
            file_urls_input = gr.Code(language="python", label="輸入下載的網址")
            download_button = gr.Button("下載")
            download_status = gr.Textbox(label="下載狀態", interactive=False)
        with gr.Column():
            gr.Markdown("**檔案瀏覽與預覽**")
            file_explorer = gr.FileExplorer(
                root_dir="./data/tmp", label="檔案瀏覽器", file_count="single"
            )
            video_preview = gr.Video(visible=False)
            image_preview = gr.Image(visible=False)

    download_button.click(fn=tdl_download, inputs=file_urls_input, outputs=download_status)

    file_explorer.change(
        fn=preview_file, inputs=file_explorer, outputs=[video_preview, image_preview]
    )

demo.launch()
