import dbus
import subprocess
import os
import re
import time
import guessit
import web
import youtube_dl
import threading
#~ import omxcon
#~ a=omxcon.OMXPlayer("video.mp4")

OMXPLAYER_LIB_PATH='/opt/vc/lib:/usr/lib/omxplayer'
LOCAL_LIB_PATH='/usr/local/lib'
FORMATS = ['.264','.avi','.bin','.divx','.f4v','.h264','.m4e','.m4v','.m4a','.mkv','.mov','.mp4','.mp4v','.mpe','.mpeg','.mpeg4','.mpg','.mpg2','.mpv','.mpv2','.mqv','.mvp','.ogm','.ogv','.qt','.qtm','.rm','.rts','.scm','.scn','.smk','.swf','.vob','.wmv','.xvid','.x264','.mp3','.flac','.ogg','.wav', '.flv', '.mkv']
FBI_FORMATS=['JPEG','JPG','jpg','jpeg','png','tiff','ppm','gif','xwd','bmp']
def find_media_info():			
	size=0
	
def reset_tv():
	subprocess.Popen(["killall","omxplayer","fbi","xpdf"])


class omxplayer():
	def __init__(self, mrl,subs=None):
		self.mrl = mrl
		keepratio=True
		options=""
		cmd=["omxplayer"]
		if mrl.startswith('.'):
			raise IOError('Unsafe path. Please use full path.')

		if mrl.startswith('/') and not os.access(mrl, os.R_OK):
			raise IOError('No permission to read %s' % mrl)
		if not mrl.startswith('http'):
			video_info=False
			timer=0
			while video_info==False:
				video_info = detect_video_information(mrl)
				time.sleep(1)
				timer+=1
				if timer==300:
					break
			if video_info == False:
				raise IOError('Media "%s" not found' % mrl)
				
			self.video_size = (video_info[0], video_info[1])
			self.audio_stream_list = video_info[2]
		cmd.extend([self.mrl , "--blank","-o","both","--threshold","7","--timeout","200"])
		#~ if subs!="" or subs!=None:
			#~ self.subtitles=subs.split(",")
			#~ suboptions="--align center --no-ghost-box --subtitles"
			#~ suboptions=suboptions.split(' ')
			#~ suboptions.extend(self.subtitles)
			#~ cmd.extend(suboptions)
			#~ self._subtitle_toggle = True
		self._paused = False
		self._subtitle_toggle = False
		self._volume = 0 # 0db
		self._mute=False
		self.audio_stream_index = 1
		self.options = options
		if self.options!="":
			m = re.search('(-n|--aidx) (\d+)', self.options)
			if m:
				self.audio_stream_index = int(m.group(2))
				if self.audio_stream_index > len(self.audio_stream_list):
					self.audio_stream_index = len(self.audio_stream_list)
				elif self.audio_stream_index < 1:
					self.audio_stream_index = 1	

		
		if self.options!="":
			cmd.extend(self.options.split(' '))
		print cmd
		try:
			files=os.listdir("/tmp")
			for f in files:
				if f.startswith("omxplayer"):
					os.remove("/tmp/"+f)
			self.proc = subprocess.Popen(cmd)
		#except OSError as e:
		except Exception as e:
			raise e
		time.sleep(5)	
		with open('/tmp/omxplayerdbus.root', 'r+') as f:
			print f
			omxplayerdbus = f.read().strip()
			print omxplayerdbus
		bus = dbus.bus.BusConnection(omxplayerdbus)
		object = bus.get_object('org.mpris.MediaPlayer2.omxplayer','/org/mpris/MediaPlayer2', introspect=False)
		self.prop = dbus.Interface(object,'org.freedesktop.DBus.Properties')
		self.key = dbus.Interface(object,'org.mpris.MediaPlayer2.Player')
		self.duration=self.prop.Duration()
		print {"duration":self.duration,"position":self.prop.Position()}

	def Seek(self,seconds):
		if self.prop.CanSeek():
			self.key.Seek(dbus.Int64(seconds*1000000))
			time.sleep(1)	
			return {"position":self.prop.Position()}	
		else:
			return {"error":"can't seek"}
	def Play(self):
		self.key.Pause()
		if self._paused:
			self._paused=False
		else:
			self._paused=True
		return	{"paused":self._paused}
	def Stop(self):
		if self.prop.CanQuit():
			time.sleep(0.3)
			position=self.prop.Position()
			time.sleep(0.3)
			self.key.Stop()
			return {"position":position}
		else:
			return {"error":"can't quit"}	
	def Mute(self):
		if self._mute:
			self._mute=False
			self.prop.Unmute()
			return {"mute":False}
		else:	
			self._mute=True	
			self.prop.Mute()
			return {"mute":True}		
	def Next(self):
		if self.prop.CanGoNext():
			self.key.Next()
			return {"position":self.prop.Position()}	
		else:
			return {"error":"can't go next"}			
	def Previous(self):
		if self.prop.CanGoPrevious():
			self.key.Previous()
			return {"position":self.prop.Position()}	
		else:
			return {"error":"can't go previous"}
	def ListSubs(self):
		return self.key.ListSubtitles()
	def SelectSub(self,subidx):
		return self.key.SelectSubtitle(dbus.Int32(subidx))			

