from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Command:
    executable: str
    args: List[str] = field(default_factory=lambda: [])
    env: Dict[str, str] = field(default_factory=lambda: {})
    copyExecutable: bool = field(default=True)
    extraEnvVars: Dict[str, str] = field(default_factory=lambda: {})
    extraFilesToInclude: List[str] = field(default_factory=lambda: [])

    @property
    def cmd(self) -> List[str]:
        return [self.executable, *self.args]
