# -*- coding: utf-8 -*-
"""
---

title:
    "Event logging support module."

description:
    "This Python module is designed to support
    event logging."

id:
    "72e0107d-5302-414e-83c4-7efff7f00d38"

type:
    dt003_python_module

validation_level:
    v00_minimum

protection:
    k00_general

copyright:
    "Copyright 2023 William Payne"

license:
    "Licensed under the Apache License, Version
    2.0 (the License); you may not use this file
    except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed
    to in writing, software distributed under
    the License is distributed on an AS IS BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
    either express or implied. See the License
    for the specific language governing
    permissions and limitations under the
    License."

...
"""


import appdirs
import logging
import os.path
import sqlite3

import fl.util



# -----------------------------------------------------------------------------
def logger(str_id, level):
    """
    Return logging components.

    """
    list_event = list()
    handler    = ListHandler(list_event)
    logger     = logging.getLogger(str_id)
    logger.addHandler(handler)
    logger.setLevel(level)

    return (logger, handler)


# =============================================================================
class ListHandler(logging.Handler):
    """
    A log handler class which stores LogRecord entries in a list.

    """

    # -------------------------------------------------------------------------
    def __init__(self, list_event):
        """
        Return an instance of the EventListHandler.

        """
        self.list_event = list_event
        super().__init__()

    # -------------------------------------------------------------------------
    def emit(self, record):
        """
        Append the specified logging record to the list.

        """
        self.list_event.append(dict(type         = 'log_event',
                                    name         = record.name,
                                    level        = record.levelname,
                                    pathname     = record.pathname,
                                    lineno       = record.lineno,
                                    msg          = record.msg,
                                    args         = record.args,
                                    exc_info     = record.exc_info,
                                    created      = record.created,
                                    thread       = record.thread,
                                    thread_name  = record.threadName,
                                    process      = record.process,
                                    process_name = record.processName))


# -----------------------------------------------------------------------------
@fl.util.coroutine
def writer(id_system, dirpath_log = None):
    """
    Coroutine for writing event log items to a persistent store.

    """

    # Create a directory for the event log file.
    # If the dirpath is not provided, then we use
    # the appdirs library to generate a platform
    # the appdirs library to generate a platform
    # system specific default path. On Unix
    # platforms this will be:
    #
    #   ~/.local/share/{id_system}/
    #
    if dirpath_log is None:
        dirpath_log = appdirs.user_data_dir(appname = id_system)

    # Create the directory where the event logs
    # are going to be stored. If we cannot create
    # the directory then we consider that to
    # be a critical (nonrecoverable) error, so
    # we signal the system to shut down by
    # raising an exception.
    #
    try:
        os.makedirs(dirpath_log, exist_ok = True)
    except OSerror as err:
        raise RuntimeError(
            'Critical error creating directory "{dirpath}": {err}'.format(
                                                        dirpath = dirpath_log,
                                                        err     = err))

    filename_log = 'log_event.db'
    filepath_log = os.path.join(dirpath_log, filename_log)
    connection   = sqlite3.connect(filepath_log)
    cursor       = connection.cursor()
    cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS log_events (name         TEXT,
                                                   level        TEXT,
                                                   pathname     TEXT,
                                                   lineno       INTEGER,
                                                   msg          TEXT,
                                                   args         TEXT,
                                                   exc_info     TEXT,
                                                   created      TIMESTAMP,
                                                   thread       INTEGER,
                                                   thread_name  TEXT,
                                                   process      INTEGER,
                                                   process_name TEXT)""")
    connection.commit()

    while True:

        (event) = yield (None)

        cursor.execute("""
                       INSERT INTO log_events (name,
                                               level,
                                               pathname,
                                               lineno,
                                               msg,
                                               args,
                                               exc_info,
                                               created,
                                               thread,
                                               thread_name,
                                               process,
                                               process_name)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       """,
                       (event['name'],
                        event['level'],
                        event['pathname'],
                        event['lineno'],
                        event['msg'],
                        repr(event['args']),
                        repr(event['exc_info']),  # Convert exception info to string
                        event['created'],
                        event['thread'],
                        event['thread_name'],
                        event['process'],
                        event['process_name']))
        connection.commit()

