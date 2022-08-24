#!/usr/bin/env python3

"""System module."""
import sys
import os
import socket
import logging
import signal
from time import sleep
from dyndns import DynDns
from config import CONFIG, _get_config_from_env

# get CONFIG from environment
_get_config_from_env()

# set logging
logger = logging.getLogger(CONFIG['app_name'])
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
hdlr = logging.FileHandler(CONFIG['log_file'])
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)

# start logging
logger.setLevel(logging.INFO)
# pylint: disable=W1203
logger.info(f"Starting {CONFIG['app_name']}, listening on {CONFIG['host']} \
        port {CONFIG['port']}")


def sig_term(mysignal, frame):
    """ Handling termination signals
    """
    # pylint: disable=W1203
    logger.info(f"Signal {mysignal} frame {frame} - exiting.")
    raise ExitDaemon


class ExitDaemon(Exception):
    """ Exception used to exit daemon
    """


# pylint: disable=W0703
if __name__ == '__main__':

    # define signals
    signal.signal(signal.SIGTERM, sig_term)
    signal.signal(signal.SIGINT, sig_term)
    signal.signal(signal.SIGHUP, sig_term)

    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    RUN = True
    while RUN:
        try:
            serversocket.bind((CONFIG['host'], CONFIG['port']))
        except Exception as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger.error(f'Exception: {err}, {exc_type}, {exc_obj}, {fname}, \
                          {exc_tb.tb_lineno}')
        else:
            try:
                serversocket.listen(5)
            except Exception as err:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logger.error(f'Exception: {err}, {exc_type}, {exc_obj}, \
                          {fname}, {exc_tb.tb_lineno}')
            while RUN:
                try:
                    conn, addr = serversocket.accept()
                    logger.info(f'Connection accepted: {conn}, {addr}')
                    thread = DynDns(conn, CONFIG, addr[0], logger)
                    thread.start()
                except KeyboardInterrupt:
                    RUN = False
                except ExitDaemon:
                    RUN = False
                except Exception as err:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code
                                          .co_filename)[1]
                    logger.error(f'Exception: {err}, {exc_type}, {exc_obj}, \
                          {fname}, {exc_tb.tb_lineno}')
        try:
            sleep(1)
        except KeyboardInterrupt:
            logger.info('KeyboardInterrupt')
        except ExitDaemon:
            logger.info('ExitDaemon')
            break
