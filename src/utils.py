import os
import shutil
from pathlib import Path
from typing import Callable, List


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
