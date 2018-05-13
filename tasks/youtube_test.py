import argparse

from app.server.helpers.youtube_data import get_search_result


parser = argparse.ArgumentParser(description='テスト用')


def run(env, *_args):
    get_search_result()
