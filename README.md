# AppDir builder
As simple as possible AppDir builder for AppImage.

## How it works
The aim of this tool is to provide the smallest footprint in terms of size. This is achieved by
running the application with `strace`, which keeps track of all the files that are being opened
within the "test execution". This execution is done during the build process and requires the
developer to use as much as possible the application. It is not strictly required to execute all
the functions, but the more you use, the less likely you'll have to manually add entries in the
ini file.

When the `strace` step is done, a list of files being opened by the application will be used to
track the only files required by the application, thus not copying the ones not being used.

For example this allows a smaller footprint when using the PyQt libraries, as it will automatically
pick the only ones used by the application.

## Usage

### AppDirBuilder.ini
The project must have an `AppDirBuilder.ini` file in its root.

```ini
[File Info]; unrelated, just to know what this file belongs to
ConfigFor=AppDirBuilder - https://github.com/elegos/AppDirBuilder

[Runtime]; $APPDIR will be resolved to where the AppDir will be mounted
uuid=unique-uuid-here-please-forreal
reverseDNS=com.github.user.project
execPath=$APPDIR/usr/bin/myexe
execArgs=$@ ; $@ will pass any argument passed to the AppImage executable
; Example for Python (see Python helper section for more info)
; execPath=$APPDIR/usr/bin/python3.9
; execArgs=/app/main.py $@
libraryPath=$APPDIR/usr/lib:$APPDIR/lib64 ; or alike... depends on the host where the AppDir is being built

[Files]
patchHardCodedBinaryPaths=true ; Patch the binary file (Runtime.execPath). See https://docs.appimage.org/packaging-guide/manual.html#no-hard-coded-paths
exclude= ; list of file names that have to be excluded
  file1.ext
  file2.ext
  file3.ext
include= ; list of partial paths or file names that have to be included. It has the precedence over exclude.
  site-packages/botocore/
  mysecretfile.wtf

[Icon]
sourcePath=relative/path/to/file.svg ; use svg files. Relative to the root of the project.

[Desktop Entry]
Name=MyCoolApp
Exec=usr/bin/mycoolapp ; relative to the root of the project
Icon=mycoolapp
Type=Application
Categories=Utility;

X-AppImage-Arch=x86_64
X-AppImage-Version=latest
X-AppImage-Name=MyCoolApp
Terminal=false

; You can add all the desktop entry settings you wish 

[Python] ; for python applications only
version=3.9 ; for a list of available versions, see https://hub.docker.com/r/giacomofurlan/python-precompiled/tags?page=1&ordering=last_updated
runWithPython=usr/bin/python3 ; usually this path
entryfile=main.py ; relative path to the python entry file
pipenvInstall=True ; if true, use pip to install pipenv. If no requirements.txt is present, generate one with it.
pipInstall=True ; if true, use pip to install the required dependencies.

```

### Execution
```bash
cd your_project
python $PATH_TO_APPDIR_BUILDER/appdir-builder.py
```

An `AppDir` folder will be created, ready to be processed by appimagetool
