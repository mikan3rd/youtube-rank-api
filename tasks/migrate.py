import argparse
import subprocess

from sqlalchemy_utils import create_database, database_exists, drop_database

from app.config import get_db_url


parser = argparse.ArgumentParser(description='データベースのマイグレーション管理')
parser.add_argument(
    '-s', '--status', help='リビジョン/ヒストリの確認', action="store_true")
parser.add_argument(
    '--head', help='最新リビジョンに進める (デフォルト)', action="store_true")
parser.add_argument('--upgrade', help='リビジョンを1つ進める', action="store_true")
parser.add_argument('--downgrade', help='リビジョンを1つ戻す', action="store_true")
parser.add_argument(
    '--db-create', help='データベースの作成', action="store_true", dest='db_create')
parser.add_argument(
    '--db-drop', help='データベースの削除 (開発環境のみ実行可能)',
    action="store_true", dest='db_drop'
)
parser.add_argument(
    '--make-revision', help='リビジョンファイルの作成 (開発環境のみ実行可能)', dest='title')


def run(env, *_args):
    args = parser.parse_args(_args)

    if args.status:
        history(env)
        exit()
    elif args.title:
        make_revision(env, args.title)
        exit()

    # データベースの作成
    url = get_db_url('rw')

    if args.db_create:
        if not database_exists(url):
            create_database(url)
            print('データベースを作成しました')
        else:
            print('データベースは既に存在しています')

        exit()

    elif args.db_drop:
        if env != 'develop':
            print('データベースの削除は開発環境のみ実行可能です')
            exit(1)

        if database_exists(url):
            drop_database(url)
            print('データベースを削除しました')
        else:
            print('データベースは既に削除されています')

        exit()

    if args.upgrade:
        command = 'upgrade +1'
    elif args.downgrade:
        command = 'downgrade -1'
    elif args.head:
        command = 'upgrade head'
    else:
        parser.print_help()
        exit()

    if not database_exists(url):
        create_database(url)

    # Alembicを実行するshellを呼び出し、テーブルを初期化
    command = './migrations/scripts/alembic.sh env=%s %s' % (env, command)
    subprocess.call(command, shell=True)


def history(env):
    command = './migrations/scripts/alembic.sh env=%s current' % env
    out, _ = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        shell=True
    ).communicate()

    current = out.decode().strip()

    command = './migrations/scripts/alembic.sh env=%s history' % env
    out, _ = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        shell=True
    ).communicate()

    history = out.decode().strip().split('\n')

    for line in history:
        if ('-> %s' % current) in line:
            print('\033[92m* %s\033[0m' % line)
        else:
            print('  %s' % line)


def make_revision(env, title):
    if env != 'develop':
        print('データベースのリビジョン作成は開発環境でのみ実行可能です')

    command = (
        'PYTHONPATH=. alembic -x env=%s --config=migrations/alembic.ini '
        'revision --autogenerate -m "%s"'
    ) % (env, title)

    status = subprocess.call(command, shell=True)

    if status == 0:
        print('')
        print('新規リビジョンファイルのベースを作成しました。')
        print('必要な修正を実施してください。')
        print('')
