from pathlib import Path
import platform
import subprocess

import logfire
from pydantic import Field, BaseModel, computed_field, model_validator

logfire.configure(send_to_logfire=False)


class TelegramDownloader(BaseModel):
    output_path: Path = Field(
        ...,
        description="The output directory for the downloaded files; same with `--dir`.",
        frozen=False,
        deprecated=False,
    )

    @model_validator(mode="after")
    def _setup(self) -> "TelegramDownloader":
        self.output_path.mkdir(parents=True, exist_ok=True)
        return self

    @computed_field
    @property
    def tdl(self) -> str:
        tdl = "./src/tdl/binaries/tdl"

        if platform.system() == "Windows":
            tdl = "./src/tdl/binaries/tdl.exe"

        elif platform.system() == "Linux":
            system_path = Path("./src/tdl/binaries/tdl").expanduser()
            if system_path.exists():
                tdl = "tdl"
        return tdl

    def download(self, urls: list[str]) -> None:
        url_string = ",".join(urls)
        command = [self.tdl, "download", "--dir", self.output_path.as_posix(), "--url", url_string]

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
