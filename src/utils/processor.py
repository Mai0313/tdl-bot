from pathlib import Path
import platform
import subprocess

import logfire
from pydantic import Field, BaseModel, computed_field


class DownloadProcessor(BaseModel):
    func: str = Field(
        default="download",
        description="The function to run",
        examples=["download"],
        pattern="download",
        # pattern="backup|login|migrate|recover|chat|download|forward|upload|completion|help|version",
    )
    serve: bool = Field(
        default=False, description="Serve the file instead of downloading it, same with `--serve`."
    )
    skip_same: bool = Field(
        default=False,
        description="Skip downloading if the file already exists; same with `--skip-same`.",
    )
    limit: int = Field(
        default=2, description="The number of files to download; same with `--limit`."
    )
    pool: int = Field(
        default=0, description="The number of concurrent downloads; same with `--pool`."
    )
    threads: int = Field(
        default=4, description="The number of threads to use; same with `--threads`."
    )

    @computed_field
    @property
    def tdl(self) -> str:
        tdl = "./binaries/tdl"

        if platform.system() == "Windows":
            tdl = "./binaries/tdl.exe"

        if platform.system() == "Linux":
            system_path = Path("~/.local/bin/tdl").expanduser()
            if system_path.exists():
                tdl = "tdl"
        return tdl

    @computed_field
    @property
    def compiled_command(self) -> list[str]:
        base_command = [self.tdl, self.func]
        if self.serve:
            base_command.append("--serve")
        if self.skip_same:
            base_command.append("--skip-same")
        if self.limit:
            base_command.extend(["--limit", str(self.limit)])
        if self.pool:
            base_command.extend(["--pool", str(self.pool)])
        if self.threads:
            base_command.extend(["--threads", str(self.threads)])
        return base_command

    def run(self, url: str) -> None:
        _command = self.compiled_command
        if url:
            _command.extend(["--url", url])
        try:
            result = subprocess.run(
                _command,
                check=True,
                capture_output=True,
                text=True,
                shell=isinstance(_command, str),
            )
            logfire.info(f"Command Output:\n{result.stdout}")
        except subprocess.CalledProcessError as e:
            logfire.error("Error:", error=e.stderr, command=_command, _exc_info=True)
