from threading import Thread
from datetime import datetime
import socket
from base64 import b64decode
import CloudFlare


class Dyndns(Thread):
    """ Thread that handles one request
    """
    def __init__(self, conn, config, remote_ip, logger):
        super().__init__()
        self.conn = conn
        self.config = config
        self.remote_ip = remote_ip
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


    def update_cf_record(self, ip):
        """ Update the DNS Record if the IP addres has changed
        """
        result = ''
        try:
            cf = CloudFlare.CloudFlare(email=self.config['cloudflare_email'],
                                       token=self.config['cloudflare_token'])
            # find out zone_id
            params = {'name': self.config['cloudflare_zone']}
            zones = cf.zones.get(params=params)
            zone_id = zones[0]['id']
            self.logger.info('Cloudflare zone id: {}'.format(zone_id))
            # read the record
            params = {
                'name': self.config['hostname'],
                'match': 'all',
                'type': 'A'
            }
            dns_records = cf.zones.dns_records.get(zone_id, params=params)
            # if the record does not exist, create it
            if len(dns_records) == 0:
                new_record = {
                    'name': self.config['hostname'],
                    'type': 'A',
                    'content': ip
                }
                try:
                    self.logger.info('Inexistent record, creating it: {}'.format(new_record))
                    dns_record = cf.zones.dns_records.post(zone_id, data=new_record)
                except CloudFlare.exceptions.CloudFlareAPIError as err:
                    self.logger.error('Cloudflare post API call failed: {}'.format(err))
                    result = 'error'
                else:
                    self.logger.info('Updated record: {} {}'.format(self.config['hostname'], ip))
                    result = 'success'
            # debugging info
            self.logger.info('DNS Records: {}'.format(dns_records))
        except CloudFlare.exceptions.CloudFlareAPIError as err:
            self.logger.error('Cloudflare get API call failed: {}'.format(err))
            result = 'error'
        else:
            for record in dns_records:
                # if A record
                if record['type'] == 'A':
                    # if the ip address has changed
                    if ip != record['content']:
                        record_id = record['id']
                        new_record = {
                            'name': self.config['hostname'],
                            'type': 'A',
                            'content': ip
                        }
                        try:
                            dns_record = cf.zones.dns_records.put(zone_id, record_id, data=new_record)
                        except CloudFlare.exceptions.CloudFlareAPIError as err:
                            self.logger.error('Cloudflare put API call failed: {}'.format(err))
                            result = 'error'
                        else:
                            self.logger.info('Updated record: {} {}'.format(self.config['hostname'], ip))
                            result = 'success'
                    else:
                        result = 'unmodified'
                else:
                    result = 'unknown'
        return result


    def process_request(self, data):
        """ Process data received from the client
        """
        headers = {}
        content = b''
        parameters = b''
        end_headers = False
        for line in data.splitlines():
            if line.startswith(b'POST') or line.startswith(b'PUT') \
                or line.startswith(b'GET') or line.startswith(b'HEAD'):
                self.logger.info('Skipping line: {}'.format(line))
                parameters = line
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
            if resp == b'OK':
                # call the Cloudflare DNS Record update
                if b'/?ipv4' in parameters:
                    ip_start = parameters.index(b'=') + 3
                    ip = ''
                    for char in str(parameters)[ip_start:]:
                        if char != ' ':
                            ip = ip + char
                            ip_start
                        else:
                            break
                    remote_ip = ip
                elif b'X-Forwarded-For' in headers:
                    remote_ip = headers[b'X-Forwarded-For'].decode('utf-8')
                else:
                    remote_ip = self.remote_ip
                resp = self.update_cf_record(remote_ip).encode('utf-8')
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
