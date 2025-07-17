from enum import Enum
import asyncio
from pathlib import Path
from datetime import timedelta
import platform

import logfire
from pydantic import Field, BaseModel, computed_field, model_validator

logfire.configure(send_to_logfire=False)


class StorageDriver(str, Enum):
    """Available storage drivers for TDL."""

    LEGACY = "legacy"
    BOLT = "bolt"
    FILE = "file"


class TDLCommand(str, Enum):
    """Available TDL commands."""

    # Account related
    BACKUP = "backup"
    LOGIN = "login"
    MIGRATE = "migrate"
    RECOVER = "recover"

    # Tools
    CHAT = "chat"
    DOWNLOAD = "download"
    EXTENSION = "extension"
    FORWARD = "forward"
    UPLOAD = "upload"

    # Additional commands
    COMPLETION = "completion"
    VERSION = "version"


class TDLResult(BaseModel):
    """Result of TDL command execution."""

    success: bool = Field(..., description="Whether the command executed successfully")
    return_code: int = Field(..., description="Process return code")
    stdout: str = Field(default="", description="Standard output from the command")
    stderr: str = Field(default="", description="Standard error from the command")
    command: list[str] = Field(..., description="The executed command")


class TDLConfig(BaseModel):
    """Configuration for TDL processor."""

    debug: bool = Field(default=False, description="Enable debug mode")
    delay: timedelta | None = Field(default=None, description="Delay between each task")
    limit: int = Field(default=2, description="Max number of concurrent tasks")
    namespace: str = Field(default="default", description="Namespace for Telegram session")
    ntp: str | None = Field(default=None, description="NTP server host")
    pool: int = Field(default=8, description="Size of the DC pool, zero means infinity")
    proxy: str | None = Field(
        default=None, description="Proxy address, format: protocol://username:password@host:port"
    )
    reconnect_timeout: timedelta = Field(
        default=timedelta(minutes=5), description="Telegram client reconnection backoff timeout"
    )
    storage: dict[str, str] = Field(
        default_factory=lambda: {"type": "bolt", "path": f"{Path.home()}/.tdl/data"},
        description="Storage options",
    )
    threads: int = Field(default=4, description="Max threads for transfer one item")


