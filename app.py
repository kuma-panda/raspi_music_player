import pygame
import os
import sys
import time
import json
import shutil
import subprocess
import RPi.GPIO as GPIO

from player import ArtistList, Player
from ui     import UIWidget, Desktop, TouchManager
from view   import NavigationView, ArtistListView, AlbumListView, PlaybackView

class Application:
    CONFIG_PATH = '/home/pi/player/config.json'

    def __init__(self):
        self.__terminated = False

        self.__artist_list = ArtistList()
        self.__artist_list.load('/media/usb/database.json')
        
        self.__player = Player()
        
        self.__touch = TouchManager()

        self.__desktop = Desktop()
        
        self.__navigation_view = NavigationView(self.__desktop, self.__player)
        self.__navigation_view.attach_event('shutdown', self.shutdown)
        
        self.__artist_listview = ArtistListView(self.__desktop, self.__artist_list)
        self.__artist_listview.attach_event('select', self.select_artist)
        self.__artist_listview.attach_event('close', self.show_playback)
        self.__artist_listview.hide()
        
        self.__album_listview = AlbumListView(self.__desktop)
        self.__album_listview.attach_event('select', self.select_album)
        self.__album_listview.attach_event('close', self.show_playback)
        self.__album_listview.hide()

        self.__playback_view = PlaybackView(self.__desktop, self.__player)
        self.__playback_view.attach_event('album', self.show_album_list)
        self.__playback_view.attach_event('artist', self.show_artist_list)

    def load_config(self):
        if os.path.isfile(self.CONFIG_PATH):
            with open(self.CONFIG_PATH, mode='r', encoding='utf-8') as fp:
                config = json.load(fp)
            artist = self.__artist_list.get_artist_by_id(config['artist'])
            album  = artist.get_album_by_id(config['album'])
        else:
            artist = self.__artist_list.artists[0]
            album = artist.albums[0]
        self.select_album(album)

    def save_config(self):
        with open(self.CONFIG_PATH, mode='w', encoding='utf-8') as fp:
            config = {
                'artist': self.__playback_view.album.artist.artist_id,
                'album': self.__playback_view.album.album_id
            }
            json.dump(config, fp, ensure_ascii=False, indent=4)

    def run(self):
        self.load_config()

        self.__desktop.show()
        self.__touch.add_event_listener(self.__desktop)
        
        while not self.__terminated:
            modified_states = self.__player.get_modified() or {}
            if self.__touch.dispatch_event():
                UIWidget.timer.reset()
            widget = UIWidget.timer.get_expired()
            if widget:
                widget.on_timeout()
            self.__navigation_view.update(modified_states)
            self.__playback_view.update(modified_states)
            time.sleep(0.1)

        self.__touch.quit()
        self.__touch = None
        self.__desktop = None
        UIWidget.timer.quit()
        pygame.quit()
        self.__player.quit()
        self.save_config()

    def shutdown(self, params):
        self.__terminated = True

    def select_artist(self, artist):
        self.__album_listview.set_artist(artist)
        self.__artist_listview.hide()
        self.__album_listview.show()

    def select_album(self, album):
        self.__player.set_album(album)
        self.__playback_view.set_album(album)
        self.__album_listview.hide()
        self.__playback_view.show()

    def show_album_list(self, album):
        self.__album_listview.set_artist(album.artist, album)
        self.__playback_view.hide()
        self.__album_listview.show()

    def show_artist_list(self, artist):
        self.__artist_listview.set_page(current_artist=artist)
        self.__playback_view.hide()
        self.__artist_listview.show()

    def show_playback(self, param):
        self.__artist_listview.hide()
        self.__album_listview.hide()
        self.__playback_view.show()

if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(26, GPIO.OUT)
    GPIO.output(26, True)
    app = Application()
    app.run()
    GPIO.output(26, False)
    subprocess.run(['/usr/bin/sudo', '/usr/sbin/shutdown', '-h', 'now'])
