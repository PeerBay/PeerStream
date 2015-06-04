"""
simpleHttpServer runner.
"""

import logging
from http_server.server import run
from config import HOST
from config import PORT
from config import setup_logging
from config import torrent_session

from libtorrent import save_resume_data_alert ,bencode
from signal import signal, SIGPIPE, SIG_IGN
import  io
from omxplayer import gallery
signal(SIGPIPE,SIG_IGN) 

Log = logging.getLogger('simpleHttpServer.run')


if __name__ == '__main__':
	setup_logging()

	try:
	    # gallery()
	    run(host=HOST, port=PORT)
	except KeyboardInterrupt:
		Log.info('simpleHttpServer stopped')
		torrents=torrent_session.get_torrents()
		torrents_len=len(torrents)
		for h in torrents:
		    h.pause()
		    h.save_resume_data()
		received=[]
		while received != torrents_len*[True]:   
		    torrent_session.wait_for_alert(1000)
		    a = torrent_session.pop_alert()
		    # print "the alert "+str(a)+" is received"
		    
		    if type(a) == save_resume_data_alert:
		        received += [True]
		        print dir(a)
		        info_hash=a.resume_data["info-hash"].encode("hex")
		        io.open("resume/"+info_hash+".resume", "wb").write(bencode(a.resume_data))
		print "the torrent resume data are saved"
