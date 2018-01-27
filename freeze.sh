#!/bin/bash

cd $(dirname "$0") || exit

# ベースバージョンを取得
if [ ! -e base_version.txt ]; then
  python_version=$(pyenv version | awk '{print $1}')
  base_version=$(pyenv versions --bare | grep /${python_version}$ | awk -F\/ '{print $1}')
  echo ${base_version} > base_version.txt
fi

# モジュール構成を出力
pyenv exec pip freeze > requirements.txt
