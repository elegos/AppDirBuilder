import os
import shutil
from pathlib import Path
from src.config import Config
from typing import Callable, Dict, List


def copyToAppDir(filesList: List[str], appDir: str, destPrefix: str = '', absRenamer: Callable[[str], str] = lambda x: x) -> List[str]:
    Path(appDir).mkdir(exist_ok=True)

    result = []
    prefix = f'{appDir}{destPrefix}'
    for file in filesList:
        destPath = f'{prefix}{absRenamer(file)}'
        destDir = os.path.dirname(destPath)

        Path(destDir).mkdir(exist_ok=True, parents=True)
        shutil.copy(file, destPath)

        result.append(destPath)

    return result


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def patchBinary(binaryPath: str) -> None:
    '''
    Unconditionally patches a binary to remove hard links to /usr
    See https://docs.appimage.org/packaging-guide/manual.html#no-hard-coded-paths
    '''
    data = b''
    with open(binaryPath, 'rb') as binFile:
        data = binFile.read()

    data = data.replace(b'/usr', b'././')
    with open(binaryPath, 'wb') as binFile:
        binFile.write(data)


def writeDesktopEntry(config: Config, destDir: str) -> None:
    print('Writing desktop entry')
    destPath = os.path.sep.join([destDir, config.desktopEntry.fileName])
    with open(destPath, 'w') as file:
        file.write(config.desktopEntry.toEntry())


def writeAppRun(config: Config, destDir: str, extraEnvVars: Dict[str, str] = {}) -> None:
    appRunPath = os.path.sep.join([destDir, 'AppRun'])

    if Path(appRunPath).is_file():
        os.chmod(appRunPath, 0o755)
        return

    print('Writing AppRun')
    curFileDir = os.path.dirname(os.path.realpath(__file__))
    tplPath = os.path.sep.join(
        [curFileDir, 'AppRun.tpl'])
    with open(tplPath, 'r') as tplFile:
        tpl = tplFile.read() \
            .replace('{{LD_LIBRARY_PATH}}', config.runtime.libraryPath) \
            .replace('{{EXEC}}', config.runtime.execPath) \
            .replace('{{EXEC_ARGS}}', config.runtime.execArgs) \
            .replace('{{EXTRA_ENV_VARS}}', '\n'.join([f'export {key}="{value}"' for key, value in extraEnvVars.items()]))

        with open(appRunPath, 'w') as appRunFile:
            appRunFile.write(tpl)

    os.chmod(appRunPath, 0o755)
