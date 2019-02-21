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
