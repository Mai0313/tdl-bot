from pathlib import Path
import platform
import subprocess

import logfire
from pydantic import Field, BaseModel, computed_field, model_validator

logfire.configure(send_to_logfire=False)


class TelegramDownloader(BaseModel):
    output_folder: Path = Field(
        ...,
        description="The output directory for the downloaded files; same with `--dir`.",
        frozen=False,
        deprecated=False,
    )

    @model_validator(mode="after")
    def _setup(self) -> "TelegramDownloader":
        self.output_folder.mkdir(parents=True, exist_ok=True)
        return self

    @computed_field
    @property
    def tdl(self) -> str:
        tdl = Path("./src/core/binaries/tdl").expanduser()
        if platform.system() == "Windows":
            tdl = Path("./src/core/binaries/tdl.exe").expanduser()
        return tdl.absolute().as_posix()

    def download(self, urls: list[str] | str) -> None:
        urls = ",".join(urls) if isinstance(urls, list) else urls
        command = [self.tdl, "download", "--dir", self.output_folder.as_posix(), "--url", urls]

        try:
            with subprocess.Popen(  # noqa: S603
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                shell=False,
            ) as proc:
                if proc.stdout is None or proc.stderr is None:
                    return
                return_code = proc.wait()
                if return_code == 0:
                    logfire.info(f"Download completed successfully with exit code {return_code}")
                    return
                logfire.error(f"Download failed with exit code {return_code}", _exc_info=True)
                return

        except Exception:
            logfire.error("An exception occurred during download", _exc_info=True)
            return