def detect_video_information(mrl):
	'''
	return:
		(width, height, audio_stream_list)
		(0, 0) - unknown size.
		False - file not found or command failed.
	'''
	OMXPLAYER='/usr/bin/omxplayer.bin'
	try:
		output = subprocess.Popen([OMXPLAYER, "-i", mrl], 
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			env={"LD_LIBRARY_PATH": OMXPLAYER_LIB_PATH}).communicate()
	except OSError:
		return False

	result = output[0].strip()
	#debug(result)
	if result.endswith(' not found.'):
		return False

	video_width = 0
	video_height = 0
	m = re.search(r'Video: .+ (\d+)x(\d+)', result)
	# m will be None or re.Match
	if m:
		print "Video size detected: %s, %s" % (m.group(1), m.group(2))
		video_width = int(m.group(1))
		video_height = int(m.group(2))
	else:
		debug("Size of video is unknown")

	m = re.findall(r'Stream #(.+): Audio: (.+)', result)
	if m:
		audio_stream_list = m
	else:
		audio_stream_list = []

	return video_width, video_height, audio_stream_list


def estimate_visual_size(x, y, width, height, video_width, video_height):

	wg = float(width) / float(video_width)
	hg = float(height) / float(video_height)

	if (wg >= hg):
		visual_w = int(round(hg * video_width))
		visual_h = height
	else:
		visual_w = width
		visual_h = int(round(wg * video_height))
	debug("visual_w: %d, visual_h: %d" % (visual_w, visual_h))

	center_vertical_offset = 0
	center_horizon_offset = 0

	if (visual_w != width):
		center_horizon_offset = (width - visual_w) / 2
	if (visual_h != height):
		center_vertical_offset = (height - visual_h) / 2
	visual_x = int(round(x + center_horizon_offset))
	visual_y = int(round(y + center_vertical_offset))
	debug("visual_x: %d; visual_y: %d" % (visual_x, visual_y))
	return visual_x, visual_y, visual_w, visual_h


def run_console_command(cmd):
	return subprocess.call(cmd.split())

# http://www.raspberrypi.org/phpBB3/viewtopic.php?f=35&t=9789
def turn_off_cursor():
	run_console_command('setterm -cursor off')

def turn_on_cursor():
	run_console_command('setterm -cursor on')

def prevent_screensaver():
	run_console_command('setterm -blank off -powerdown off')



def kill_process(pid):
	try:
		os.kill(pid, signal.SIGKILL)
	except:
		pass


def terminate_self(signum, func):
	#~ global Service
	#~ Service.terminate_all_players()
	#~ remove_pid_file()
	#~ log("Terminate service (signal: %d)" % signum)
	#sys.exit(0) # this will be hang.
	os._exit(0)


def get_pid_filepath():
	'this service is run by nobody. it could not save pid to /var/run.'
	return "/tmp/omxplayer-dbus-service.pid"


def remove_pid_file():
	try:
		os.remove(get_pid_filepath())
	except:
		pass

