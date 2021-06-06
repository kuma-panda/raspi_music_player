import json
import os
import threading
import queue
import time
import math
from PIL import Image
from mpd import MPDClient
from enum import Enum


# ------------------------------------------------------------------------------
class Song:
    def __init__(self, album):
        self.__title = ''       # 曲名
        self.__track_index = 0  # トラックNo. (1がアルバムの先頭の曲)
        self.__duration = 0     # 曲の演奏時間(秒単位)
        self.__filename = ''    # ファイル名
        self.__album = album    # この曲が収録されているアルバム

    @property
    def album(self):
        return self.__album

    @property
    def filename(self):
        return self.__filename

    @property
    def path(self):
        return os.path.join(self.__album.path, self.__filename)

    @property
    def title(self):
        return self.__title

    @property
    def duration(self):
        return self.__duration

    @property
    def track_index(self):
        return self.__track_index

    def load(self, obj):
        self.__track_index = obj['index']
        self.__title = obj['title']
        self.__duration = obj['duration']
        self.__filename = obj['filename']

# ------------------------------------------------------------------------------
class Album:
    IMAGE_SIZE = (240, 240)

    def __init__(self, artist):
        self.__id = 0           # アルバムID
        self.__songs = []       # アルバムに収録されている曲のリスト
        self.__title = ''       # アルバムタイトル
        self.__total_time = 0   # 総演奏時間（各曲の演奏時間の総和、秒単位）
        self.__year = 0         # アルバムの発売年（西暦）
        self.__directory = ''   # フォルダ名（"trespass" など。フルパスではなくそのアルバムの曲が格納されたディレクトリ名であることに注意）
        self.__artist = artist  # このアルバムを所有するアーティスト
        self.__image = None     # カバーアート画像データ   

    @property
    def album_id(self):
        return self.__id

    @property
    def artist(self):
        return self.__artist

    @property
    def title(self):
        return self.__title

    @property
    def directory(self):
        return self.__directory

    @property
    def path(self):
        return os.path.join(self.__artist.path, self.__directory)

    @property
    def num_tracks(self):
        return len(self.__songs)

    @property
    def songs(self):
        return self.__songs

    @property
    def total_time(self):
        return self.__total_time

    @property
    def year(self):
        return self.__year

    @property
    def image(self):
        return self.__image

    def get_song(self, index):
        return self.__songs[index]

    def get_playlist(self):
        playlist = []
        for song in self.__songs:
            playlist.append(os.path.join(self.__artist.directory, self.__directory, song.filename))
            # playlist.append(song.path)
        return playlist

    def load(self, obj):
        self.__id = obj['id']
        self.__title = obj['title']
        self.__year = obj['year']
        self.__directory = obj['directory']
        self.__total_time = obj['totalTime']
        for track in obj['tracks']:
            song = Song(self)
            song.load(track)
            self.__songs.append(song)
        
        image_path = os.path.join(self.path, 'coverart.png')
        self.__image = Image.open(image_path).convert('RGB')
        # self.__image = src.resize(size=Album.IMAGE_SIZE, resample=Image.BICUBIC)

# ------------------------------------------------------------------------------
class Artist:
    ROOT_PATH = '/media/usb'
    IMAGE_SIZE = (180, 180)

    def __init__(self):
        self.__id = 0           # アーティストID
        self.__directory = ''   # ディレクトリ名
        self.__albums = []      # アルバムのリスト
        self.__name = ''        # アーティスト名
        self.__image = None     # アーティストの画像

    @property
    def artist_id(self):
        return self.__id
    
    @property
    def name(self):
        return self.__name

    @property
    def directory(self):
        return self.__directory

    @property
    def path(self):
        return Artist.ROOT_PATH + '/' + self.__directory

    @property
    def num_albums(self):
        return len(self.__albums)

    @property
    def albums(self):
        return self.__albums

    @property
    def image(self):
        return self.__image

    def load(self, obj):
        self.__id = obj['id']
        self.__name = obj['name']
        self.__directory = obj['directory']
        for a in obj['albums']:
            album = Album(self)
            album.load(a)
            self.__albums.append(album)
        image_path = os.path.join(Artist.ROOT_PATH, self.__directory, 'artist.png')
        self.__image = Image.open(image_path).convert('RGB')
        # self.__image = src.resize(size=Artist.IMAGE_SIZE, resample=Image.BICUBIC)

    def get_index_of_album(self, target):
        for i, a in enumerate(self.__albums):
            if a.album_id == target.album_id:
                return i
        return -1

    def get_album_of_index(self, index):
        return self.__albums[index]

    def get_album_by_id(self, target_id):
        return [a for a in self.__albums if a.album_id == target_id][0]

    def find_album(self, target_id):
        found = [a for a in self.__albums if a.album_id == target_id]
        return found[0] if len(found) > 0 else self.__albums[0]