class TelegramDownloader(BaseModel):
    """Enhanced Telegram Downloader with full TDL CLI support."""

    output_folder: Path = Field(..., description="The output directory for the downloaded files")
    config: TDLConfig = Field(default_factory=TDLConfig, description="TDL configuration options")

    @model_validator(mode="after")
    def _setup(self) -> "TelegramDownloader":
        """Setup the output folder."""
        self.output_folder.mkdir(parents=True, exist_ok=True)
        return self

    @computed_field
    @property
    def tdl_binary(self) -> str:
        """Get the path to TDL binary based on platform."""
        binary_name = "tdl.exe" if platform.system() == "Windows" else "tdl"
        tdl_path = Path(__file__).parent / "binaries" / binary_name
        return tdl_path.absolute().as_posix()

    def _build_base_command(self) -> list[str]:
        """Build the base command with global flags."""
        command = [self.tdl_binary]

        if self.config.debug:
            command.append("--debug")

        if self.config.delay:
            command.extend(["--delay", str(int(self.config.delay.total_seconds()))])

        command.extend(["--limit", str(self.config.limit)])
        command.extend(["--ns", self.config.namespace])

        if self.config.ntp:
            command.extend(["--ntp", self.config.ntp])

        command.extend(["--pool", str(self.config.pool)])

        if self.config.proxy:
            command.extend(["--proxy", self.config.proxy])

        command.extend([
            "--reconnect-timeout",
            str(int(self.config.reconnect_timeout.total_seconds())),
        ])

        # Build storage options
        storage_str = ",".join([f"{k}={v}" for k, v in self.config.storage.items()])
        command.extend(["--storage", storage_str])

        command.extend(["--threads", str(self.config.threads)])

        return command

    async def _execute_command(
        self, command: list[str], timeout: float | None = None
    ) -> TDLResult:
        """Execute TDL command asynchronously."""
        try:
            logfire.info(f"Executing command: {' '.join(command)}")

            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

            return TDLResult(
                success=process.returncode == 0,
                return_code=process.returncode or 0,
                stdout=stdout.decode("utf-8") if stdout else "",
                stderr=stderr.decode("utf-8") if stderr else "",
                command=command,
            )

        except asyncio.TimeoutError:
            logfire.error(f"Command timed out: {' '.join(command)}")
            return TDLResult(
                success=False, return_code=-1, stderr="Command timed out", command=command
            )
        except Exception as e:
            logfire.error(f"Command execution failed: {e}", exc_info=True)
            return TDLResult(success=False, return_code=-1, stderr=str(e), command=command)

    # Account related methods
    async def login(self) -> TDLResult:
        """Login to Telegram."""
        command = [*self._build_base_command(), TDLCommand.LOGIN]
        return await self._execute_command(command)

    async def backup(self, destination: str | None = None) -> TDLResult:
        """Backup your data."""
        command = [*self._build_base_command(), TDLCommand.BACKUP]
        if destination:
            command.extend(["--dest", destination])
        return await self._execute_command(command)

    async def migrate(self, from_storage: str, to_storage: str) -> TDLResult:
        """Migrate your current data to another storage."""
        command = [
            *self._build_base_command(),
            TDLCommand.MIGRATE,
            "--from",
            from_storage,
            "--to",
            to_storage,
        ]
        return await self._execute_command(command)

    async def recover(self, source: str) -> TDLResult:
        """Recover your data."""
        command = [*self._build_base_command(), TDLCommand.RECOVER, "--source", source]
        return await self._execute_command(command)

    # Tools methods
    async def download(
        self,
        urls: list[str] | str,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        restart: bool = False,
        skip_same: bool = False,
    ) -> TDLResult:
        """Download anything from Telegram (protected) chat."""
        if isinstance(urls, list):
            urls = ",".join(urls)

        command = [
            *self._build_base_command(),
            TDLCommand.DOWNLOAD,
            "--dir",
            self.output_folder.as_posix(),
            "--url",
            urls,
        ]

        if include:
            command.extend(["--include", ",".join(include)])

        if exclude:
            command.extend(["--exclude", ",".join(exclude)])

        if restart:
            command.append("--restart")

        if skip_same:
            command.append("--skip-same")

        return await self._execute_command(command, timeout=3600)  # 1 hour timeout

    async def upload(self, path: str, to: str, remove_after: bool = False) -> TDLResult:
        """Upload anything to Telegram."""
        command = [*self._build_base_command(), TDLCommand.UPLOAD, "--path", path, "--to", to]

        if remove_after:
            command.append("--rm")

        return await self._execute_command(command, timeout=3600)  # 1 hour timeout

    async def forward(
        self, from_chat: str, to_chat: str, filter_text: str | None = None
    ) -> TDLResult:
        """Forward messages with automatic fallback and message routing."""
        command = [
            *self._build_base_command(),
            TDLCommand.FORWARD,
            "--from",
            from_chat,
            "--to",
            to_chat,
        ]

        if filter_text:
            command.extend(["--filter", filter_text])

        return await self._execute_command(command)

    # Chat tools
    async def chat_list(self) -> TDLResult:
        """List all chats."""
        command = [*self._build_base_command(), TDLCommand.CHAT, "ls"]
        return await self._execute_command(command)

    async def chat_export(self, chat: str, output: str | None = None) -> TDLResult:
        """Export chat messages."""
        command = [*self._build_base_command(), TDLCommand.CHAT, "export", "--chat", chat]

        if output:
            command.extend(["--output", output])

        return await self._execute_command(command, timeout=3600)  # 1 hour timeout

    # Extension management
    async def extension_list(self) -> TDLResult:
        """List installed extensions."""
        command = [*self._build_base_command(), TDLCommand.EXTENSION, "ls"]
        return await self._execute_command(command)

    async def extension_install(self, extension: str) -> TDLResult:
        """Install an extension."""
        command = [*self._build_base_command(), TDLCommand.EXTENSION, "install", extension]
        return await self._execute_command(command)

    async def extension_remove(self, extension: str) -> TDLResult:
        """Remove an extension."""
        command = [*self._build_base_command(), TDLCommand.EXTENSION, "rm", extension]
        return await self._execute_command(command)

    # Utility methods
    async def get_version(self) -> TDLResult:
        """Get TDL version information."""
        command = [*self._build_base_command(), TDLCommand.VERSION]
        return await self._execute_command(command)

    async def generate_completion(self, shell: str) -> TDLResult:
        """Generate autocompletion script for specified shell."""
        command = [*self._build_base_command(), TDLCommand.COMPLETION, shell]
        return await self._execute_command(command)
