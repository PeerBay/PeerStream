"""
Configuration settings for torrent support.
"""

import os
import logging.config
import libtorrent


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_FILES_DIR = os.path.join(PROJECT_DIR, 'static_files')
TORRENTS_DIR=os.path.join(STATIC_FILES_DIR,'_torrents')
torrent_session = libtorrent.session()		
torrent_session.listen_on(6881, 6891)
torrent_session.set_alert_mask(libtorrent.alert.category_t.storage_notification + libtorrent.alert.category_t.status_notification)
atp={}
atp["static_path"]="_torrents"
atp["save_path"] = os.path.join(STATIC_FILES_DIR,atp["static_path"])
atp["storage_mode"] = libtorrent.storage_mode_t.storage_mode_sparse
atp["paused"] = False
atp["auto_managed"] = True
atp["duplicate_is_error"] = True
read_piece_alert=libtorrent.read_piece_alert
future_pieces=3
more_pieces=10
HOST = '0.0.0.0'
PORT = 5555

SOCKET_BACKLOG_SIZE = 5

FILE_CHUNK_SIZE = 1024 * 1024

RECV_BUFSIZ = 1024

THREAD_POOL_SIZE = 10

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(module)s %(process)d %(thread)d %(levelname)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file-log': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'verbose',
            'filename': 'run.log',
            'when': 'midnight',
        },
    },
    'loggers': {
        'simpleHttpServer': {
            'handlers': ['file-log', 'console'],
            'propagate': False,
            'level': 'INFO',
        },
    },
}


def setup_logging():
    logging.config.dictConfig(LOGGING)

