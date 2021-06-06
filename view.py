from ui import TextAlign
from ui import Canvas
from ui import TouchManager
from ui import UIWidget
from ui import Desktop
from ui import Popup
from ui import Button
from ui import Label
from ui import PaintBox

from player import PlaybackState

from PIL import Image
import pygame
import time
import datetime


# ------------------------------------------------------------------------------
class NavigationView(UIWidget):
    BKCOL = (0, 0, 0)
    FGCOL = (0x9E, 0xA1, 0xA3)

    def __init__(self, parent, player):
        super().__init__(parent)
        
        self.__player = player

        self.__state_box = PaintBox(self, self.draw_state)
        self.__song_label = Label(self)
        self.__elapsed_label = {
            'mm': Label(self),
            'ss': Label(self)
        }

        self.__buttons = {
            'play/stop': Button(self, icon='play'),
            'pause':     Button(self, icon='pause'),
            'previous':  Button(self, icon='skip-previous'),
            'next':      Button(self, icon='skip-next'),
            'power':     Button(self, icon='power')
        }

        self.__buttons['play/stop'].attach_event('click', self.on_play_stop)
        self.__buttons['pause'    ].attach_event('click', self.on_pause)
        self.__buttons['previous' ].attach_event('click', self.on_previous)
        self.__buttons['next'     ].attach_event('click', self.on_next)
        self.__buttons['power'    ].attach_event('click', self.on_poweroff)

        w, h = 64, 64
        self.create((0, 0, Canvas.SCREEN_WIDTH, h))

        self.__state_box.create((0, 0, w, h))
        self.__song_label.create((200, 0, 90, h))
        self.__song_label.canvas.set_font_size('sseg')
        self.__song_label.text = '99'
        self.__song_label.text_color = self.FGCOL
        self.__song_label.back_color = self.BKCOL
        self.__song_label.alignment = TextAlign.MIDDLE

        self.__elapsed_label['mm'].create((400, 0, 90, h))
        self.__elapsed_label['mm'].canvas.set_font_size('sseg')
        self.__elapsed_label['mm'].text = '99'
        self.__elapsed_label['mm'].text_color = self.FGCOL
        self.__elapsed_label['mm'].back_color = self.BKCOL
        self.__elapsed_label['mm'].alignment = TextAlign.MIDDLE|TextAlign.RIGHT

        self.__elapsed_label['ss'].create((530, 0, 90, h))
        self.__elapsed_label['ss'].canvas.set_font_size('sseg')
        self.__elapsed_label['ss'].text = '99'
        self.__elapsed_label['ss'].text_color = self.FGCOL
        self.__elapsed_label['ss'].back_color = self.BKCOL
        self.__elapsed_label['ss'].alignment = TextAlign.MIDDLE|TextAlign.LEFT

        self.__buttons['play/stop'].create((Canvas.SCREEN_WIDTH-w*5, 0, w, h))  # 704
        self.__buttons['previous' ].create((Canvas.SCREEN_WIDTH-w*4, 0, w, h))  # 768
        self.__buttons['pause'    ].create((Canvas.SCREEN_WIDTH-w*3, 0, w, h))  # 832
        self.__buttons['next'     ].create((Canvas.SCREEN_WIDTH-w*2, 0, w, h))  # 896
        self.__buttons['power'    ].create((Canvas.SCREEN_WIDTH-w,   0, w, h))  # 960

        self.__playback_state = PlaybackState.STOP

    def draw(self):
        super().draw()
        self.canvas.clear(self.BKCOL)
        self.canvas.set_font_size(20)
        self.canvas.draw_text_rect((100, 2, 80, 30), 'track', TextAlign.RIGHT, self.FGCOL)
        self.canvas.draw_text_rect((300, 2, 80, 30), 'time',  TextAlign.RIGHT, self.FGCOL)
        self.canvas.draw_circle((512, 16), 6, self.FGCOL)
        self.canvas.draw_circle((508, 48), 6, self.FGCOL)
        # self.canvas.fill_rect((0, 48, Canvas.SCREEN_WIDTH, 2), (0x59, 0x58, 0x57))

    def draw_state(self, target):
        target.canvas.clear(self.BKCOL)
        target.canvas.draw_icon_center('large', (32, 32), self.__playback_state.value, self.FGCOL, self.BKCOL)
 
    def on_play_stop(self, param):
        if self.__buttons['play/stop'].icon == 'play':
            self.__player.play(0)
            self.trigger_event('play')
            self.__buttons['play/stop'].icon = 'stop'
        else:
            self.__player.stop()
            self.trigger_event('stop')
            self.__buttons['play/stop'].icon = 'play'
    
    def on_pause(self, param):
        self.__player.toggle_pause()
        self.trigger_event('pause')

    def on_previous(self, param):
        self.__player.previous()
        self.trigger_event('previous')

    def on_next(self, param):
        self.__player.next()
        self.trigger_event('next')

    def on_poweroff(self, param):
        self.trigger_event('shutdown')

    def update(self, modified):
        for key in modified:
            if key == 'state':
                self.__playback_state = modified[key]
                self.__state_box.refresh()
                if modified[key] == PlaybackState.STOP:
                    self.__song_label.text = '00'
                    self.__elapsed_label['mm'].text = '00'
                    self.__elapsed_label['ss'].text = '00'
                    self.__buttons['play/stop'].icon = 'play'
                else:
                    self.__buttons['play/stop'].icon = 'stop'
            if key == 'song':
                s = '{:0>2}'.format(modified[key])
                self.__song_label.text = s
            if key == 'elapsed':
                t = modified[key]
                # if self.__song_label.text == '00':
                #     t = 0
                self.__elapsed_label['mm'].text = '{:0>2}'.format(t//60)
                self.__elapsed_label['ss'].text = '{:0>2}'.format(t%60)


# ------------------------------------------------------------------------------
class ArtistListView(UIWidget):
    BKCOL = (0, 0, 0)
    HEADER_FGCOL = (0x81, 0x80, 0xB2)
    HEADER_BKCOL = [(0x1B, 0x1A, 0x59), (0x0A, 0x09, 0x3B)]
    NUM_PANELS = 6

    def __init__(self, parent, artist_list):
        super().__init__(parent)
        self.__artist_list = artist_list
        self.__current_artist = None
        self.__page = 0
        self.__buttons = {
            'up': Button(self, icon='chevron-up'),
            'close': Button(self, icon='close'),
            'down': Button(self, icon='chevron-down')
        }
        self.__buttons['up'].attach_event('click', self.on_up)
        self.__buttons['close'].attach_event('click', self.on_close)
        self.__buttons['down'].attach_event('click', self.on_down)

        self.__header = PaintBox(self, self.draw_header)

        self.__panels = [Button(self) for i in range(self.NUM_PANELS)]
        for n, panel in enumerate(self.__panels):
            panel.tag = {'index': n, 'artist': None, 'current': False}
            panel.set_customdraw(self.draw_panel)
            panel.attach_event('click', self.on_select)

        self.create((0, 64, Canvas.SCREEN_WIDTH, Canvas.SCREEN_HEIGHT-64))
        self.__header.create((0, 0, Canvas.SCREEN_WIDTH, 30))
        w, h = 64, 56
        self.__buttons['up'   ].create((224, 480, w, h))
        self.__buttons['close'].create((480, 480, w, h))
        self.__buttons['down' ].create((736, 480, w, h))
        for panel in self.__panels:
            x = (panel.tag['index'] % 2)*512
            y = 30 + (panel.tag['index'] // 2)*150
            panel.create((x, y, 512, 150))

    def show(self):
        super().show()
        self.set_timeout(30, True)

    def on_timeout(self):
        self.trigger_event('close')

    def set_page(self, *, page=0, current_artist=None):
        if current_artist:
            self.__current_artist = current_artist
            found = [i for i, artist in enumerate(self.__artist_list.artists) if artist.artist_id == current_artist.artist_id]
            if found:
                self.__page = found[0] // self.NUM_PANELS
            else:
                self.__page = 0
        else:
            self.__page = page
        artists = self.__artist_list.artists[self.__page*self.NUM_PANELS:]
        if len(artists) <= self.NUM_PANELS:
            self.__buttons['down'].disable()
            artists += [None for i in range(self.NUM_PANELS)]
        else:
            self.__buttons['down'].enable()
        if self.__page == 0:
            self.__buttons['up'].disable()
        else:
            self.__buttons['up'].enable()
        artists = artists[:self.NUM_PANELS]
        for panel, artist in zip(self.__panels, artists):
            panel.tag['artist'] = artist
            if artist:
                if self.__current_artist and (artist.artist_id == self.__current_artist.artist_id):
                    panel.tag['current'] = True
                else:
                    panel.tag['current'] = False
                panel.enable()
            else:
                panel.tag['current'] = False
                panel.disable()
        self.refresh()        

    def draw_header(self, header):
        header.canvas.clear(self.HEADER_BKCOL[0])
        n = len(self.__artist_list.artists)
        s = self.__page * self.NUM_PANELS + 1
        e = min([s + self.NUM_PANELS - 1, n])
        header.canvas.set_font_size(20)
        text = 'アーティスト ({} - {} / {})'.format(s, e, n)
        header.canvas.draw_text_rect((20, 0, 1000, 30), text, TextAlign.MIDDLE, self.HEADER_FGCOL)

    def draw_panel(self, panel):
        artist = panel.tag['artist']
        if not artist:
            panel.canvas.clear(self.BKCOL)
            return
        fgcol, bkcol = self.HEADER_FGCOL, self.HEADER_BKCOL[1] if panel.tag['current'] else self.BKCOL
        if panel.captured:
            fgcol, bkcol = self.HEADER_FGCOL, self.HEADER_BKCOL[0]
        panel.canvas.clear(bkcol)
        r = panel.client_rect.copy()
        panel.canvas.set_font_size(20)
        panel.canvas.draw_text((12, 20), artist.name, fgcol)
        panel.canvas.draw_text((12, 60), '{} album(s)'.format(len(artist.albums)), fgcol)
        panel.canvas.draw_rect((r.width-149, 1, 148, 148), (0x56, 0x56, 0x56))
        image = artist.image.resize((146, 146), resample=Image.BICUBIC)
        panel.canvas.draw_image(image, (r.width-148, 2, 146, 146))

    def on_up(self, param):
        self.set_page(page=self.__page-1)

    def on_down(self, param):
        self.set_page(page=self.__page+1)

    def on_close(self, param):
        self.trigger_event('close')

    def on_select(self, panel):
        artist = panel.tag['artist']
        if artist:
            print(artist.name)
            self.trigger_event('select', artist)


# ------------------------------------------------------------------------------
class AlbumListView(UIWidget):
    BKCOL = (0, 0, 0)
    HEADER_FGCOL = (0x88, 0xCC, 0x88)
    HEADER_BKCOL = [(0x11, 0x66, 0x11), (0x00, 0x44, 0x00)]
    NUM_PANELS = 6

    def __init__(self, parent):
        super().__init__(parent)
        # self.hide()
        self.__artist = None
        self.__current_album = None
        self.__page = 0

        self.__buttons = {
            'up': Button(self, icon='chevron-up'),
            'close': Button(self, icon='close'),
            'down': Button(self, icon='chevron-down')
        }
        self.__buttons['up'].attach_event('click', self.on_up)
        self.__buttons['close'].attach_event('click', self.on_close)
        self.__buttons['down'].attach_event('click', self.on_down)

        self.__header = PaintBox(self, self.draw_header)

        self.__panels = [Button(self) for i in range(self.NUM_PANELS)]
        for n, panel in enumerate(self.__panels):
            panel.tag = {'index': n, 'album': None, 'current': False}
            panel.set_customdraw(self.draw_panel)
            panel.attach_event('click', self.on_select)

        self.create((0, 64, Canvas.SCREEN_WIDTH, Canvas.SCREEN_HEIGHT-64))
        self.__header.create((0, 0, Canvas.SCREEN_WIDTH, 30))
        w, h = 64, 56
        self.__buttons['up'   ].create((224, 480, w, h))
        self.__buttons['close'].create((480, 480, w, h))
        self.__buttons['down' ].create((736, 480, w, h))
        for panel in self.__panels:
            x = (panel.tag['index'] % 2)*512
            y = 30 + (panel.tag['index'] // 2)*150
            panel.create((x, y, 512, 150))

    def show(self):
        super().show()
        self.set_timeout(30, True)

    def on_timeout(self):
        self.trigger_event('close')

    def set_page(self, page):
        self.__page = page
        albums = self.__artist.albums[page*self.NUM_PANELS:]
        if len(albums) <= self.NUM_PANELS:
            self.__buttons['down'].disable()
            albums += [None for i in range(self.NUM_PANELS)]
        else:
            self.__buttons['down'].enable()
        if page == 0:
            self.__buttons['up'].disable()
        else:
            self.__buttons['up'].enable()
        albums = albums[:self.NUM_PANELS]
        for panel, album in zip(self.__panels, albums):
            panel.tag['album'] = album
            if album:
                panel.enable()
                if self.__current_album and self.__current_album.album_id == album.album_id:
                    panel.tag['current'] = True
                else:
                    panel.tag['current'] = False
            else:
                panel.disable()
                panel.tag['current'] = False
        self.refresh()        

    def set_current(self, current_album):
        self.__current_album = current_album
        found = [i for i, album in enumerate(self.__artist.albums) if album.album_id == self.__current_album.album_id]
        if not found:
            self.set_page(0)
            return
        page = found[0] // self.NUM_PANELS
        self.set_page(page)

    def draw_header(self, header):
        header.canvas.clear(self.HEADER_BKCOL[0])
        header.canvas.set_font_size(20)
        if self.__artist:
            text = '"{}" のアルバム ({})'.format(self.__artist.name, len(self.__artist.albums))
            header.canvas.draw_text_rect((20, 0, 1000, 30), text, TextAlign.MIDDLE, self.HEADER_FGCOL)

    def draw_panel(self, panel):
        album = panel.tag['album']
        if not album:
            panel.canvas.clear(self.BKCOL)
            return
        fgcol, bkcol = self.HEADER_FGCOL, self.HEADER_BKCOL[1] if panel.tag['current'] else self.BKCOL
        if panel.captured:
            fgcol, bkcol = self.HEADER_FGCOL, self.HEADER_BKCOL[0]
        panel.canvas.clear(bkcol)
        r = panel.client_rect.copy()
        panel.canvas.set_font_size(20)
        panel.canvas.draw_text_rect_wrap((12, 15, 340, 70), album.title, TextAlign.LEFT, fgcol)    #((12, 20), album.title, fgcol)
        panel.canvas.set_font_size(18)
        panel.canvas.draw_text_rect((12, 90, 340, 30), str(album.year), TextAlign.RIGHT, fgcol)
        text = '{0} tracks / {1:0>2}:{2:0>2}'.format(album.num_tracks, album.total_time // 60, album.total_time % 60)
        panel.canvas.draw_text_rect((12, 120, 340, 30), text, TextAlign.RIGHT, fgcol)
        panel.canvas.draw_rect((r.width-149, 1, 148, 148), (0x56, 0x56, 0x56))
        image = album.image.resize((146, 146), resample=Image.BICUBIC)
        panel.canvas.draw_image(image, (r.width-148, 2, 146, 146))

    def on_up(self, param):
        self.set_page(self.__page - 1)

    def on_down(self, param):
        self.set_page(self.__page + 1)

    def on_close(self, param):
        self.trigger_event('close')

    def on_select(self, panel):
        current = panel.tag['current']
        if current:
            # タップしたアルバムは現在演奏中のアルバムなので、そのまま閉じる
            self.trigger_event('close')
            return
        album = panel.tag['album']
        if album:
            print(album.title)
            self.trigger_event('select', album)

    def set_artist(self, artist, album=None):
        self.__artist = artist
        if album:
            self.set_current(album)
        else:
            self.__current_album = None
            self.set_page(0)


# ------------------------------------------------------------------------------
class PlaybackView(UIWidget):
    BKCOL = (0, 0, 0)
    FGCOL = (0x9E, 0xA1, 0xA3)
    # PANEL_BKCOL = [(0x38, 0x38, 0x00), (0, 0, 0), (0x80, 0x65, 0x15)]
    # PANEL_FGCOL = (0xFF, 0xEA, 0xAA)
    PANEL_BKCOL = [(0x29, 0x02, 0x38), (0, 0, 0), (0x6C, 0x22, 0x81)]
    PANEL_FGCOL = (0xFF, 0xDD, 0xFF)

    NUM_PANELS = 5

    def __init__(self, parent, player):
        super().__init__(parent)
        self.__player = player
        self.__album = None
        # self.hide()

        self.__labels = {
            'album_title': Label(self),
            'artist_name': Label(self),
            'year':        Label(self),
            'info':        Label(self)
        }
        self.__image = PaintBox(self, self.draw_image)
        self.__track_panels = [Button(self) for i in range(self.NUM_PANELS)]
        self.__buttons = {
            'up': Button(self, icon='chevron-up'),
            'down': Button(self, icon='chevron-down'),
            'artist': Button(self, icon='account'),
            'album': Button(self, icon='playlist-audio')
        }
        self.__buttons['up'    ].attach_event('click', self.scroll_up)
        self.__buttons['down'  ].attach_event('click', self.scroll_down)
        self.__buttons['artist'].attach_event('click', self.on_view_artist)
        self.__buttons['album' ].attach_event('click', self.on_view_album)

        self.create((0, 64, Canvas.SCREEN_WIDTH, Canvas.SCREEN_HEIGHT-64))
        self.__labels['album_title'].create((10, 10, Canvas.SCREEN_WIDTH-20, 30))
        self.__labels['artist_name'].create((10, 40, Canvas.SCREEN_WIDTH-20, 30))
        self.__labels['year'       ].create((Canvas.SCREEN_WIDTH-250, 340, 240, 30))
        self.__labels['info'       ].create((Canvas.SCREEN_WIDTH-250, 370, 240, 30))
        for label, size in zip(self.__labels.values(), [24, 24, 18, 18]):
            label.alignment = TextAlign.RIGHT|TextAlign.MIDDLE
            label.canvas.set_font_size(size)
            label.text_color = self.FGCOL
            label.back_color = self.BKCOL

        self.__image.create((Canvas.SCREEN_WIDTH-250, 80, 240, 240))
        
        '''
        600 - 64 = 536
        536 - (80 + 56) = 400
        '''
        w, h = Canvas.SCREEN_WIDTH-260, 80
        y = 80
        for i, panel in enumerate(self.__track_panels):
            panel.tag = {'index': i, 'song': None, 'selected': False}
            panel.set_customdraw(self.draw_panel)
            panel.attach_event('click', self.on_select)
            panel.create((0, y, w, h))
            y += h

        w, h = 64, 56
        self.__buttons['up'    ].create((255-32, 480, w, h))
        self.__buttons['down'  ].create((509-32, 480, w, h))
        self.__buttons['artist'].create((896,    480, w, h))
        self.__buttons['album' ].create((960,    480, w, h))

    @property
    def album(self):
        return self.__album

    def draw(self):
        super().draw()
        self.canvas.draw_rect((Canvas.SCREEN_WIDTH-251, 79, 242, 242), (0x56, 0x56, 0x56))

    def draw_image(self, panel):
        if self.__album:
            image = self.__album.image.resize((240, 240), resample=Image.BICUBIC)
            panel.canvas.draw_image(image, panel.client_rect)
        else:
            panel.canvas.clear(self.BKCOL)

    def draw_panel(self, panel):
        song = panel.tag['song']
        selected = panel.tag['selected']
        index = panel.tag['index']
        if not song:
            panel.canvas.clear(self.PANEL_BKCOL[index % 2])
            return

        fgcol = self.PANEL_FGCOL if selected else self.FGCOL
        if panel.captured or selected:
            bkcol = self.PANEL_BKCOL[2]
        else:
            bkcol = self.PANEL_BKCOL[index % 2]
        panel.canvas.clear(bkcol)
        panel.canvas.set_font_size(20)
        r = panel.client_rect
        panel.canvas.draw_text_rect((0, 10, 50, 30), '{:0>2}.'.format(song.track_index), TextAlign.RIGHT, fgcol)
        panel.canvas.draw_text_rect_wrap((60, 10, r.width-120, 60), song.title, TextAlign.TOP|TextAlign.LEFT, fgcol)
        panel.canvas.set_font_size(18)
        text = '{0:0>2}:{1:0>2}'.format(song.duration // 60, song.duration % 60)
        panel.canvas.draw_text_rect((r.width-70, 50, 60, 30), text, TextAlign.RIGHT, fgcol)

    def set_album(self, album):
        self.__album = album
        for panel in self.__track_panels:
            panel.tag['song'] = None
        self.scroll_into_view(1, 1)
        self.__image.refresh()
        self.__labels['album_title'].text = album.title
        self.__labels['artist_name'].text = album.artist.name
        self.__labels['year'].text = 'released : {}'.format(album.year)
        self.__labels['info'].text = '{0} tracks / {1:0>2}:{2:0>2}'.format(album.num_tracks, album.total_time // 60, album.total_time % 60)

    def on_select(self, panel):
        index = panel.tag['song'].track_index - 1
        self.__player.play(index)

    def on_view_album(self, param):
        self.trigger_event('album', self.__album)

    def on_view_artist(self, param):
        self.trigger_event('artist', self.__album.artist)

    def scroll_down(self, param):
        if not self.__album:
            return
        last_song = self.__track_panels[-1].tag['song']
        if (not last_song) or last_song.track_index >= self.__album.num_tracks:
            return
        for i, panel in enumerate(self.__track_panels[:-1]):
            # tag ごとコピーしてはならない点に注意（'index'プロパティはコピーしてはいけない）
            panel.tag['song'] = self.__track_panels[i+1].tag['song']
            panel.tag['selected'] = self.__track_panels[i+1].tag['selected']
            panel.refresh()
        bottom_panel = self.__track_panels[-1]
        bottom_panel.tag['song'] = self.__album.songs[last_song.track_index]
        bottom_panel.refresh()
        self.unselect_all()
        status = self.__player.status
        if status.state != PlaybackState.STOP:
            self.select(status.song+1)
        self.__buttons['up'].enable()
        if bottom_panel.tag['song'].track_index >= self.__album.num_tracks:
            self.__buttons['down'].disable()
        self.__buttons['up'].refresh()
        self.__buttons['down'].refresh()

    def scroll_up(self, param):
        if not self.__album:
            return
        first_song = self.__track_panels[0].tag['song']
        if (not first_song) or first_song.track_index <= 1:
            return
        for i, panel in zip(reversed(list(range(self.NUM_PANELS))), reversed(self.__track_panels[1:])):
            # tag ごとコピーしてはならない点に注意（'index'プロパティはコピーしてはいけない）
            panel.tag['song'] = self.__track_panels[i-1].tag['song']
            panel.tag['selected'] = self.__track_panels[i-1].tag['selected']
            panel.refresh()
        top_panel = self.__track_panels[0]
        top_panel.tag['song'] = self.__album.songs[first_song.track_index-2]
        top_panel.refresh()
        self.unselect_all()
        status = self.__player.status
        if status.state != PlaybackState.STOP:
            self.select(status.song+1)
        self.__buttons['down'].enable()
        if top_panel.tag['song'].track_index <= 1:
            self.__buttons['up'].disable()
        self.__buttons['up'].refresh()
        self.__buttons['down'].refresh()

    def scroll_into_view(self, track_index, direction):
        if not self.__album:
            return
        if [panel for panel in self.__track_panels if panel.tag['song'] and panel.tag['song'].track_index == track_index]:
            return

        track_index = max(1, track_index)
        track_index = min(track_index, self.__album.num_tracks)
        indices = [i for i in range(1, self.__album.num_tracks+1)]
        if direction < 0:
            p = -self.NUM_PANELS
            while track_index not in indices[p:p+self.NUM_PANELS]:
                p -= 1
        else:
            p = 0
            while track_index not in indices[p:p+self.NUM_PANELS]:
                p += 1
        indices = indices[p:p+self.NUM_PANELS] + [0 for i in range(self.NUM_PANELS)]

        for track_index, panel in zip(indices, self.__track_panels):
            if track_index > 0:
                panel.tag['song'] = self.__album.songs[track_index-1]
            else:
                panel.tag['song'] = None
            panel.tag['selected'] = False
            panel.refresh()
        if indices[0] == 1:
            self.__buttons['up'].disable()
        else:
            self.__buttons['up'].enable()
        if indices[4] >= self.__album.num_tracks:
            self.__buttons['down'].disable()
        else:
            self.__buttons['down'].enable()
        self.__buttons['up'].refresh()
        self.__buttons['down'].refresh()

    def unselect_all(self):
        for panel in [panel for panel in self.__track_panels if panel.tag['selected']]:
            panel.tag['selected'] = False
            panel.refresh()

    def select(self, track_index):
        found = [panel for panel in self.__track_panels if panel.tag['song'] and panel.tag['song'].track_index == track_index]
        if found:
            panel = found[0]
            panel.tag['selected'] = True
            panel.refresh()

    def update(self, modified):
        if 'song' in modified:
            track_index = modified['song'] if modified.get('state') != PlaybackState.STOP else 0 
            if track_index > 0:
                self.scroll_into_view(track_index, 1)
                self.unselect_all()
                self.select(track_index)
            else:
                self.scroll_into_view(1, 1)
                self.unselect_all()


if __name__ == '__main__':
    from player import Player
    from player import ArtistList

    terminated = False

    def quit(param):
        print('terminate')
        global terminated
        terminated = True

    def select_artist(artist):
        global artist_listview
        global album_listview
        album_listview.set_artist(artist)
        artist_listview.hide()
        album_listview.show()
        album_listview.refresh()

    def select_album(album):
        global player
        global playback_view
        player.set_album(album)
        playback_view.set_album(album)
        album_listview.hide()
        playback_view.show()
        playback_view.refresh()

    artist_list = ArtistList()
    artist_list.load('/media/usb/database.json')
    player = Player()
    desktop = Desktop()
    navigation_view = NavigationView(desktop, player)
    navigation_view.attach_event('shutdown', quit)
    artist_listview = ArtistListView(desktop, artist_list)
    artist_listview.attach_event('select', select_artist)
    album_listview = AlbumListView(desktop)
    album_listview.attach_event('select', select_album)
    album_listview.hide()
    playback_view = PlaybackView(desktop, player)
    playback_view.hide()

    desktop.show()
    artist_listview.set_page(0)

    touch = TouchManager()
    touch.add_event_listener(desktop)

    while not terminated:
        modified_states = player.get_modified() or {}
        touch.dispatch_event()
        navigation_view.update(modified_states)
        playback_view.update(modified_states)
        time.sleep(0.1)
    touch.quit()
    touch = None
    desktop = None
    UIWidget.timer.quit()
    pygame.quit()
    player.quit()
