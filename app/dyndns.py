"""dyndns module."""
from threading import Thread
import socket
from base64 import b64decode
import CloudFlare


# pylint: disable=R0912,W0703,E1101
class DynDns(Thread):

    """ Thread that handles one request
    """
    def __init__(self, conn, config, remote_ip, logger):
        super().__init__()
        self.conn = conn
        self.config = config
        self.remote_ip = remote_ip
        self.logger = logger
        self.data_size = 1024
        self.logger.info(f'{self.name} - New thread started')

    def send_response(self, code, resp):
        """ Send http response
        """
        try:
            self.conn.send(b'HTTP/1.0 %s\n' % code)
            self.conn.send(b'Content-Type: text/plain\n\n')
            self.conn.send(b'%s\n' % resp)
        except socket.error as err:
            self.logger.error(f'Exception while sending response: {err}')

        self.conn.close()

    def authenticate(self, headers):
        """ Basic authentication
        """
        if b'Authorization' in headers:
            self.logger.info(headers[b'Authorization'])
            user_pass = b64decode(headers[b'Authorization'][6:])
            if user_pass == \
                    (self.config['username'] + ':' +
                     self.config['password']).encode('utf-8'):
                code = b'200 OK'
                resp = b'OK'
            else:
                self.logger.info(f"Wrong username or password \
                    {self.config['username']} + ':' + \
                        { self.config['password']}")

                code = b'403 Unauthorized'
                resp = b'Access denied!'
        else:
            self.logger.info('Unauthorized')
            code = b'403 Unauthorized'
            resp = b'Access denied!'
        return code, resp

    def update_cf_record(self, public_ip):
        """ Update the DNS Record if the IP addres has changed
        """
        result = ''
        try:
            cloudflare = CloudFlare.CloudFlare(
                         email=self.config['cloudflare_email'],
                         token=self.config['cloudflare_token'])
            # find out zone_id
            params = {'name': self.config['cloudflare_zone']}
            zones = cloudflare.zones.get(params=params)
            zone_id = zones[0]['id']
            self.logger.info(f'Cloudflare zone id: {zone_id}')
            # read the record
            params = {
                'name': self.config['hostname'],
                'match': 'all',
                'type': 'A'
            }
            dns_records = cloudflare.zones.dns_records.get(zone_id,
                                                           params=params)
            # if the record does not exist, create it
            if len(dns_records) == 0:
                new_record = {
                    'name': self.config['hostname'],
                    'type': 'A',
                    'content': public_ip
                }
                try:
                    self.logger.info(f'Inexistent record, creating it: \
                        {new_record}')
                    cloudflare.zones.dns_records.post(zone_id,
                                                      data=new_record)
                except CloudFlare.exceptions.CloudFlareAPIError as err:
                    self.logger.error(f'Cloudflare post API call failed: {err}'
                                      )
                    result = 'error'
                else:
                    self.logger.info(f"Updated record: \
                                     {self.config['hostname']} {public_ip}")
                    result = 'success'
            # debugging info
            self.logger.info(f'DNS Records: {dns_records}')
        except CloudFlare.exceptions.CloudFlareAPIError as err:
            self.logger.error(f'Cloudflare get API call failed: {err}')
            result = 'error'
        else:
            for record in dns_records:
                # if A record
                if record['type'] == 'A':
                    # if the ip address has changed
                    if public_ip != record['content']:
                        record_id = record['id']
                        new_record = {
                            'name': self.config['hostname'],
                            'type': 'A',
                            'content': public_ip
                        }
                        try:
                            cloudflare.zones.dns_records.put(zone_id,
                                                             record_id,
                                                             data=new_record)
                        except CloudFlare.exceptions.CloudFlareAPIError as err:
                            self.logger.error(f'Cloudflare put API call \
                                              failed: {err}')
                            result = 'error'
                        else:
                            self.logger.info(f"Updated record: \
                                    {self.config['hostname']} {public_ip}")
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
                self.logger.info(f'Skipping line: {line}')
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
                            self.logger.info(f'Exception: {err}')
                            self.logger.info(f'Original line: {line}')
        # finished decoding the request
        self.logger.info(f'Headers:\n{headers}')
        self.logger.info(f'Content:\n{content}')
        try:
            self.logger.info('Processing data...')
            code, resp = self.authenticate(headers)
            if resp == b'OK':
                # call the Cloudflare DNS Record update
                if b'/?ipv4' in parameters:
                    ip_start = parameters.index(b'=') + 3
                    current_ip = ''
                    for char in str(parameters)[ip_start:]:
                        if char != ' ':
                            current_ip = current_ip + char
                        else:
                            break
                    remote_ip = current_ip
                elif b'X-Forwarded-For' in headers:
                    remote_ip = headers[b'X-Forwarded-For'].decode('utf-8')
                else:
                    remote_ip = self.remote_ip
                resp = self.update_cf_record(remote_ip).encode('utf-8')
        except Exception as err:
            self.logger.info(f'Exception in process_request: {err}')
            code = '503 Service Unavailable'.encode('utf-8')
            resp = f'An error has occured: {err}'.encode('utf-8')
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
                self.logger.error(f'Exception: {err}')
            self.send_response(code, resp)
            self.logger.info(f'GET or HEAD data: {data}')
        elif data.startswith(b'PUT /') or data.startswith(b'POST /'):
            try:
                # perform the check
                code, resp = self.process_request(data)
            except Exception as err:
                code = '503 Service Unavailable'.encode('utf-8')
                resp = f'An error has occured: {err}'.encode('utf-8')
                self.logger.error(f'Exception in run: {err}')
            self.send_response(code, resp)
            self.logger.info(f'PUT or POST data: {data}')
        else:
            code = b'400 Invalid Request'
            resp = b'Invalid Request'
            self.send_response(code, resp)
            self.logger.warning('Invalid request')
