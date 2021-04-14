#!/usr/bin/env bash

APPDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$APPDIR"

export LD_LIBRARY_PATH={{LD_LIBRARY_PATH}}
{{EXTRA_ENV_VARS}}
{{EXEC}} {{EXEC_ARGS}}
