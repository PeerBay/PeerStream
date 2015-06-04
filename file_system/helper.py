"""
File system helper.
"""
import os
import logging
import mimetypes
import socket
from config import STATIC_FILES_DIR
from config import FILE_CHUNK_SIZE
from config import TORRENTS_DIR
from time import sleep
from config import torrent_session
from config import atp
from config import read_piece_alert
from config import future_pieces
from config import more_pieces
import urllib2
import io
import libtorrent
import signal
import sys

Log = logging.getLogger('simpleHttpServer.helper')
class reference(object):
	pass

                    

   

class File(object):
    def __init__(self, request_uri=None, file_name=None, file_size=None, exists=False, mime_type=None,handle=None):
        self.request_uri = request_uri
        self.file_name = file_name
        self.file_size = file_size
        self.exists = exists
        self.mime_type = mime_type
        self.handle=handle

    def __str__(self):
        return 'File (request_uri=%s, file_name=%s, exists=%s, mime_type=%s)' % \
               (self.request_uri, self.file_name, self.exists, self.mime_type)

    def open(self):
		
        return open(self.file_name, 'rb')

    def calculate_range(self, range):
        range_start, range_end = 0, None
		
        if range:
            range_start, range_end = range

        if not range_end:
            range_end = self.file_size - 1

        return range_start, range_end

    def stream_to(self, output, range, file_chunk_size=None):
        if not file_chunk_size:
            file_chunk_size = FILE_CHUNK_SIZE

        range_start, range_end = range
  
        remaining_bytes = range_end - range_start + 1
        if self.handle:
            # self.handle.resume()
            info=self.handle.get_torrent_info()
            num_pieces=info.num_pieces()
            # piece=self.handle.map_piece(range_start).piece
            # piece_priorities=piece*[0]+future_pieces*[7]+more_pieces*[1]+(num_pieces-piece-future_pieces-more_pieces)*[0]
            # piece_priorities=piece_priorities[:num_pieces]
            # self.handle.prioritize_pieces(piece_priorities)
        # until there is no more bytes to send
        byte=range_start
        while remaining_bytes > 0:
            if self.handle:
                
                piece=self.handle.map_piece(byte).piece
                have=self.handle.have_piece(piece)
                print 'want:',piece,"have:",have
                piece_priorities=piece*[0]+(num_pieces-piece)*[1]
                # piece_priorities=piece*[0]+(2*future_pieces)*[7]+more_pieces*[1]+(num_pieces-piece-(2*future_pieces)-more_pieces)*[0]
                piece_priorities[:num_pieces]
                if num_pieces!=len(piece_priorities):
                    print "wrong length"
                    piece_priorities=num_pieces*[1]
                self.handle.prioritize_pieces(piece_priorities)
                self.handle.piece_priority(piece,7)
                sleep(0.1)
                if not have:
                    status=self.handle.status()
                    pieces=status.pieces
                    print "waiting for piece:",piece 
                    while not self.handle.have_piece(piece):
                        sleep(1)
                    print "piece ",piece," arrived"    
            with open(self.file_name, 'rb') as tf:
                tf.seek(byte)
                bytes_read = tf.read(min(remaining_bytes, file_chunk_size))
                print "piece sent"
                byte=tf.tell()
            tf.close()
            # with open("vid.mp4","wb") as vid:
            #     vid.wri
            # print f.tell(), len(bytes_read)
            
            try:
                output.sendall(bytes_read)
            except socket.error, (val, msg):

                if val == 104:
                    # supress Connection reset by peer error
                    Log.debug('Error will be skipped: %s %s', val, msg)
                else:
                    Log.error('Error occured: %s %s', val, msg)
                    # if self.handle:
                    #     self.handle.pause()
                    raise

            remaining_bytes -= file_chunk_size


