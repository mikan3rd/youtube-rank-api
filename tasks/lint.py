import argparse
import subprocess

commands = [
    ('flake8', 'flake8 . --exclude=.tox,.git'),
    ('mypy', 'mypy . --ignore-missing-imports'),
    ('isort', 'isort -c'),
]

parser = argparse.ArgumentParser(description='各種lintツールを実行')
parser.add_argument('--flake8', help='flake8実行', action="store_true")
parser.add_argument('--mypy', help='mypy実行', action="store_true")
parser.add_argument('--isort', help='isort実行', action="store_true")


def run(env, *_args):
    args = parser.parse_args(_args)

    run_commands = []
    if not args.flake8 and not args.mypy and not args.isort:
        run_commands = [c[0] for c in commands]

    if args.flake8:
        run_commands.append('flake8')

    if args.mypy:
        run_commands.append('mypy')

    if args.isort:
        run_commands.append('isort')

    errors = []
    for taskname, command in commands:
        if taskname not in run_commands:
            continue

        print('[%s] (command=\'%s\')' % (taskname, command))
        returncode = subprocess.call(command, shell=True)
        if returncode != 0:
            errors.append(taskname)
        print()

    print('----[summary]----------------')
    ok_text = '\033[92mOK\033[0m'
    failed_text = '\033[91mERROR!!\033[0m'
    for taskname in run_commands:
        print(
            '%s: %s' %
            (taskname, failed_text if taskname in errors else ok_text)
        )
    print()
