SIP
===================
SIP is the program that bind C++ with Python

let’s  go were you have downloaded the sip tar.gz and enter the folder

```
cd ~/Downloads/sip-4.11-snapshot-052b642f04a8
```

and we are gonna try to install it with the following lines :

```
python configure.py -d /Library/Python/2.7/site-packages --arch x86_64
```

— arch i386 is to specify that we want this architecture

then lets make it and install it with the following commands :

```
make
sudo make install
```

PyQt4
===================
Once installed let’s move back an go to the PyQt folder to configure it and install it with the following command :

```
cd ..
cd PyQt-mac-gpl-snapshot-4.7.5-8a6793a155e0
```

and let’s try to configure it with the right things

```
python configure.py -q /usr/bin/qmake-4.8 -d /Library/Python/2.7/site-packages/ --use-arch x86_64
```

then let’s make them with:

```
make
sudo make install
```

and now, everything should be Up and running.