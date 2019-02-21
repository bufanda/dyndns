#!/usr/bin/env python3


from datetime import datetime
import logging
import sys
import os
import signal
import socket
from time import sleep
from threading import Thread
from Dyndns import Dyndns
from config import config


# set logging
logger = logging.getLogger(config['app_name'])
hdlr = logging.FileHandler(config['log_file'])
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)

# start logging
logger.setLevel(logging.INFO)
logger.info('Starting {}, listening on {} port {}'.format(config['app_name'], config['host'], config['port']))


def sig_term(mysignal, frame):
    """ Handling termination signals
    """
    logger.info("Signal %s frame %s - exiting." % (mysignal, frame))
    raise ExitDaemon


class ExitDaemon(Exception):
    """ Exception used to exit daemon
    """
    pass


if __name__ == '__main__':
    # define signals
    signal.signal(signal.SIGTERM, sig_term)
    signal.signal(signal.SIGINT, sig_term)
    signal.signal(signal.SIGHUP, sig_term)
    
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    run = True
    while run:
        try:
            serversocket.bind((config['host'], config['port']))
        except Exception as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger.error('Exception: %s %s %s %s %s' % (err, exc_type, exc_obj,
                                                        fname, exc_tb.tb_lineno))
        else:
            try:
                serversocket.listen(5)
            except Exception as err:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                logger.error('Exception: %s %s %s %s %s' % (err, exc_type, exc_obj,
                                                            fname, exc_tb.tb_lineno))
            while run:
                try:
                    conn, addr = serversocket.accept()
                    logger.info('Connection accepted: %s %s' % (conn, addr))
                    thread = Dyndns(conn, config, addr[0], logger)
                    thread.start()
                except KeyboardInterrupt:
                    run = False
                except ExitDaemon:
                    run = False
                except Exception as err:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    logger.error('Exception: %s %s %s %s %s' % (err, exc_type, exc_obj,
                                                               fname, exc_tb.tb_lineno))
        try:
            sleep(1)
        except KeyboardInterrupt:
            logger.info('KeyboardInterrupt')
        except ExitDaemon:
            logger.info('ExitDaemon')
            break
