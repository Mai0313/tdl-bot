from pathlib import Path
import platform
import subprocess

import logfire
from pydantic import Field, BaseModel, computed_field, model_validator

logfire.configure(send_to_logfire=False)


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
            result = subprocess.run(  # noqa: S603
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                shell=isinstance(command, str),
            )
            logfire.info(f"Command Output:\n{result.stdout}", status_code=result.returncode)
        except subprocess.CalledProcessError as e:
            logfire.error("Error:", error=e.stderr, command=command, _exc_info=True)

    def download(self, urls: list[str]) -> None:
        url_string = ",".join(urls)
        command = [self.tdl, "download", "--dir", self.output_path.as_posix(), "--url", url_string]
        try:
            result = subprocess.run(  # noqa: S603
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                shell=isinstance(command, str),
            )
            logfire.info(f"Command Output:\n{result.stdout}", status_code=result.returncode)
        except subprocess.CalledProcessError as e:
            logfire.error("Error:", error=e.stderr, command=command, _exc_info=True)
