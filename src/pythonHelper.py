from pathlib import Path
import shutil
from src.command import Command
from sys import stderr
from typing import Optional
from src.config import Config
import subprocess
import os


def pythonHelper(config: Config) -> Optional[Command]:
    # Python helper is disabled (no version specified)
    if config.python.version is None:
        return

    retval = None

    # Copy the python build in AppDir
    cwd = os.getcwd()
    appDir = os.path.sep.join([cwd, 'AppDir', 'usr'])
    Path(appDir).mkdir(parents=True, exist_ok=True)
    dockerCmd = ['docker', 'run', '--rm', '--volume', f'{appDir}:/opt/out',
                 '--user', f'{os.geteuid()}:{os.getegid()}',
                 f'giacomofurlan/python-precompiled:v{config.python.version}', '/opt/out/']
    subprocess.run(dockerCmd)

    retval = Command(
        executable=os.path.sep.join([appDir, 'bin', 'python3']),
        args=[config.python.entryfile],
        env={
            'LD_LIBRARY_PATH': os.path.sep.join([appDir, 'lib']),
            'PYTHONPATH': os.path.sep.join([appDir, 'lib', f'python{config.python.version}', 'site-packages']),
        },
        copyExecutable=False,
        # Ensure that Python files are kept, nonetheless
        # (maybe include ony /usr/bin ones, and leave strace the job to filter out the others?)
        extraFilesToInclude=[str(file) for file in Path(
            appDir).glob('**/*') if file.is_file()],
    )

    # Generate the requirements.txt and install the requirements
    if config.python.pipenvInstall:
        env = [
            '--env', f'LD_LIBRARY_PATH=/opt/out/lib',
            '--env', f'HOME=/tmp',
        ]
        commands = [
            (['-m', 'ensurepip', '--upgrade'], None),
            (['-m', 'pip', 'install', '--upgrade', 'pip'], None),
            (['-m', 'pip', 'install', 'pipenv'], None),
            (['-m', 'pipenv', '--python', '/opt/out/bin/python3',
                'lock', '-r'], os.path.sep.join([cwd, 'requirements.txt'])),
        ]

        for command in commands:
            dockerCmd = [
                'docker', 'run', '--rm',
                '--volume', f'{appDir}:/opt/out', '--volume', f'{cwd}:/tmpapp',
                '--user', f'{os.geteuid()}:{os.getegid()}', *env,
                '--workdir', '/tmpapp', '--entrypoint', '/opt/out/bin/python3',
                f'giacomofurlan/python-precompiled:v{config.python.version}',
                *command[0],
            ]
            captureOutput = command[1] is not None
            result = subprocess.run(dockerCmd, capture_output=captureOutput)
            if captureOutput:
                print(result.stderr.decode('utf-8'), file=stderr)
                with open(command[1], 'w') as f:
                    print(result.stdout.decode('utf-8'), file=f)

    if config.python.pipInstall:
        dockerCmd = [
            'docker', 'run', '--rm',
            '--volume', f'{appDir}:/opt/out', '--volume', f'{cwd}:/tmpapp',
            '--user', f'{os.geteuid()}:{os.getegid()}', *env,
            '--workdir', '/tmpapp', '--entrypoint', '/opt/out/bin/python3',
            f'giacomofurlan/python-precompiled:v{config.python.version}',
            '-m', 'pip', 'install', '-r', 'requirements.txt',
        ]

        subprocess.run(dockerCmd)

    # Remove pycache folders
    # (is this necessary?)
    for folder in [file for file in Path(cwd).glob('**/__pycache__') if file.is_dir()]:
        shutil.rmtree(str(folder))

    pythonPath = [str(p)[len(appDir):]
                  for p in Path(appDir).glob('**/site-packages')]

    return retval
