"""
simpleHttpServer request handler.
"""

import socket
import urllib
import cgi
import os
from file_system.helper import get_file
# from file_system.helper import get_torrent_file
from http_protocol.request import parse_http_request
from http_protocol.response import HttpResponse
from thread_pool.pool import ThreadPool
from config import RECV_BUFSIZ
from config import STATIC_FILES_DIR
from config import TORRENTS_DIR
from config import THREAD_POOL_SIZE
from config import SOCKET_BACKLOG_SIZE
import io
import libtorrent
from config import torrent_session
from config import atp
from config import read_piece_alert
from time import sleep
import omxplayer
import json
def Log(string): print string


def handle_request(clientsock, addr):

    data = clientsock.recv(RECV_BUFSIZ)

    #Log('Request received: %s' % data)

    request = parse_http_request(data)

    path = STATIC_FILES_DIR + clean_path(request.request_uri)
    request_uri=request.request_uri[1:]
    if request_uri.startswith("_omx"):
        req=request_uri.split("/")
        cmd=req[1]
        if cmd=="play":
            omxplayer.reset_tv()
            link=("/").join(req[2:])
            path=STATIC_FILES_DIR + "/"+clean_path(req[2])
            print path
            if os.path.isdir(path):
                link= "http://localhost/"+link
                playing_video=omxplayer.omxplayer(str(link))
            elif link.split(".").pop()  in omxplayer.FORMATS:
                playing_video=omxplayer.omxplayer(str(link))
            elif link.split(".").pop()  in omxplayer.FBI_FORMATS:
                shown_image= omxplayer.image(str(link))
            elif link.split(".").pop() in ["pdf"]:
                shown_pdf= omxplayer.pdf(str(link))
            else:
                link=omxplayer.ytdl(link)  
                playing_video=omxplayer.omxplayer(str(link))
            response = HttpResponse(protocol=request.protocol, status_code=200)
            response.write_to(clientsock)
            clientsock.close()


    # if request_uri.startswith("magnet") or request_uri.endswith(".torrent") or request_uri.startswith(atp["static_path"]):
    if request_uri.startswith("magnet") or request_uri.endswith(".torrent"):
        chosen_file=None
        torrent=atp
        
        print "req uri:"+request_uri
        if request_uri.startswith("magnet"):
            info_hash=libtorrent.parse_magnet_uri(request_uri)["info_hash"]
        elif request_uri.startswith(atp["static_path"]):
            chosen_file=urllib.unquote("/".join(request_uri.split("/")[2:]))
            print "chosen file:"+chosen_file
            request_uri="magnet:?xt=urn:btih:"+request_uri.split("/")[1]
            info_hash=libtorrent.parse_magnet_uri(request_uri)["info_hash"]
        elif request_uri.endswith(".torrent"):

            #get info hash
            pass
        handle=torrent_session.find_torrent(info_hash)

        if handle.is_valid():
            print "Magnet already in the session"
            torrent_handle=handle 
        elif (str(info_hash)+".resume") in os.listdir("resume"):
            torrent["resume_data"] = io.open("resume/"+str(info_hash)+".resume", "rb").read()
            torrent_handle = torrent_session.add_torrent(torrent)
        else:
            print " start new torrrent"
            torrent["url"]=request_uri
            # torrent["paused"]=True
            torrent["save_path"]=os.path.join(TORRENTS_DIR,str(info_hash))
            torrent_handle = torrent_session.add_torrent(torrent)
            print "getting metadata"
            while not torrent_handle.has_metadata():
                sleep(1)
        print "getting info"       
        info=torrent_handle.get_torrent_info()        
        torrent_files=info.files()
        torrent_handle.auto_managed(False)    
        if chosen_file is not None:
            for i,file_info in enumerate(torrent_files):
                print "path:",file_info.path 
                if chosen_file == file_info.path:

                    torrent_handle.file_priority(i,1)
                    file_index=i
                else:
                    torrent_handle.file_priority(i,0)    

            file = get_torrent_file(torrent_handle,file_index)

            if file.exists and request.is_range_requested():
                response = HttpResponse(protocol=request.protocol, status_code=206,
                                        range=request.get_range())
                response.file = file

            elif file.exists:
                response = HttpResponse(protocol=request.protocol, status_code=200)
                response.file = file
                Log('%s GET "%s" %s %s %s' %
                    (addr[0], request.request_uri, request.protocol, request.get_range(), response.status_code))

                response.write_to(clientsock)
                clientsock.close()    
         
        info=torrent_handle.get_torrent_info()
        name= info.name()
        # f = str()
        # f += '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">'
        # f += "<html>\n<title>Directory listing for %s</title>\n" % name
        # f +="<body>\n<h2>Directory listing for %s</h2>\n" % name
        # f += "<hr>\n<ul>\n"
        f={}
        for i,file_info in enumerate(torrent_files):
            f[i]={"link":"/"+os.path.join(atp["static_path"],str(info_hash),file_info.path),
                  "size":file_info.size,
                  "path":file_info.path
            }
            # f += '<li><a href="%s">%s</a><h6>%s</h6></li>\n' % (os.path.join(atp["static_path"],str(info_hash),file_info.path), file_info.path,file_info.size)
        # f += "</ul>\n<hr>\n</body>\n</html>\n"
        f=json.dumps(f)
        response = HttpResponse(protocol=request.protocol, status_code=200)
        response.headers['Content-type'] = 'application/json'
        response.headers['Content-Length'] = len(f)
        # response.headers['Accept-Ranges'] = 'bytes'
        response.content = f
        Log('%s GET "%s" %s %s %s' %
            (addr[0], request.request_uri, request.protocol, request.get_range(), response.status_code))
        response.write_to(clientsock)
        clientsock.close()
        return None

      
        
        # h.set_sequential_download(True)
        # while h.status().progress < 0.01:
        #     sleep(1)          
        # h.file_index=max_i  
        # h.offset=max_offset     
    
    # check if path is dir (copy from the SimpleHttpServer)
    path=STATIC_FILES_DIR + clean_path(request.request_uri)
    if os.path.isdir(path):
        print path
        if not path.endswith('/'):
            # redirect browser - doing basically what apache does
            response = HttpResponse(protocol=request.protocol, status_code=301)
            response.headers['Location'] = path + "/"
            Log('%s GET "%s" %s %s %s' %
                (addr[0], request.request_uri, request.protocol, request.get_range(), response.status_code))
            response.write_to(clientsock)
            clientsock.close()
            return None
        for index in "index.html", "index.htm":
            index = os.path.join(path, index)
            if os.path.exists(index):
                path = index
                break
        else:
            # quick and dirty but it works :P (also copy from SimpleHttpServer)
            try:
                list = os.listdir(path)
            except os.error:
                response = HttpResponse(protocol=request.protocol, status_code=404)
                response.headers['Content-type'] = 'text/plain'
                response.content = 'No permission to list directory'
                Log('%s GET "%s" %s %s %s' %
                    (addr[0], request.request_uri, request.protocol, request.get_range(), response.status_code))
                response.write_to(clientsock)
                clientsock.close()
                return None
            list.sort(key=lambda a: a.lower())
            f = str()
            displaypath = cgi.escape(urllib.unquote(request.request_uri))
            # f += '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">'
            # f += "<html>\n<title>Directory listing for %s</title>\n" % displaypath
            # f +="<body>\n<h2>Directory listing for %s</h2>\n" % displaypath
            f += "<hr>\n<ul>\n"
            for name in list:
                fullname = os.path.join(path, name)
                displayname = linkname = name
                # Append / for directories or @ for symbolic links
                if os.path.isdir(fullname):
                    displayname = name + "/"
                    linkname = name + "/"
                if os.path.islink(fullname):
                    displayname = name + "/" # "@"
                    # Note: a link to a directory displays with @ and links with /
                f += '<li><a href="%s">%s</a>\n' % (urllib.quote(linkname), cgi.escape(displayname))
            f += "</ul>\n<hr>\n</body>\n</html>\n"
            response = HttpResponse(protocol=request.protocol, status_code=200)
            response.headers['Content-type'] = 'text/html'
            response.headers['Content-Length'] = len(f)
            response.headers['Accept-Ranges'] = 'bytes'
            response.content = f
            Log('%s GET "%s" %s %s %s' %
                (addr[0], request.request_uri, request.protocol, request.get_range(), response.status_code))
            response.write_to(clientsock)
            clientsock.close()
            return None
    print urllib.unquote(request.request_uri)[1:]

    file = get_file(path)

    if file.exists and request.is_range_requested():
        response = HttpResponse(protocol=request.protocol, status_code=206,
                                range=request.get_range())
        response.headers["Content-Type"]=file.mime_type
        response.headers["Connection"]="Keep-Alive"
        response.file = file

    elif file.exists:
        response = HttpResponse(protocol=request.protocol, status_code=200)
        response.file = file

    else:
        response = HttpResponse(protocol=request.protocol, status_code=404)
        response.headers['Content-type'] = 'text/plain'
        response.content = 'This file does not exist!'

    Log('%s GET "%s" %s %s %s' %
        (addr[0], request.request_uri, request.protocol, request.get_range(), response.status_code))

    response.write_to(clientsock)
    clientsock.close()

def clean_path(path):
    """ remove query parameters and decode html """
    # abandon query parameters
    path = path.split('?',1)[0]
    path = path.split('#',1)[0]
    path = urllib.unquote(path)
    return path

def run(host, port):
    address = (host, port)
    serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serversock.bind(address)
    serversock.listen(SOCKET_BACKLOG_SIZE)

    Log('simpleHttpServer started on %s:%s' % (host, port))

    pool = ThreadPool(THREAD_POOL_SIZE)

    while True:
        #Log('Waiting for connection...')

        clientsock, addr = serversock.accept()
        #Log('Connected from: %s' % addr)

        pool.add_task(handle_request, clientsock, addr)
