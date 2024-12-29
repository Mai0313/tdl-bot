import re
from pathlib import Path
import platform
import subprocess

import logfire
from pydantic import Field, BaseModel, computed_field, model_validator
from rich.console import Console

logfire.configure(send_to_logfire=False)
console = Console()

ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub("", text)


class TDLManager(BaseModel):
    output_path: Path = Field(
        default=Path("./data/tmp"),
        description="The output directory for the downloaded files; same with `--dir`.",
    )

    @model_validator(mode="after")
    def _setup(self) -> "TDLManager":
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

    def login(self) -> None:
        if platform.system() == "Windows":
            command = [self.tdl, "login", "--type", "desktop"]
        else:
            command = [self.tdl, "login", "--type", "qr"]

        try:
            with subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                shell=False,
            ) as proc:
                if proc.stdout is None:
                    return

                logged_in = False
                while True:
                    output = proc.stdout.readline()
                    console.print(output.strip())
                    if output == "" and proc.poll() is not None:
                        break
                    # 偵測是否登錄成功的提示（根據實際輸出內容修改）
                    if "Login successfully" in output:
                        logged_in = True
                        break

                if proc.stderr is not None:
                    error = proc.stderr.read()
                    if error:
                        logfire.error(f"Error during login: {error}")

                return_code = proc.wait()
                if return_code != 0 or not logged_in:
                    raise RuntimeError("Login failed or not completed.")
                logfire.info("Login completed successfully.")

        except Exception:
            logfire.error("An exception occurred during login", exc_info=True)
            raise

    def download(self, urls: list[str]) -> None:
        url_string = ",".join(urls)
        command = [self.tdl, "download", "--dir", self.output_path.as_posix(), "--url", url_string]

        try:
            with subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                shell=False,
            ) as proc:
                if proc.stdout is None:
                    return
                # for line in iter(proc.stdout.readline, ""):
                #     if line:
                #         cleaned_output = strip_ansi(line)
                #         console.print(cleaned_output)

                if proc.stderr is None:
                    return
                # for error_line in iter(proc.stderr.readline, ""):
                #     if error_line:
                #         cleaned_output = strip_ansi(error_line)
                #         console.print(f"ERROR: {cleaned_output}", flush=True)

                return_code = proc.wait()
                if return_code == 0:
                    logfire.info(f"Download completed successfully with exit code {return_code}")
                else:
                    raise RuntimeError(f"Download failed with exit code {return_code}")

        except RuntimeError as e:
            logfire.error(f"Runtime error during download: {e}")
            raise
        except Exception:
            logfire.error("An exception occurred during download", exc_info=True)
            raise
