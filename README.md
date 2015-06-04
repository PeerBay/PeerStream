# peerStream
Converts torrents to http streams.(streaming and seeking)

An SimpleHTTPServer variant that considers torrents as local folders (and can play things on the raspberry pi).

## Instructions
!!Warning This has been tested in linux only.

It only works with libtorrent version prior to 1

```bash 
  sudo apt-get install -y libboost1.50-all-dev automake autoconf libtool build-essential
  wget http://downloads.sourceforge.net/project/libtorrent/libtorrent/libtorrent-rasterbar-1.0.1.tar.gz
  tar -xvzf libtorrent-rasterbar-1.0.1.tar.gz 
  cd libtorrent-rasterbar-1.0.1
  ./configure --enable-python-binding
  make
  sudo make install
  cd ..
```

Then:

```
git clone https://github.com/PeerBay/peerMagnet/
cd peerMagnet
```
Start it with 
```
python run.py
```

###Load a magnet link 
visit http://localhost:5555/demo (or the ip/localdomain of the computer)
Insert a magnet link in Stream torrent section and than choose the file you want to load.


##Raspberry Pi+TV

Install omxplayer and youtube_dl
Check the link for omxplayer at http://omxplayer.sconde.net/
```
wget http://omxplayer.sconde.net/builds/omxplayer_????_armhf.deb
sudo dpkg -i omxplayer_????_armhf.deb
sudo pip install guessit BeautifulSoup requests youtube_dl pexpect

```
You can also play video/audio on your TV from youtube and [hundreds of websites using youtube_dl](http://rg3.github.io/youtube-dl/supportedsites.html)

#Development
The only files changed from the SimpleHTTPServer are:
- filesystem/helper.py
- http_server/server.py
- run.py
- config.py


The http api is http://local-ip:5555/magnet:?xt=...
e.g
```
# Play A boy and his dog (1975) movie
http://localhost:5555/magnet:?xt=urn:btih:601ddebcfb064ced0ad506b7c908e54291fa08c7&dn=A+Boy+and+His+Dog+%281975%29+1080p+BrRip+x264+-+YIFY&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Fopen.demonii.com%3A1337&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969&tr=udp%3A%2F%2Fexodus.desync.com%3A6969
```
This will the torrent metadata and return a json object with information about the files of the torrent.
A folder with the hash of the torrent in the static_files/_torrents folder.
To start streaming a file you just insert the link of the video/audio/pdf like this:
http://localhost:5555/_torrents/[folder name]/[file name]
e.g
```
http://localhost:5555/_torrents/601ddebcfb064ced0ad506b7c908e54291fa08c7/A Boy and His Dog (1975) [1080p]/A.Boy.and.His.Dog.1975.1080p.BluRay.x264.YIFY.mp4
```
If you run this on raspberry you can control omxplayer with this:
http://localhost:5555/_omx/play/_torrents/[folder name]/[file name]



