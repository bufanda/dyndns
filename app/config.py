import os

# config hash
config = {}

config['host'] = '0.0.0.0'
config['port'] = 18080
config['app_name'] = 'Dyndns'
config['log_file'] = '/var/log/dyndns.log'

# Fritz Box login to DynDNS
config['username'] = 'fritzUser'
config['password'] = 'fritz!passw0rd'
config['hostname'] = 'my.ddnshostname.net'

# Cloudflare data
config['cloudflare_email'] = "email.address@domain.net"
config['cloudflare_token'] = "my.secret.cloudflare.token"
config['cloudflare_zone']  = "ddnshostname.net"

#docker stuff
config['inContainer'] = False

def _get_config_from_env():
    global config
    if "DYN_HOST" in os.environ:
        config['host'] = os.environ['DYN_HOST']

    if "DYN_PORTT" in os.environ:
        config['port'] = 18080

    if "DYN_LOGFILE" in os.environ:
        config['log_file'] = os.environ['DYN_LOGFILE']

    if "DYN_FRITZBOX_USERNAME" in os.environ:
        config['username'] = os.environ['DYN_FRITZBOX_USERNAME']

    if "DYN_FRITZBOX_PASSWORD" in os.environ:
        config['password'] = os.environ['DYN_FRITZBOX_PASSWORD']

    if "DYN_DNSNAME" in os.environ:
        config['hostname'] = os.environ['DYN_DNSNAME']
    
    if "DYN_CF_MAIL" in os.environ:
        config['cloudflare_email'] = os.environ['DYN_CF_MAIL']
    
    if "DYN_CF_API_TOKE" in os.environ:
        config['cloudflare_token'] = os.environ['DYN_CF_API_TOKE']
    
    if "DYN_CF_ZONE" in os.environ:
        config['cloudflare_zone']  = os.environ['DYN_CF_ZONE']

    if "DYN_INCONTAINER" in os.environ:
        config['inContainer']  = True
    
    return
    