#!/usr/bin/env python

import os
import re
import sys

from app.config import init_config


def main():
    curr_dir = os.getcwd()
    file_dir = os.path.dirname(os.path.realpath(__file__))

    if curr_dir != file_dir:
        print('This script must be run from the app dir.', file=sys.stderr)
        sys.exit(1)

    # add app to path
    sys.path.append(curr_dir)

    args = sys.argv[1:]
    if len(args) > 1 and args[0] in ['-e', '--env']:
        env = args[1]
        args = args[2:]
    else:
        env = 'develop'

    # コンフィグ初期化
    try:
        init_config(env=env)
    except:
        print('存在しない環境が指定されました: %s' % env)
        exit(1)

    if len(args) == 0 or args[0] in ['-h', '--help']:
        usage_exit(0)

    task_name = args[0]

    # 実行コマンドをタスク名を含めて書き換え
    sys.argv[0] = '%s %s' % (sys.argv[0], task_name)

    if task_name == 'test':
        # テストランナー
        task_module = 'tests.runner'
        task = __import__(task_module, fromlist=[''])
        task.run(*args[1:])

    else:
        # 汎用タスクランナー
        task_module = 'tasks.' + args[0]

        try:
            task = __import__(task_module, fromlist=[''])
            task.run(env, *args[1:])
        except ImportError:
            print('No task specified.', file=sys.stderr)
            usage_exit(1)


def usage_exit(status=0):
    usage_msgs = []
    usage_msgs.append('')
    usage_msgs.append('usage: task.py [-h] [-e ENV] TASK [-h] [task args]')
    usage_msgs.append('')
    usage_msgs.append('optional arguments:')
    usage_msgs.append('  -h, --help  show this help message and exit')
    usage_msgs.append('  -e, --env   環境の指定 (デフォルト: develop)')
    usage_msgs.append('')
    usage_msgs.append('TASK:')

    tasklist = []
    tasklist.append(('test', 'ユニットテストの実行'))

    for path in os.listdir('tasks'):
        if not path.endswith('.py'):
            continue

        module_name = re.sub('\.py$', '', path)
        module = __import__('tasks.%s' % module_name, fromlist=[''])
        if hasattr(module, 'parser'):
            description = module.parser.description
        else:
            description = ''
        tasklist.append((module_name, description))

    max_taskname_length = max(len(t[0]) for t in tasklist)
    for taskname, description in tasklist:
        usage_msgs.append(
            ('  %%-%ss    %%s' % max_taskname_length) % (taskname, description)
        )

    usage_msgs.append('')
    usage_msgs.append('  task.py TASK -h でタスク毎のヘルプメッセージを表示')
    usage_msgs.append('')
    print('\n'.join(usage_msgs))

    sys.exit(status)


if __name__ == '__main__':
    main()
