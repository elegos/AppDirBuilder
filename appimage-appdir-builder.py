#!/usr/bin/env python3
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from copy import deepcopy
from pathlib import Path
from typing import List

from src.config import Config
from src.pythonHelper import pythonHelper
from src.utils import copyToAppDir, which

cwd = os.getcwd()
appDir = os.path.sep.join([cwd, 'AppDir'])
shutil.rmtree(appDir, ignore_errors=True)

configFilePath = os.path.sep.join([cwd, 'AppImageAppDirBuilder.ini'])
config = Config.defaultConfig()
if Path(configFilePath).is_file():
    config = Config.fromFile(configFilePath)


execCmd = pythonHelper(config)

if len(sys.argv) == 1 and execCmd is None:
    print('Usage:')
    print(f'{sys.argv[0]} app-to-execute arg1 argN')
    sys.exit(0)

print('Now use the application to read the dependencies with `strace`')

copyExec = True
extraFilesToKeep = []
exec = []
if execCmd is not None:
    exec = execCmd.cmd
    copyExec = execCmd.copyExecutable
    extraFilesToKeep.extend(execCmd.extraFilesToInclude)
else:
    exec = [sys.argv[1]]

envVars = deepcopy(dict(os.environ))
envVars.update(execCmd.env if execCmd is not None else {})
if not Path(exec[0]).is_absolute():
    exec[0] = which(exec[0])

straceCmdArgs = ['strace', *exec, *sys.argv[2:]]
# straceCmdArgs = ['/usr/bin/env']
envVars.update({
    # 'LD_DEBUG': 'libs',
    # 'QT_DEBUG_PLUGINS': '1'
})
completedProcess: subprocess.CompletedProcess = subprocess.run(
    straceCmdArgs, capture_output=True, env=envVars)

# print(completedProcess.stderr.decode('utf-8'), sys.stderr)

filePathRegex = re.compile('"([^"]+)"')
straceOutput = completedProcess.stderr.decode('utf-8').split('\n')
straceOutput = [line for line in straceOutput if 'openat' in line]
straceOutput = [filePathRegex.search(line)[1] for line in straceOutput]

# Remove non-existing files
straceOutput = [line for line in straceOutput if Path(line).is_file()]

filesAlreadyInAppDir = [
    line for line in straceOutput if line.startswith(appDir)]
straceOutput = [line for line in straceOutput if not line.startswith(appDir)]


excludeList: List[re.Pattern] = [
    # /home/<user
    re.compile('^\/home\/[^/]+\/\.'),
    re.compile('\.so\.cache$'),
    re.compile('\.ids$'),
    re.compile('^\/(etc|dev|dri|proc|run|sys|var)\/'),
    re.compile('\/(drirc)'),
    re.compile('\/share\/(fonts|icons|locale|kde-settings|mime)\/?'),
    re.compile('\/share\/X11\/(fonts|locale)\/?'),
    re.compile('\/lib(64)?\/locale\/'),
    re.compile('\/(lib|share)\/fontconfig\/'),
    re.compile('\/nsswitch\.conf$'),
]
for regex in excludeList:
    straceOutput = [
        line for line in straceOutput if regex.search(line) is None]

# Remove duplicates
straceOutput = list(set(straceOutput))

# Exclude list from pkg2appimage
with urllib.request.urlopen('https://raw.githubusercontent.com/AppImage/pkg2appimage/master/excludelist') as response:
    excludeList = response.read().decode('utf-8').split('\n')
    excludeList = [line.split('#')[0].strip() for line in excludeList if line !=
                   '' and not line.startswith('#')]

    for excluded in excludeList:
        straceOutput = [
            line for line in straceOutput if not line.endswith(f'/{excluded}')]

print(f'- {len(straceOutput)} accessed files (without blacklist)')

appFiles = [line for line in straceOutput if line.startswith(cwd)]
otherFiles = [line for line in straceOutput if not line.startswith(cwd)]


print('')
print(f'- {len(appFiles)} files added to /app')
copiedAppFiles = copyToAppDir(appDir=appDir, filesList=appFiles, destPrefix='/app',
                              absRenamer=lambda x: x[len(cwd):])

print(f'- {len(otherFiles)} files added to /')
copiedOtherFiles = copyToAppDir(appDir=appDir, filesList=otherFiles)

# Remove unused files
filesToKeep = [*filesAlreadyInAppDir, *copiedAppFiles,
               *copiedOtherFiles, *extraFilesToKeep]
# Files that have to be ignored
filesToKeep = [file for file in filesToKeep if os.path.basename(
    file) not in config.files.exclude]
filesInAppDir = list(Path(appDir).glob('**/*'))
for file in filesInAppDir:
    if file.is_dir():
        continue
    if str(file) not in filesToKeep:
        file.unlink()

# Copy the executable itself
if copyExec:
    if Path(exec[0]).is_absolute():
        exec = which(exec)

    copyToAppDir(
        appDir=appDir,
        filesList=[exec],
        destPrefix='/app/',
        absRenamer=lambda x: os.path.basename(x)
    )
