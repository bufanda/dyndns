# Systemd automatic startup

- copy the files Dyndns.py and dns.py to /usr/local/bin
- copy the dyndns.service file to /lib/systemd/system
- run 
<pre>
systemctl daemon-reload
</pre>
and 
<pre>
systemctl enable dyndns.service
</pre>
to enable automatic startup of dyndns service at reboot.
- run
<pre>
systemctl start dyndns.service
</pre>
to start the service now.