# ------------------------------------------------------------------------------
class ArtistList:
    def __init__(self):
        self.__artists = []

    @property
    def num_artists(self):
        return len(self.__artists)

    @property
    def artists(self):
        return self.__artists

    def load(self, path):
        with open(path, 'r') as fp:
            obj = json.load(fp)
            for o in obj:
                artist = Artist()
                artist.load(o)
                self.__artists.append(artist)

    def find_album(self, target_album_id):
        for artist in self.__artists:
            album = artist.find_album(target_album_id)
            if album:
                return album
        return None
    
    def get_index_of_artist(self, target):
        for i, a in enumerate(self.__artists):
            if a.artist_id == target.artist_id:
                return i
        return -1

    def get_artist_of_index(self, index):
        return self.__artists[index]

    def get_artist_by_id(self, target_id):
        found = [a for a in self.__artists if a.artist_id == target_id]
        return found[0] if found else self.__artists[0]

# ------------------------------------------------------------------------------
class PlaybackState(Enum):
    STOP  = 'stop'
    PAUSE = 'pause'
    PLAY  = 'play'

# ------------------------------------------------------------------------------
class PlayerStatus:
    def __init__(self):
        self.__state = None
        self.__song = -1    # 0はアルバムの先頭の曲を示す
        self.__elapsed = 0
        self.__updating = False

    @property
    def state(self):
        return self.__state

    @property
    def song(self):
        return self.__song

    @property
    def elapsed(self):
        return self.__elapsed

    @property
    def updating(self):
        return self.__updating

    def update(self, status):
        # self.__volume = int(status.get('volume') or '0')
        self.__state = PlaybackState(status.get('state') or 'stop')
        self.__song = int(status.get('song') or '0')
        self.__elapsed = math.floor(float(status['elapsed'])) if 'elapsed' in status else 0
        self.__updating = True if 'updating_db' in status else False

    def copy(self, source):
        result = {}
        if self.__state != source.state:
            # state が変化したときは、全ての情報の更新を指示する
            result['state'] = source.state
            result['song'] = source.song
            result['elapsed'] = source.elapsed
            self.__state = source.state
        if self.__song != source.song:
            result['song'] = source.song
            self.__song = source.song
        if self.__elapsed != source.elapsed:
            result['elapsed'] = source.elapsed
            self.__elapsed = source.elapsed

        if result.get('state') == PlaybackState.STOP:
            result['song'] = 0
            result['elapsed'] = 0
        else:
            if ('song' in result) and self.__state in [PlaybackState.PLAY, PlaybackState.PAUSE]:
                result['song'] += 1

        return result


