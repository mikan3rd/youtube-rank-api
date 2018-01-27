#!/bin/bash

cd $(dirname "$0") || exit

function exists_python_version() {
    local version="$1"
    exists="$(pyenv versions --bare | grep -c "^${version}$")"
    [ "${exists}" -gt 0 ] && echo true || echo false
}

function can_install_python_version() {
    local version="$1"
    exists="$(pyenv install --list --bare | awk '{print $1}' | grep -c "^${version}$")"
    [ "${exists}" -gt 0 ] && echo true || echo false
}

function is_installed_pyenv() {
    pyenv -h > /dev/null 2>&1
    [ $? -eq 0 ] && echo true || echo false
}

function is_installed_virtualenv() {
    pyenv virtualenv -h > /dev/null 2>&1
    [ $? -eq 0 ] && echo true || echo false
}

function install_virtualenv() {
    git clone https://github.com/yyuu/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv
    echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bash_profile
    source ~/.bash_profile
}

if ! $(is_installed_pyenv); then
    echo "pyenvが利用できないため環境構築中止"
    exit 1
fi

if [ ! -e "python-version" ]; then
    echo "Pythonバージョン情報 python-version が存在しません"
    exit 1
fi

base_version="$(cat "base_version.txt")"
python_version="$(cat "python-version")"

if [ "${base_version}" == "${python_version}" ]; then
    echo "Pythonのベースバージョンと仮想環境名が同一です"
    exit 1
fi

echo
echo "Python環境セットアップ情報"
echo "----------------------------------------------------------------------"
echo "Base Version: ${base_version}"
echo "Venv Version: ${python_version}"
echo

if ! $(exists_python_version "${python_version}"); then
    # 実行環境バージョンが存在しない場合、環境を準備する

    if ! $(is_installed_virtualenv); then
        install_virtualenv

        if ! $(is_installed_virtualenv); then
            # pyenv virtualenvが利用できない場合、終了
            echo "pyenv用のvirtualenvが利用できません"
            exit 1
        fi
    fi

    if ! $(exists_python_version "${base_version}"); then
        # ベースとなる環境が存在しない場合、環境を準備する

        # pyenvを最新版に更新
        pushd ~/.pyenv > /dev/null
        git pull
        popd > /dev/null

        if ! $(can_install_python_version "${base_version}"); then
            # 指定されたバージョンのPythonが利用できない場合、終了する
            echo "指定されたPythonバージョンは利用できません: ${base_version}"
            exit 1
        fi

        # ベースバージョンのインストール
        pyenv install "${base_version}"
    fi

    # 実行環境のvirtualenvを作成
    pyenv virtualenv "${base_version}" "${python_version}"
fi

cp -pr python-version ../.python-version

# requirementモジュール群のインストール
pip install --upgrade pip
pip install -r requirements.txt
