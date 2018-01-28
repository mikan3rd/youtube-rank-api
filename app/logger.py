import logging.config
import os


def setup_logger(config: dict, log_dir: str='log', debug: bool=False) -> None:
    '''ロガーを初期化する

    Args:
        config: ロガーのコンフィグ
        log_dir: ログ出力するディレクトリ
                 logging.yamlに設定されたhandlerのfilenameにlog_dirが付加される
        debug: Trueの場合、logging.yamlのloggerのlevelをDEBUGに変更される
    '''
    # ログ出力ディレクトリが存在しない場合、作成する
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 設定のhandlerに出力ファイルがある場合、log_dirを頭につける
    for handler in config.get('handlers').values():
        if 'filename' in handler:
            handler['filename'] = '%s/%s' % (log_dir, handler.get('filename'))

    # debug = Trueの場合、loggerのレベルをDEBUGにする
    if debug:
        for logger in config.get('loggers').values():
            if 'level' in logger:
                logger['level'] = 'DEBUG'

    logging.config.dictConfig(config)
