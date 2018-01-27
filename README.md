# ファイル構成
```
.
├── server.py         # サーバの起動スクリプト
├── tasks.py          # バッチのインターフェースやタスクランナーを記述
├── app
│   ├── config
│   │   ├── env       # 環境ごとの設定ファイル
│   │   ├── mode      # モード別の設定ファイル
│   │   └── logging
│   ├── models        # DBモデル/データ構造のスキーマ
│   │   ├── matome    #   DBモデル (SQLAlchemy)
│   │   └── utils     #   mixinやユーザー定義型など
│   ├── resources     # リソースデータ
│   │   ├── mail_template # メールのテンプレート
│   │   └── schema    #   jsonschemaデータ (データのバリデーションに用いる)
│   └── server        # サーバーのソース
│       ├── helpers   # サーバーで利用するヘルパー
│       └── views     # APIの実装
├── migrations        # DB migration関連
│   ├── scripts
│   └── versions
├── tasks             # バッチやCLIツール置き場
├── tests             # テストコード
└── venv              # 仮想環境構築用データ
```

# 開発環境構築
## Python環境
### 前提ソフトウェア
#### pyenv
```shell
$ brew install pyenv
```

#### pyenv-virtualenv
```shell
$ brew install pyenv-virtualenv
```

※ pyenv-virtualenvは存在しない場合、環境構築スクリプトで自動インストールされます。

### 構築
```shell
$ cd matome-api/venv
$ ./setup.sh
```

### 更新
追加でパッケージをインストールした際は、以下のコマンドで依存パッケージファイルを更新してください。
```shell
$ cd matome-api/venv
$ ./freeze.sh
```

## データベース
### 前提
#### MySQL
##### バージョン
MySQL 5.7

##### ユーザー
以下のユーザーが存在すること

  - user: develop
  - password: develop
  - 権限: all

存在しない場合は、GRANT権限を持つユーザーでMySQLへログインし、以下を実行する。
※ developユーザーの部分は環境に応じて修正
```MySQL
mysql> CREATE USER 'develop'@'localhost' IDENTIFIED BY 'matome';
mysql> GRANT ALL ON matome.* TO 'develop'@'localhost';
```

`Your password does not satisfy the current policy requirements` と出力される場合、強固なパスワードが必要な設定になっているので、一時的にポリシーを緩和させる。

```MySQL
mysql> SET GLOBAL validate_password_length=4;
mysql> SET GLOBAL validate_password_policy=LOW;
```

と実行した上で、上記ユーザー作成を実施。

緩和させたポリシーをMySQL5.7のデフォルトに戻すには以下を実施する。
```MySQL
mysql> SET GLOBAL validate_password_length=8;
mysql> SET GLOBAL validate_password_policy=MEDIUM;
```

### データベース構築
以下を実行することで、データベース及びテーブルが構築されます。
```shell
$ python task.py migrate --head
```

### データベース定義変更
AlembicでRDBのスキーマ管理
http://alembic.zzzcomputing.com/en/latest/

#### Modelの修正
app/models/db以下のモデルクラスを適宜修正

#### 変更の自動検出
```shell
$ cd matome-api
$ python task.py migrate --make-revision "title"
```

上記を実行すると、`migrations/versions/`以下にマイグレーションファイルが作成される
実行時、必ずarea.sp_area_locationを削除する以下のメッセージが表示される
```
INFO  [alembic.autogenerate.compare] Detected removed index 'sp_area_location' on 'area'
```
これは`SPATIAL INDEX`がSQLAlchemyに対応していないため発生する
マイグレーションファイルから、以下を取り除く
  1. upgradeメソッド内の以下のdrop_index
  ```
  op.drop_index('sp_area_location', table_name='area')
  ```
  2. downgradeメソッド内の以下のcreate_index
  ```
  op.create_index('sp_area_location', 'area', ['location'], unique=False)
  ```

#### 変更実施
```shell
$ cd matome-api
$ python task.py migrate --head
```

# 実行
```
$ python server.py -h
usage: server.py [-h] [-e {local,develop,staging,prduction}]
                 [-m {external,internal}]

optional arguments:
  -h, --help            show this help message and exit
  -e {develop,staging,prduction,slm}, --env {develop,staging,prduction,slm}
                        実行環境
  -m {external,internal}, --mode {external,internal}
                        起動モード
```

| 引数 | デフォルト | 説明 |
| :-: | :-: | --- |
| env | develop | 環境を選択(develop,staging,prduction,slm) |
| mode | external | external: 外部公開用APIのみの起動, internal: 内部用APIも合わせて起動 |

開発環境で全APIを実行できる形で起動する場合、以下で実行する。
```
$ python server.py --env develop --mode internal
```

# 開発時チェック
## ユニットテスト
```shell

# テストの実行
$ coverage run test
# パッケージ、モジュール指定の場合
$ coverage run test p=tests.config
$ coverage run test p=tests.config.test_config
# モジュール名指定でもテスト可能
$ coverage run test p=tests/config/test_config.py
# モジュール、クラス、メソッド指定の場合
$ coverage run test m=tests.config.test_config
$ coverage run test m=tests.config.test_config.ConfigTest
$ coverage run test m=tests.config.test_config.ConfigTest.test_config

# カバレッジのブラウザ上での確認
# ソースコードレベルでカバーしているか確認できる！
$ coverage html
$ open htmlcov/index.html
```

## lint
flake8, mypy, isortによるlintを実施する。

```shell
$ python task.py lint
```

## リポジトリプッシュ前チェック
上記テスト及びlintをまとめて実施する(toxを利用) 。
本チェックにおいてNGとなった場合、修正してからプッシュすること。本チェックでは、環境をイチから生成するため、requirements.txtの更新漏れなどもチェックできます。

※ 初回実行は環境構築も実施するため若干時間がかかります。

```shell
$ python task.py check
```