# ------------------------------------------------------------------------------
class Player:
    def __init__(self):
        self.__client = MPDClient()
        self.__client.timeout = 10
        self.__client.idletimeout = None
        self.__client.connect('localhost', 6600)
        self.__status = PlayerStatus()
        # self.__volume = None
        self.__lock = threading.Lock()
        self.__queue = queue.Queue()
        self.__terminated = False
        self.__thread = threading.Thread(target=self.update)
        self.__thread.start()

    @property
    def status(self):
        s = PlayerStatus()
        self.__lock.acquire()
        try:
            s.copy(self.__status)
        except:
            pass
        finally:
            self.__lock.release()
        return s

    def quit(self):
        self.stop()
        self.__terminated = True
        self.__thread.join()
        print('Player: terminated')

    def update(self):
        s = PlayerStatus()
        while not self.__terminated:
            time.sleep(0.1)
            self.__lock.acquire()
            try:
                s.update(self.__client.status())
                modified = self.__status.copy(s)
                if modified:
                    self.__queue.put(modified)
                # if self.__volume is None:
                #     self.__volume = self.__status.volume
            except:
                pass
            finally:
                self.__lock.release()

    def get_modified(self):
        return self.__queue.get() if not self.__queue.empty() else None

    def set_album(self, album):
        playlist = album.get_playlist()
        self.__lock.acquire()
        try:
            self.__client.command_list_ok_begin()
            self.__client.stop()
            self.__client.clear()
            # self.__client.add('muon.mp3')
            # self.__client.add('{}/muon.mp3'.format(Artist.ROOT_PATH))
            for url in playlist:
                print(url)
                self.__client.add(url)
            self.__client.command_list_end()
        except:
            pass
        finally:
            self.__lock.release()

    def play(self, song):   # song はゼロが１曲目
        self.__lock.acquire()
        try:
            self.__client.play(song)
        except:
            pass
        finally:
            self.__lock.release()

    def toggle_pause(self):
        self.__lock.acquire()
        try:
            if self.__status.state == PlaybackState.PAUSE:
                self.__client.play()
            elif self.__status.state == PlaybackState.PLAY:
                self.__client.pause()
        except:
            pass
        finally:
            self.__lock.release()

    def next(self):
        self.__lock.acquire()
        try:
            self.__client.next()
        except:
            pass
        finally:
            self.__lock.release()
    
    def previous(self):
        self.__lock.acquire()
        try:
            self.__client.previous()
        except:
            pass
        finally:
            self.__lock.release()

    def stop(self):
        self.__lock.acquire()
        try:
            self.__client.stop()
        except:
            pass
        finally:
            self.__lock.release()

    # def set_volume(self, vol):
    #     self.__lock.acquire()
    #     try:
    #         self.__client.setvol(vol)
    #     except:
    #         pass
    #     finally:
    #         self.__lock.release()

    # def set_volume_delta(self, delta):
    #     if (delta in [-1, 1]) and (not self.__volume is None):
    #         self.__volume += delta
    #         self.set_volume(self.__volume)

    def update_db(self):
        self.stop()
        print('start update')
        self.__lock.acquire()
        try:
            self.__client.update()
        except:
            print('update failed')
            pass
        finally:
            self.__lock.release()
        print('waiting for beginning to update ...')
        while True:
            self.__lock.acquire()
            try:
                s = self.__client.status()
            except:
                pass
            finally:
                self.__lock.release()
            if 'updateing_db' in s:
                break
            time.sleep(0.1)
        print('updating database ...')
        while True:
            self.__lock.acquire()
            try:
                s = self.__client.status()
            except:
                pass
            finally:
                self.__lock.release()
            if 'updateing_db' not in s:
                break
            time.sleep(0.1)
        print('done.')

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    artist_list = ArtistList()
    artist_list.load('/media/usb/database.json')
    # for artist in artist_list.artists:
    #     print('[{0: >3}] {1}'.format(artist.artist_id, artist.name))
    #     for album in artist.albums:
    #         print('    [{0: >3}] {1}'.format(album.album_id, album.title))
    #         print('    {}'.format(album.year))
    #         print('    {0:0>2}:{1:0>2}'.format(album.total_time//60, album.total_time%60))
    #         for song in album.songs:
    #             print('      {: >2} {}'.format(song.track_index, song.title))

    player = Player()
    artist = artist_list.get_artist_by_id(3800)
    album = artist.get_album_by_id(3804)
    player.set_album(album)
    time.sleep(1)
    player.play(0)
