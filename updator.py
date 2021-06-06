import mutagen
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
import glob
import os
import json
from functools import cmp_to_key
from PIL import Image

class AlbumFolder:
    def __init__(self, root, album_id):
        self.__id = album_id
        self.__root_path = root
        self.__songs = []
        self.__total_time = 0

    @property
    def artist_name(self):
        return self.__songs[0]['artist']
    @property
    def year(self):
        return self.__songs[0]['year']
    @property
    def title(self):
        return self.__songs[0]['album']

    def get_cover_image(self):
        image_path = os.path.join(self.__root_path, 'coverart.png')
        if not os.path.isfile(image_path):
            return None
        return Image.open(image_path)

    def parse_files(self):
        music_files = [f for f in glob.glob('{}/*'.format(self.__root_path)) if os.path.splitext(f)[-1].lower() in ['.mp3', '.m4a', '.flac']]
        for music_file in music_files:
            # print(music_file)
            ext = os.path.splitext(music_file)[-1].lower()
            song = {'filename': os.path.split(music_file)[-1]}
            if 'mp3' in ext:
                f = MP3(music_file)
                song['duration'] = round(f.info.length)
                song['artist'] = str(f['TPE1'].text[0])
                song['album'] = str(f['TALB'].text[0])
                song['title'] = str(f['TIT2'].text[0])
                song['year'] = int(str(f['TDRC'].text[0]))
                song['index'] = int(str(f['TRCK'].text[0]).split('/')[0])
            elif 'm4a' in ext:
                f = MP4(music_file)
                song['duration'] = round(f.info.length)
                song['artist'] = f['\xa9ART'][0]
                song['album'] = f['\xa9alb'][0]
                song['title'] = f['\xa9nam'][0]
                song['year'] = int(f['\xa9day'][0])
                song['index'] = int(f['trkn'][0][0])
            elif 'flac' in ext:
                f = FLAC(music_file)
                song['duration'] = round(f.info.length)
                song['artist'] = f['artist'][0]
                song['album'] = f['album'][0]
                song['title'] = f['title'][0]
                song['year'] = int(f['date'][0])
                song['index'] = int(f['tracknumber'][0])
            self.__songs.append(song)
        self.__songs.sort(key=lambda d: d['index'])
        self.__total_time = sum([s['duration'] for s in self.__songs])

    def to_json(self):
        return {
            'id': self.__id,
            'title': self.__songs[0]['album'],
            'year': self.__songs[0]['year'],
            'directory': os.path.split(self.__root_path)[-1],
            'totalTime': self.__total_time,
            'tracks': self.__songs
        }

class ArtistFolder:
    def __init__(self, root, artist_id):
        self.__id = artist_id
        self.__root_path = root
        self.__albums = []
    
    @property
    def directory(self):
        return os.path.split(self.__root_path)[-1]
    @property
    def name(self):
        return self.__albums[0].artist_name
    @property
    def albums(self):
        return self.__albums

    def parse_files(self):
        album_folders = [f for f in glob.glob('{}/*'.format(self.__root_path)) if os.path.isdir(f)]
        if album_folders:
            album_folders.sort()
            for i, folder in enumerate(album_folders, self.__id+1):
                # if os.path.isdir(folder):
                album = AlbumFolder(folder, i)
                album.parse_files()
                self.__albums.append(album) 

        def cmp(a, b):
            if a.year == b.year:
                return -1 if a.title < b.title else 1
            return -1 if a.year < b.year else 1

        self.__albums.sort(key=cmp_to_key(cmp)) #key=lambda d: d.year)

        print(self.name)
        for album in self.__albums:
            img = album.get_cover_image()
            print('  {}  {}'.format(
                album.title,
                '(Image: {}*{})'.format(*img.size) if img else ' ************ ERROR: no coverart image ************'    
            ))

        image_path = os.path.join(self.__root_path, 'artist.png')
        if os.path.isfile(image_path):
            i = Image.open(image_path)
            print('  artist.png ({} * {})'.format(*i.size))
        else:
            print('  ********** ERROR: artist.png not found **********')
        print()

    def to_json(self):
        return {
            'id': self.__id,
            'name': self.__albums[0].artist_name,
            'directory': os.path.split(self.__root_path)[-1],
            'albums': [album.to_json() for album in self.__albums]
        }

def update(root_path, outname='database.json', callback=None):
    print('updating {}'.format(outname))
    try:
        artists = []
        directories = [d for d in glob.glob('{}/*'.format(root_path)) if os.path.isdir(d)]
        i = 100
        if callback:
            callback(0, len(directories))
        for n, directory in enumerate(directories, 1):
            artist = ArtistFolder(directory, i)
            artist.parse_files() 
            # print(artist.name)
            # for album in artist.albums:
            #     print('  {}'.format(album.title))
            artists.append(artist)
            if callback:
                callback(n, len(directories))
            i += 100
        artists.sort(key=lambda d: d.directory.lower())
        path = '{}/{}'.format(root_path, outname)
        with open(path, mode='w', encoding='utf-8') as fp:
            json.dump([artist.to_json() for artist in artists], fp, indent=4, ensure_ascii=False)

    except Exception as e:
        raise
        # print(e)
        # return False

    print('{} successfully updated'.format(outname))
    return True

if __name__ == '__main__':
    def cb(pos, total):
        print('{} / {}'.format(pos, total))

    if update('/media/usb', outname='database.json'): #, callback=cb):
        print('done')



