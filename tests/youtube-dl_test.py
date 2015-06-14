'''
Created on 12 May 2015

@author: ooe
'''

import youtube_dl
youtube_url = "http://www.youtube.com/watch?v=wTcNtgA6gHs"

format = "bestvideo"
opts = {
 'format' : format,
 'skip_download' : True,
 'writeinfojson' : True,
 'quiet' : True
}
with youtube_dl.YoutubeDL(opts) as ydl:
    ydl.download([youtube_url])
    print ydl.url
    

