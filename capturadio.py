#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import urllib2
import time
import argparse
import ConfigParser
import os


def as_utf8(string):
	return u'%s' % unicode(string, 'utf-8')

def as_ascii(string):
	return '%s' % string.decode('ascii', 'ignore')

def format_date(time_value):
	if (config.has_section('settings') and config.has_option('settings', 'date_pattern')):
		pattern = config.get('settings', 'date_pattern', '%Y-%m-%d_%H-%M-%S')
	else:
		pattern = '%Y-%m-%d_%H-%M-%S'

	if (type(time_value).__name__ == 'float'):
		time_value = time.localtime(time_value)
	elif (type(time_value).__name__ == 'struct_time'):
		pass
	else:
		raise TypeError('time_value has to be a struct_time or a float. "%s" given.' % time_value)
	return time.strftime(pattern, time_value)

class CaptuRadio:
	def capture(self, stream_url, duration):
		import tempfile
		file_name = u"%s/capturadio_%s.mp3" % (tempfile.gettempdir(), os.getpid())
		file = open(file_name, 'w+b')
		not_ready = True
		try:
			stream = urllib2.urlopen(stream_url);
			while not_ready:
				file.write(stream.read(10240));
				if ((time.time() - start_time) > duration):
					not_ready = False
			file.close
			return file_name
		except Exception as e:
			print "Could not complete capturing, because an exception occured.", e
			os.remove(file_name)

	def add_metadata(self, file, station_name, show_title, title):
		print u"add_metadata: file=%s, station_name=%s, show_title=%s, title=%s" % (file, station_name, show_title, title)
		from mutagen.mp3 import MP3
		import mutagen.id3
		if (config.has_section(station_name) and config.has_option(station_name, 'name')):
			station_name = config.get(station_name, 'name', station_name)

		show_title = as_utf8(show_title)
		title = as_utf8(title)
		station_name = as_utf8(station_name)
		date = time.strftime('%Y', time.localtime(start_time))
		comment = u'Show: %s\nEpisode: %s\nCopyright: %s %s' % (show_title, title, date, station_name)

		audio = MP3(file)
		# See http://www.id3.org/id3v2.3.0 for details about the ID3 tags
		audio["TIT2"] = mutagen.id3.TIT2(encoding=2, text=[title])
		audio["TDRC"] = mutagen.id3.TDRC(encoding=2, text=[format_date(start_time)])
		audio["TCON"] = mutagen.id3.TCON(encoding=2, text=[u'Podcast'])
		audio["TALB"] = mutagen.id3.TALB(encoding=2, text=[show_title])
		audio["TLEN"] = mutagen.id3.TLEN(encoding=2, text=[duration * 1000])
		audio["TPE1"] = mutagen.id3.TPE1(encoding=2, text=[station_name])
		audio["TCOP"] = mutagen.id3.TCOP(encoding=2, text=[station_name])
		audio["COMM"] = mutagen.id3.COMM(encoding=2, text=[comment])

		# APIC part taken from http://mamu.backmeister.name/praxis-tipps/pythonmutagen-audiodateien-mit-bildern-versehen/
		if (config.has_section(station_name) and config.has_option(station_name, 'logo')):
			logo = config.get(station_name, 'logo')
			imgdata = urlopen(logo).read()
			img = mutagen.id3.APIC(3, u'image/jpeg', 3, u'Station logo', imgdata)
			audio.tags.add(img)

		audio.save()

	def store_file(self, src_file, destination, station_name, artist, title):
		import shutil, re
		if (config.has_section(station_name) and config.has_option(station_name, 'name')):
			station_name = config.get(station_name, 'name', station_name)

		destination = os.path.expanduser(destination)
		time_string = format_date(time.localtime(start_time))
		target_file = u"%s/%s/%s/%s_%s.mp3" % (as_ascii(destination), as_ascii(station_name), as_ascii(artist), as_ascii(title), time_string)
		target_file = re.compile(u'[^\w\d._/ -]').sub('', target_file)
		if (not os.path.isdir(os.path.dirname(target_file))):
			os.makedirs(os.path.dirname(target_file))
		shutil.copy2(src_file, target_file)
		return target_file

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.capturadio/capturadiorc'), os.path.expanduser('~/.capturadiorc')])

parser = argparse.ArgumentParser(description='Capture internet radio programs broadcasted in mp3 encoding format.',
epilog="Here is a list of defined radio stations: %s" % config.options('stations'))
parser.add_argument('-l', metavar='length', type=int, required=True, help='Length of recording in seconds')
parser.add_argument('-s', metavar='station', required=True, help='Name of the station, defined in ~/.capturadio/capturadiorc.')
parser.add_argument('-b', metavar='broadcast', required=True, help='Title of the broadcast')
parser.add_argument('-t', metavar='title', required=False, help='Title of the recording')
parser.add_argument('-d', metavar='destination', required=False, help='Destination directory')

args = parser.parse_args()

duration = args.l
if (duration < 1):
    print "Length of '%d' is not a valid recording duration. Use a value greater 1." % duration
    exit(1)

station = args.s
if (not config.has_option('stations', station)):
    print "Station '%s' is unknown. Use one of these: %s." % (station, config.options('stations'))
    exit(1)

title = args.t if (args.t != None) else args.b

if (args.d != None):
	destination = args.d
elif(config.has_section('settings') and config.has_option('settings', 'destination')):
	destination = os.path.expanduser(config.get('settings', 'destination'))
else:
	destination = os.getcwd()

start_time = time.time()

recorder = CaptuRadio()

file = recorder.capture(config.get('stations', station), duration)
file = recorder.store_file(file, destination, station, args.b, title)
recorder.add_metadata(file, station, args.b, title)
