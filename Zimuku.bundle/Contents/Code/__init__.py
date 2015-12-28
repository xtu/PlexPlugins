#zimuku.net
#Subtitles service allowed by www.zimuku.net

import io
import os
import hashlib
import json
import urllib
import urllib2
from urllib2 import HTTPError
import httplib


ZIMUKU_API = 'http://www.zimuku.net/search?q=%s'
# OS_LANGUAGE_CODES = 'http://www.opensubtitles.org/addons/export_languages.php'
ZIMUKU_PLEX_USERAGENT = 'plexapp.com v9.0'
subtitleExt       = ['utf','utf8','utf-8','sub','srt','smi','rt','ssa','aqt','jss','ass','idx']
 
def Start():
  HTTP.CacheTime = 0
  HTTP.Headers['User-agent'] = ZIMUKU_PLEX_USERAGENT
  Log.Debug("Zimuku Agent Start")

def fetchSubtitle(url):
  Log("fetching subtitle %s" % (url))
  folder, filename = os.path.split(url)  
  filename_without_extension, extension = os.path.splitext(filename)

  # check subtitle whether exists or not
  for ext in subtitleExt:
    subtitle = "%s.%s" % (filename_without_extension, ext)
    file_path = os.path.join(folder, subtitle)
    if os.path.exists(file_path):
      Log("subtitle file(s) has already existed.")
      return

  statinfo = os.stat(url)
  file = io.open(url, "rb")

  file_size = statinfo.st_size

  if (file_size < 8 * 1024):
    Log("It's impossible that video file length is less than 8k")
    return

  positions = []
  positions.append(4 * 1024)
  positions.append(file_size / 3)
  positions.append(file_size / 3 * 2)
  positions.append(file_size - (8 * 1024))

  hashes = []
  for p in positions:
    file.seek(p)
    byte_data = file.read(4 * 1024)
    hashes.append(hashlib.md5(byte_data).hexdigest())

  filehash = ';'.join(hashes)

  post_data = {'filehash' : filehash, 'pathinfo' : filename, 'format' : 'json', 'lang' : 'Chn'}
  # user_agent = "SPlayerX 1.1.8 (Build 1113)"
  headers = {'Content-Type' : 'application/x-www-form-urlencoded', 'User-Agent' : ZIMUKU_PLEX_USERAGENT}
  params = urllib.urlencode(post_data)

  req = urllib2.Request(ZIMUKU_API, params, headers)
  response = urllib2.urlopen(req)
  json_data = json.load(response)

  if len(json_data) == 0:
    Log('Wrong response from ZIMUKU API')
    return

  subtitles = []
  for json_obj in json_data:
    if len(json_obj['Files']) > 0:
      file_json = json_obj['Files'][0]
      subtitle_link = file_json['Link']
      subtitle_extension = file_json["Ext"]
      subtitle_filename = "%s.%s" % (filename_without_extension, subtitle_extension)
      subtitle_obj = {'ext' : subtitle_extension, 
                      'link' : subtitle_link,
                      'subtitle_filename' : subtitle_filename}
      subtitles.append(subtitle_obj)

  if len(subtitles) == 0:
    return

  subtitle_to_download = subtitles[0]
  for subtitle in subtitles:
    if subtitle['ext'] == 'ass':
      subtitle_to_download = subtitle
      break

  try :
    u = urllib2.urlopen(subtitle_to_download['link'])
    fileurl = os.path.join(folder, subtitle_to_download['subtitle_filename'])
    with io.open(fileurl, "wb") as subtitle_file:
      subtitle_file.write(u.read())
      
    Log.Debug("subtitle %s downloaded" % (subtitle_to_download['subtitle_filename']))

  except urllib2.HTTPError, e:
    Log("HTTP Error:", e.code, link)
  except urllib2.URLError, e:
    Log("URL Error:", e.reason, link)


class ZimukuAgentMovies(Agent.Movies):
  name = 'Zimuku.net'
  languages = [Locale.Language.Chinese]  
  primary_provider = False
  contributes_to = ['com.plexapp.agents.imdb']

  def search(self, results, media, lang):
    Log.Debug("ZimukuAgentMovies.search")
    results.Append(MetadataSearchResult(
      id    = "null",    
      score = 100
    ))
    
    
  def update(self, metadata, media, lang):
    Log.Debug("ZimukuAgentMovies.update")    
    for i in media.items:
      for part in i.parts:
        fetchSubtitle(part.file)

    

class ZimukuAgentTVShows(Agent.TV_Shows):
  name = 'Zimuku.net'
  languages = [Locale.Language.Chinese]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.thetvdb']

  def search(self, results, media, lang, manual):
    Log.Debug("ZimukuAgentTVShows.search")
    results.Append(MetadataSearchResult(
      id    = "null",    
      score = 100
    ))
    

  def update(self, metadata, media, lang, force):
    Log.Debug("ZimukuAgentTVShows.update")
    for s in media.seasons:
      # just like in the Local Media Agent, if we have a date-based season skip for now.
      if int(s) < 1900:
        for e in media.seasons[s].episodes:
          for i in media.seasons[s].episodes[e].items:
            for part in i.parts:
              fetchSubtitle(part.file)


