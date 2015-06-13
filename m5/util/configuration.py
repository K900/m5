import logging
import os.path

import peewee
import toml

LOG = logging.getLogger('m5.configuration')


def load_config(name, schema=None):
    LOG.debug('Trying to load configuration file for {}'.format(name))
    config_path = './config/{}.toml'.format(name)
    if os.path.exists(config_path):
        data = toml.load(open(config_path, encoding='utf-8'))
    else:
        LOG.warning('Attempted to load non-existent configuration file {}'.format(name))
        data = {}

    if schema:
        return schema.validate(data)
    else:
        return data


def get_database(name):
    if not os.path.exists('./storage/'):
        os.mkdir('./storage/')
    storage_path = './storage/{}.sqlite3'.format(name)
    return peewee.SqliteDatabase(storage_path, check_same_thread=False)