def get_duration(mediafile):
	info = pexpect.spawn( _FILE_INFO_CMD % (mediafile) )
	duration = '00:00:00'
	data=info.readlines()
	for l in data:
		if re.findall('Duration: ([^"]*), start',l)!=[]:
			duration =re.findall('Duration: ([^"]*), start',l)
			duration=duration[0].split(".")[0]
			l = duration.split(':')
			duration=int(l[0]) * 3600 + int(l[1]) * 60 + int(l[2])
	return duration
	
	
def get_subtitles(language):
	try:
		session = subdown.server.LogIn('', '', 'en', 'opensubtitles-download 3.2')
	except:
		print "cant connect to opensubs"				
	
def image(link):
	th=threading.Thread(target=startx)
	th.start()
	subprocess.Popen('killall fbi',shell=True)
	subprocess.Popen(["fbi","-T","1","-t","5","-a","-e","-cachemem","50",link])
def gallery(links=[]):
	th=threading.Thread(target=startx)
	th.start()
	time.sleep(5)
	subprocess.Popen('killall fbi',shell=True)
	if links==[]:
		
		print "gallery"
		subprocess.Popen(["sh","startGallery.sh"])
def pdf(url):
	subprocess.Popen(["wget",url,"-P","/home/pdf"])
	file_dest='/home/pdf/'+url.split("?")[0].split("/").pop()

	print file_dest
	subprocess.Popen(['xpdf',file_dest])
	print file_dest
	pass
	global pdfprog
	pdfprog = 'xpdf'
	#~ if not pdfprog:
		#~ if os.path.exists('/usr/bin/evince'):
			#~ pdfprog = 'evince'
		#~ elif os.path.exists('/usr/bin/xpdf'):
			#~ pdfprog = 'xpdf'
		#~ else:
			#~ pdfprog = 'mupdf'
	go = False
	# option to open pdf as local file copies instead of downloading them first
	if pdfpathreplacements:
		for k,v in pdfpathreplacements.iteritems():
			if url.startswith(k):
				nurl = url.replace(k,v)
				if os.path.exists(urllib.unquote(nurl.replace('file://','').replace('%20',' ').split('#')[0])):
					url = nurl
				break
	if url.startswith('file://'):
		url = url.replace('file://','').replace('%20',' ')
		url = urllib.unquote(url)
		urll = url.split('#page=')
		f = urll[0]
		if os.path.exists(f):
			if len(urll) > 1:
				page = urll[1].split('&')[0]
				if pdfprog in ['evince','evince-gtk']:
					os.execvp(pdfprog,[pdfprog]+pdfoptions+['-i',page,f])
				else:
					os.execvp(pdfprog,[pdfprog]+pdfoptions+[f,page])
			else:
				os.execvp(pdfprog,[pdfprog]+pdfoptions+[f])
	else:
		lower = url.lower()
		if lower.endswith('.pdf') or '.pdf#page' in lower:
			urll = url.split('#page=')
			f = dldir+os.sep+urllib.unquote(urll[0].split('/')[-1].replace('%20',' '))
			if os.path.exists(f):
				go = True
			else:
				try:
					fn,h = urllib.urlretrieve(urll[0],f)
					go = True
				except:
					pass
		if go:
			if len(urll) > 1:
				page = urll[1].split('&')[0]
				if pdfprog in ['evince','evince-gtk']:
					os.execvp(pdfprog,[pdfprog]+pdfoptions+['-i',page,f])
				else:
					os.execvp(pdfprog,[pdfprog]+pdfoptions+[f,page])
			else:
				os.execvp(pdfprog,[pdfprog]+pdfoptions+[f])
				
				
def ytdl(link):
	link=web.webapi.urllib.unquote(link)
	ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s%(ext)s'})
	# Add all the available extractors
	ydl.add_default_info_extractors()
	
	result = ydl.extract_info(link
	    , download=False # We just want to extract the info
	    )
	
	if 'entries' in result:
	    # Can be a playlist or a list of videos
	    video = result['entries'][0]
	else:
	    # Just a video
	    video = result
	
	print(video)
	return video['url']

def startx():
	subprocess.call('xinit',shell=True)
