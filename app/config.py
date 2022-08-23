"""OS module."""
import os

# CONFIG hash
CONFIG = {}

CONFIG['host'] = '0.0.0.0'
CONFIG['port'] = 18080
CONFIG['app_name'] = 'Dyndns'
CONFIG['log_file'] = '/var/log/dyndns.log'

# Fritz Box login to DynDNS
CONFIG['username'] = 'fritzUser'
CONFIG['password'] = 'fritz!passw0rd'
CONFIG['hostname'] = 'my.ddnshostname.net'

# Cloudflare data
CONFIG['cloudflare_email'] = "email.address@domain.net"
CONFIG['cloudflare_token'] = "my.secret.cloudflare.token"
CONFIG['cloudflare_zone'] = "ddnshostname.net"

# docker stuff
CONFIG['inContainer'] = False


def _get_config_from_env():
    if "DYN_HOST" in os.environ:
        CONFIG['host'] = os.environ['DYN_HOST']

    if "DYN_PORT" in os.environ:
        CONFIG['port'] = 18080

    if "DYN_LOGFILE" in os.environ:
        CONFIG['log_file'] = os.environ['DYN_LOGFILE']

    if "DYN_FRITZBOX_USERNAME" in os.environ:
        CONFIG['username'] = os.environ['DYN_FRITZBOX_USERNAME']

    if "DYN_FRITZBOX_PASSWORD" in os.environ:
        CONFIG['password'] = os.environ['DYN_FRITZBOX_PASSWORD']

    if "DYN_DNSNAME" in os.environ:
        CONFIG['hostname'] = os.environ['DYN_DNSNAME']

    if "DYN_CF_MAIL" in os.environ:
        CONFIG['cloudflare_email'] = os.environ['DYN_CF_MAIL']

    if "DYN_CF_API_TOKE" in os.environ:
        CONFIG['cloudflare_token'] = os.environ['DYN_CF_API_TOKE']

    if "DYN_CF_ZONE" in os.environ:
        CONFIG['cloudflare_zone'] = os.environ['DYN_CF_ZONE']

    if "DYN_INCONTAINER" in os.environ:
        CONFIG['inContainer'] = True
