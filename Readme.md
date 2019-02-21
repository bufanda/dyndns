# Cloudflare DynDNS for FritzBox

The problem: my DSL internet connection has a dynamic IP Address and I want to know this IP Address, of course, even when I'm not home. And it's very dynamic, it changes very often.
The router (a Fritz Box) has a DynDNS menu and a few provider options. I used one of them for a long time, but it is annoying that I have to confirm my only free hostname every 30 days, and starting with a few months ago, updating the IP Address is not working properly. The IP Address for my hostname is not the real one.

I already have my own domain, with the DNS Servers hosted for free in Cloudflare, and Cloudflare has an API that can be used, and I also have a few virtual machines with public IP Addresses, so I decided to write a python DynDNS Server to set it in my router. I did some reverse engineering to understand the requests that the Fritz Box is doing.
The requests are GET requests, with basic authentication. A request (going through a nginx server, that's why the X-Forwarded-For header and 127.0.0.1 Host header) looks like this:

<pre>
GET /dyndns HTTP/1.0\r\nX-Forwarded-For: A.B.C.D\r\nHost: 127.0.0.1:12873\r\nConnection: close\r\nAuthorization: Basic <'username:password' url64 encoded>\r\nUser-Agent: Fritz!Box DDNS/1.0.1\r\n\r\n
</pre>

I wrote a multi-threaded python3 program that is processing the HTTP requests (similar to the ldapcheck program that I wrote almost 2 years ago). It logs for now a lot of debugging information. After finishing the test period I will probably update it to remove some of the debugging information.
I also created a systemd service file in the etc folder, with information about how to make the program start automatically at reboot.
The settings in config.py are self explanatory.
