#!/usr/bin/env bash

set -e
set -x

mypy src/extract_favicon
ruff check src/extract_favicon