def get_file(fn):
    # request_uri = fn.split("/",1)[-1]
    fsize = None
    exists = False
    mime_type = ''

    request_uri=fn.replace(STATIC_FILES_DIR+"/","")
    print request_uri
    if request_uri.startswith(atp["static_path"]):
        torrent=atp
        chosen_file="/".join(request_uri.split("/")[2:])
        print "chosen file:"+chosen_file
        url="magnet:?xt=urn:btih:"+request_uri.split("/")[1]
        info_hash=libtorrent.parse_magnet_uri(url)["info_hash"]
        handle=torrent_session.find_torrent(info_hash)
        # print str(info_hash)+".resume", os.listdir("resume")
        if handle.is_valid():
            print "Magnet already in the session"
            torrent_handle=handle
        # elif str(info_hash)+".resume" in os.listdir("resume"):
        #     torrent["resume_data"] = io.open("resume/"+str(info_hash)+".resume", "rb").read()
        #     torrent_handle = torrent_session.add_torrent(torrent)
        else:
            print " start new torrent"
            torrent["url"]=url
            torrent["save_path"]=os.path.join(TORRENTS_DIR,str(info_hash))
            # torrent["paused"]=True
            torrent_handle = torrent_session.add_torrent(torrent)
            while not torrent_handle.has_metadata():
                sleep(0.5)  

        info=torrent_handle.get_torrent_info()        
        torrent_files=info.files()
        # torrent_handle.auto_managed(False)    
        if chosen_file is not None:
            for i,file_info in enumerate(torrent_files):
                print "path:",file_info.path 
                if chosen_file == file_info.path:
                    torrent_handle.file_priority(i,1)
                    torrent_file=file_info
                    file_index=i
                else:
                    torrent_handle.file_priority(i,0)
        torrent_handle.map_piece = lambda offset: info.map_file(file_index, offset, 1)
        
        path=os.path.join(TORRENTS_DIR,torrent_file.path)
        first_byte=torrent_file.offset
        last_byte=torrent_file.offset+torrent_file.size
        torrent_handle.set_sequential_download(True)   
        first_piece=torrent_handle.map_piece(first_byte).piece
        last_piece=torrent_handle.map_piece(last_byte).piece
        num_pieces=info.num_pieces()
        future_pieces=int((last_piece-first_piece)*0.01)
        print "offset",torrent_file.offset,"piece",first_piece,"total", num_pieces
        piece_priorities=first_piece*[0]+(num_pieces-first_piece)*[1]
        piece_priorities=piece_priorities[:num_pieces]
        # piece_priorities=first_piece*[0]+future_pieces*[7]+more_pieces*[1]+(num_pieces-first_piece-future_pieces-more_pieces)*[0]
        torrent_handle.prioritize_pieces(piece_priorities)
        # torrent_handle.prioritize_pieces(num_pieces*[0])
        # torrent_handle.piece_priority(first_piece,7)
        torrent_handle.piece_priority(last_piece,7)
        torrent_handle.piece_priority(last_piece-1,7)
        # torrent_handle.num_pieces=info.num_pieces()
        piece=first_piece
        waiting=True


        while waiting:
            sleep(1)
            # if torrent_handle.have_piece(first_piece) and torrent_handle.have_piece(last_piece):
            #     waiting =False
            status=torrent_handle.status()
            pieces=status.pieces
            print pieces[piece:piece+future_pieces],last_piece  ,pieces[last_piece-1] , status.progress,status.download_rate,status.state
            if pieces[piece:piece+future_pieces] == future_pieces*[True] and pieces[last_piece-1]:
                waiting=False
        print "first and last piece received"
        # torrent_handle.prioritize_pieces(num_pieces*[1])
    else:
        torrent_handle=None    
    try:
        fsize = os.path.getsize(fn)
        exists = True
        type, encoding = mimetypes.guess_type(request_uri)
        if type:
            mime_type = type
    except:
        pass

    return File(request_uri, fn, fsize, exists, mime_type,torrent_handle)

