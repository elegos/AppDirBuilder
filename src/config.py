import configparser
from dataclasses import dataclass
from typing import Any, List, Optional

_defaultConfigDict = {
    'Files': {
        'exclude': '',
        'include': '',
        'patchHardCodedBinaryPaths': 'false',
    },
    'Python': {
        'version': '',
        'runWithPython': '',
        'pythonPath': '',
        'pipenvInstall': '',
        'pipInstall': '',
        'entryfile': '',
    },
    'Runtime': {
        'uuid': '',
        'reverseDNS': '',
        'execPath': '',
        'execArgs': '$@',
        'libraryPath': '$APPDIR/usr/lib:$APPDIR/lib64',
    },
    'Desktop Entry': {
        'X-AppImage-Arch': 'x86_64',
        'X-AppImage-Version': 'latest',
        'X-AppImage-Name': '',
        'Name': '',
        'Exec': '',
        'Icon': '',
        'Type': 'Application',
        'Terminal': '',
        'Categories': 'Utility',
        'Comment': '',
    },
    'Icon': {
        'sourcePath': '',
    }
}


class DesktopEntry:
    reverseDNS: str
    _section: configparser.SectionProxy

    def __init__(self, reverseDNS: str, section: configparser.SectionProxy) -> None:
        self.reverseDNS = reverseDNS
        self._section = section

    def toEntry(self) -> str:
        result = ['[Desktop Entry]']
        for key, value in self._section.items():
            if key == 'Exec' and ' ' in value:
                value = f'sh -c "{value}"'
            value = value.replace('$', '\\\$')
            result.append(f'{key}={value}')

        return '\n'.join(result)

    @property
    def fileName(self) -> str:
        return f'{self.reverseDNS}.desktop'

    def __getitem__(self, name: str) -> Any:
        if name in self._section.keys():
            return self._section[name]

        return None


@dataclass
class Runtime:
    uuid: str
    reverseDNS: str
    execPath: str
    execArgs: str
    libraryPath: str

    @staticmethod
    def fromSection(section: configparser.SectionProxy) -> 'Runtime':
        return Runtime(
            uuid=section['uuid'],
            reverseDNS=section['reverseDNS'],
            execPath=section['execPath'],
            execArgs=section['execArgs'],
            libraryPath=section['libraryPath'],
        )


@dataclass
class FilesConfig:
    patchHardCodedBinaryPaths: bool
    exclude: List[str]
    include: List[str]

    @staticmethod
    def fromSection(section: configparser.SectionProxy) -> 'FilesConfig':
        return FilesConfig(
            patchHardCodedBinaryPaths=True if section['patchHardCodedBinaryPaths'].lower(
            ) == 'true' else False,
            exclude=[line.strip() for line in section['exclude'].split(
                '\n') if line.strip() != ''],
            include=[line.strip() for line in section['include'].split(
                '\n') if line.strip() != ''],
        )


@dataclass
class PythonConfig:
    version: Optional[str]
    runWithPython: Optional[str]
    pythonPath: Optional[str]
    entryfile: Optional[str]
    pipenvInstall: bool
    pipInstall: bool

    @staticmethod
    def fromSection(section: configparser.SectionProxy) -> 'PythonConfig':
        return PythonConfig(
            version=section['version'] if section['version'] != '' else None,
            runWithPython=section['runWithPython'] if section['runWithPython'] != '' else None,
            pythonPath=section['pythonPath'] if section['pythonPath'] != '' else None,
            entryfile=section['entryfile'] if section['entryfile'] != '' else None,
            pipenvInstall=True if section['pipenvInstall'].lower(
            ) == 'true' else False,
            pipInstall=True if section['pipInstall'].lower(
            ) == 'true' else False,
        )


@dataclass
class Icon:
    sourcePath: str

    @staticmethod
    def fromSection(section: configparser.SectionProxy) -> 'Icon':
        return Icon(sourcePath=section['sourcePath'])


@dataclass
class Config:
    files: FilesConfig
    python: PythonConfig
    runtime: Runtime
    desktopEntry: DesktopEntry
    icon: Icon

    @staticmethod
    def defaultConfig() -> 'Config':
        parser = configparser.ConfigParser()
        parser.optionxform = str
        for key, values in _defaultConfigDict.items():
            parser[key] = values

        return Config(
            files=FilesConfig.fromSection(parser['Files']),
            python=PythonConfig.fromSection(parser['Python']),
            runtime=Runtime.fromSection(parser['Runtime']),
            desktopEntry=DesktopEntry(
                reverseDNS='', section=parser['Desktop Entry']),
            icon=Icon.fromSection(parser['Icon']),
        )

    @ staticmethod
    def fromFile(path: str) -> 'Config':
        parser = configparser.ConfigParser()
        parser.optionxform = str
        for key, values in _defaultConfigDict.items():
            parser[key] = values

        parser.read(path)
        runtime = Runtime.fromSection(parser['Runtime'])
        return Config(
            files=FilesConfig.fromSection(parser['Files']),
            python=PythonConfig.fromSection(parser['Python']),
            runtime=runtime,
            desktopEntry=DesktopEntry(
                runtime.reverseDNS, parser['Desktop Entry']),
            icon=Icon.fromSection(parser['Icon']),
        )
