import argparse
import subprocess

parser = argparse.ArgumentParser(description='リポジトリプッシュ前の確認実行')


def run(env, *_args):
    parser.parse_args(_args)

    subprocess.call('tox', shell=True)
