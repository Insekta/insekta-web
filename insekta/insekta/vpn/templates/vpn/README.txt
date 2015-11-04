{%load i18n %}{%blocktrans %}Insekta VPN
===========

Setting up VPN
--------------

Copy your RSA private key (client.key) into this directory. If you have
multiple certificates, you have to edit the client.conf and adjust the "cert"
option. We have put all valid certificates in this bundle. They are named
"client_XX.conf", where XX is a number, and are ordered by their expire date.

We use OpenVPN, which can usually be installed by systems package manager.
For Debian you can use "sudo apt install openvpn" to install it. For other
distributions consult your distribution's documentation.


Running VPN
-----------

To start the VPN daemon and connect to VPN simply run:

    sudo openvpn client.conf

After a while you should see the following message:

    "FIXME: Lookup! (something like: Initialization sequence completed)".

Your VPN connection is now up and running. You should now be able the reach
the services inside the VPN.

To stop the VPN connection just press CTRL+C.{% endblocktrans%}
