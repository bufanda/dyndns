from threading import Thread
from datetime import datetime
import socket
from base64 import b64decode


class Dyndns(Thread):
    """ Thread that handles one request
    """
    def __init__(self, conn, config, logger):
        super().__init__()
        self.conn = conn
        self.config = config
        self.logger = logger
        self.data_size = 1024
        self.logger.info('{} - New thread started'.format(self.name))


    def send_response(self, code, resp):
        """ Send http response
        """
        try:
            self.conn.send(b'HTTP/1.0 %s\n' % code)
            self.conn.send(b'Content-Type: text/plain\n\n')
            self.conn.send(b'%s\n' % resp)
        except socket.error as err:
            logger.error('Exception while sending response: {}'.format(err))
        self.conn.close()


    def authenticate(self, headers):
        """ Basic authentication
        """
        if b'Authorization' in headers:
            self.logger.info(headers[b'Authorization'])
            user_pass = b64decode(headers[b'Authorization'][6:])
            if user_pass == (self.config['username'] + ':' + self.config['password']).encode('utf-8'):
                code = b'200 OK'
                resp = b'OK'
            else:
                self.logger.info('Wrong username or password {}'.format(
                    self.config['username'] + ':' + self.config['password']))
                code = b'403 Unauthorized'
                resp = b'Access denied!'
        else:
            self.logger.info('Unauthorized')
            code = b'403 Unauthorized'
            resp = b'Access denied!'
        return code, resp


    def process_request(self, data):
        """ Process data received from the client
        """
        headers = {}
        content = b''
        end_headers = False
        for line in data.splitlines():
            if line.startswith(b'POST') or line.startswith(b'PUT') \
                or line.startswith(b'GET') or line.startswith(b'HEAD'):
                self.logger.info('Skipping line: {}'.format(line))
            else:
                if end_headers:
                    content += line
                else:
                    if line == b'':
                        end_headers = True
                    else:
                        hdr = line.split(b': ')
                        try:
                            # ucfirst format hor headers
                            headers[hdr[0].title()] = hdr[1]
                        except Exception as err:
                            self.logger.info('Exception: {}'.format(err))
                            self.logger.info('Original line: {}'.format(line))
        # finished decoding the request
        self.logger.info('Headers:\n{}'.format(headers))
        self.logger.info('Content:\n{}'.format(content))
        try:
            self.logger.info('Processing data...')
            code, resp = self.authenticate(headers)
        except Exception as err:
            self.logger.info('Exception in process_request: {}'.format(err))
            code = '503 Service Unavailable'.encode('utf-8')
            resp = 'An error has occured: {}'.format(err).encode('utf-8')
        return code, resp


    def run(self):
        data = b''
        while True:
            read_data = self.conn.recv(self.data_size)
            data += read_data
            if len(read_data) < self.data_size:
                break
        # GET or HEAD
        if data.startswith(b'GET /') or data.startswith(b'HEAD /'):
            try:
                # perform the check
                code, resp = self.process_request(data)
            except Exception as err:
                code = b'503 Service Unavailable'
                resp = err
                self.logger.error('Exception: {}'.format(err))
            self.send_response(code, resp)
            self.logger.info('GET or HEAD data: {}'.format(data))
        elif data.startswith(b'PUT /') or data.startswith(b'POST /'):
            try:
                # perform the check
                code, resp = self.process_request(data)
            except Exception as err:
                code = '503 Service Unavailable'.encode('utf-8')
                resp = 'An error has occured: {}'.format(err).encode('utf-8')
                self.logger.error('Exception in run: {}'.format(err))
            self.send_response(code, resp)
            self.logger.info('PUT or POST data: {}'.format(data))
        else:
            code = b'400 Invalid Request'
            resp = b'Invalid Request'
            self.send_response(code, resp)
            self.logger.warning('Invalid request')
