import pygame
from pygame.locals import *
import os
import sys
import time
import threading
import queue
import json
from select import select
from PIL import Image
from evdev import (InputDevice, ecodes)
from enum import Enum, Flag, auto

# ------------------------------------------------------------------------------
class TextAlign(Flag):
    LEFT    = auto()
    CENTER  = auto()
    RIGHT   = auto()
    TOP     = auto()
    MIDDLE  = auto()
    BOTTOM  = auto()

# ------------------------------------------------------------------------------
class Canvas:
    SCREEN_WIDTH  = 1024
    SCREEN_HEIGHT = 600

    FONT_PATH = '/home/pi/player/res/rounded-mgenplus-1cp-medium.ttf'
    SSEG_PATH = '/home/pi/player/res/LED7SEG_Standard.ttf'
    # ICON_PATH = './res/MaterialIcons-Regular.ttf'
    ICON_PATH = '/home/pi/player/res/Material-Design-Iconic-Font.ttf'

    BLACK      = (0x00, 0x00, 0x00)
    DARKGRAY   = (0x33, 0x33, 0x33)
    MEDIUMGRAY = (0x66, 0x66, 0x66)
    GRAY       = (0x99, 0x99, 0x99)
    LIGHTGRAY  = (0xCC, 0xCC, 0xCC)
    WHITE      = (0xFF, 0xFF, 0xFF)
    RED        = (0xFF, 0x00, 0x00)
    GREEN      = (0x00, 0xFF, 0x00)
    BLUE       = (0x00, 0x00, 0xFF)
    YELLOW     = (0xFF, 0xFF, 0x00)
    MAGENTA    = (0xFF, 0x00, 0xFF)
    CYAN       = (0x00, 0xFF, 0xFF)

    screen = None
    fonts = {}
    icon_code = {}
    dirty_rect = Rect(0, 0, 0, 0)

    # --------------------------------------------------------------------------
    @classmethod
    def initialize(cls):
        os.putenv('SDL_FBDEV', '/dev/fb1')
        pygame.init()
        pygame.mouse.set_visible(False)
        Canvas.screen = pygame.display.set_mode((Canvas.SCREEN_WIDTH, Canvas.SCREEN_HEIGHT))
        Canvas.dirty_rect = Rect(0, 0, 0, 0)
        Canvas.fonts = {
            20:     pygame.font.Font(Canvas.FONT_PATH, 20),
            'sseg': pygame.font.Font(Canvas.SSEG_PATH, 50),     # 55 -> '00' の幅=86, 高さ=60
            'icon_small': pygame.font.Font(Canvas.ICON_PATH, 30),
            'icon_large': pygame.font.Font(Canvas.ICON_PATH, 72)
        }
        with open('/home/pi/player/res/codepoints.json', mode='r') as fp:
            data = json.load(fp)
            for name, code in data.items():
                Canvas.icon_code[name] = int(code, 16)

        # with open('./res/codepoints', 'r') as fp:
        #     lines = fp.readlines()
        #     for line in lines:
        #         v = line.strip().split(' ')
        #         Canvas.icon_code[v[0]] = int(v[1], 16)        

    # --------------------------------------------------------------------------
    @classmethod
    def update(cls):
        pygame.display.update(Canvas.dirty_rect)
        Canvas.dirty_rect = Rect(0, 0, 0, 0)

    # --------------------------------------------------------------------------
    def __init__(self, rect):
        rect = Rect(rect)
        self.__surface = pygame.Surface((rect.width, rect.height))
        self.__screen_rect = rect 
        self.__current_font_size = 16

    # --------------------------------------------------------------------------
    def blit(self, pos):
        Canvas.screen.blit(self.__surface, pos)
        r = self.__screen_rect.copy()
        r.topleft = pos
        Canvas.dirty_rect.union_ip(r)

    # --------------------------------------------------------------------------
    def set_font_size(self, size):
        if size not in Canvas.fonts:
            Canvas.fonts[size] = pygame.font.Font(Canvas.FONT_PATH, size)
        self.__current_font_size = size

    # --------------------------------------------------------------------------
    def clear(self, color):
        self.__surface.fill(color)

    # --------------------------------------------------------------------------
    def draw_line(self, start, end, color, width=1):
        pygame.draw.line(self.__surface, color, start, end, width)

    def fill_rect(self, rect, color):
        pygame.draw.rect(self.__surface, color, rect)

    def draw_rect(self, rect, color, width=1):
        pygame.draw.rect(self.__surface, color, rect, width)

    def draw_circle(self, center, radius, color, width=0):
        pygame.draw.circle(self.__surface, color, center, radius, width)

    def draw_text(self, pos, text, fgcol, bkcol=None):
        font = Canvas.fonts[self.__current_font_size]
        text_surface = font.render(text, True, fgcol, bkcol)
        size = text_surface.get_size()
        self.__surface.blit(text_surface, pos)

    def draw_text_rect(self, bound_rect, text, alignment, fgcol, bkcol=None):
        font = Canvas.fonts[self.__current_font_size]
        text_surface = font.render(text, True, fgcol, bkcol)
        text_rect = text_surface.get_rect()
        bound_rect = Rect(bound_rect)
        if alignment & TextAlign.CENTER:
            if alignment & TextAlign.MIDDLE:
                text_rect.center = bound_rect.center
            elif alignment & TextAlign.BOTTOM:
                text_rect.midbottom = bound_rect.midbottom
            else:
                text_rect.midtop = bound_rect.midtop
        elif alignment & TextAlign.RIGHT:
            if alignment & TextAlign.MIDDLE:
                text_rect.midright = bound_rect.midright
            elif alignment & TextAlign.BOTTOM:
                text_rect.bottomright = bound_rect.bottomright
            else:
                text_rect.topright = bound_rect.topright
        else:
            if alignment & TextAlign.MIDDLE:
                text_rect.midleft = bound_rect.midleft
            elif alignment & TextAlign.BOTTOM:
                text_rect.bottomleft = bound_rect.bottomleft
            else:
                text_rect.topleft = bound_rect.topleft
        self.__surface.set_clip(bound_rect)
        if bkcol:
            self.fill_rect(rect=bound_rect, color=bkcol)
        self.__surface.blit(text_surface, text_rect)
        self.__surface.set_clip(None)

    def draw_text_rect_wrap(self, bound_rect, text, alignment, fgcol, bkcol=None):
        font = Canvas.fonts[self.__current_font_size]
        bound_rect = Rect(bound_rect)
        # print('width = {}'.format(bound_rect.width))
        words = text.split(' ')
        line = '' #words.pop(0)
        text_surfaces = []
        while len(words) > 0:
            w = font.size(line + ' ' + words[0])[0]
            # print('line : {} (width = {})'.format(line + ' ' + words[0], w))
            if w <= bound_rect.width:
                if line:
                    line += ' '
                line += words.pop(0)
            else:
                # print('-- newline')
                text_surfaces.append(font.render(line, True, fgcol, bkcol))
                line = ''
        if line:
            # print('line : {}'.format(line))
            # print('-- newline (end)')
            text_surfaces.append(font.render(line, True, fgcol, bkcol))

        x = bound_rect.right if (alignment & TextAlign.RIGHT) else bound_rect.left
        y = bound_rect.top

        self.__surface.set_clip(bound_rect)
        if bkcol:
            self.fill_rect(bound_rect, bkcol)

        for surface in text_surfaces:
            text_rect = surface.get_rect()
            if alignment & TextAlign.RIGHT:
                text_rect.topright = (x, y)
            else:
                text_rect.topleft = (x, y)
            self.__surface.blit(surface, text_rect)
            y += text_rect.height
    
        self.__surface.set_clip(None)

    def draw_sseg(self, pos, text, fgcol, bkcol=None):
        font = Canvas.fonts['sseg']
        surface = font.render(text, True, fgcol, bkcol)
        size = surface.get_size()
        self.__surface.blit(surface, pos)

    def draw_icon(self, ls, pos, name, fgcol, bkcol=None):
        font = Canvas.fonts['icon_{}'.format(ls)]
        surface = font.render(chr(Canvas.icon_code[name]), True, fgcol, bkcol)
        size = surface.get_size()
        self.__surface.blit(surface, pos)

    def draw_icon_center(self, ls, pos, name, fgcol, bkcol=None):
        font = Canvas.fonts['icon_{}'.format(ls)]
        surface = font.render(chr(Canvas.icon_code[name]), True, fgcol, bkcol)
        rect = surface.get_rect()
        rect.center = pos
        self.__surface.blit(surface, rect)

    def draw_image(self, buffer, rect):
        # path が指す画像は PNG を想定している。
        # PNG 画像は直接 pygame.image.load で読み込めないので、Pillow を使う
        # buffer = Image.open(path).convert('RGB')
        image = pygame.image.fromstring(buffer.tobytes(), buffer.size, buffer.mode).convert()
        image = pygame.transform.scale(image, Rect(rect).size)
        self.__surface.blit(image, rect)

# ------------------------------------------------------------------------------
class TouchManager:
    def __init__(self):
        self.__device = InputDevice('/dev/input/event1')
        self.__touched = False
        self.__listeners = []
        self.__pos = {}
        self.__queue = queue.Queue()
        self.__terminated = False
        self.__thread = threading.Thread(target=self.execute)
        self.__thread.start()

    def quit(self):
        print('[TouchManager] terminating...')
        self.__terminated = True
        self.__thread.join()
        # os.close(self.__device.fd)
        print('[TouchManager] successfully terminated')

    def add_event_listener(self, listener):
        if not [w for w in self.__listeners if w.id == listener.id]:
            # NOTE: リストの先頭に追加される点に注意
            # これにより、後から登録されたリスナが優先的にイベントを処理する機会を与えられる
            self.__listeners.insert(0, listener)    

    def remove_event_listener(self, listener):
        self.__listeners = [w for w in self.__listeners if w.id != listener.id]

    def dispatch_event(self):
        event = self.peek_event()
        if event:
            for listener in self.__listeners:
                if listener.is_enabled() and listener.is_visible():
                    if listener.handle_touch_event(event):
                        break
            return True
        return False

    def peek_event(self):
        return self.__queue.get() if not self.__queue.empty() else None

    def get_screen_coord(self):
        x, y = self.__pos['x'], self.__pos['y']
        return (x, y)
        # screen_x = Canvas.SCREEN_WIDTH - x 
        # screen_y = Canvas.SCREEN_HEIGHT - y
        # return (screen_x, screen_y)

    def execute(self):
        while not self.__terminated:
            r, w, c = select([self.__device.fd], [], [], 0.1)
            if self.__device.fd in r:
                for event in self.__device.read():
                    if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
                        if event.value:
                            self.__touched = True
                            self.__pos = {}
                        else:
                            print('released')
                            self.__touched = False
                            if ('x' in self.__pos) and ('y' in self.__pos):
                                self.__queue.put({'touched': False, 'pos': self.get_screen_coord(), 'raw': self.__pos})
                    if event.type == ecodes.EV_ABS:
                        if event.code == ecodes.ABS_X:
                            self.__pos['x'] = event.value 
                        if event.code == ecodes.ABS_Y:
                            self.__pos['y'] = event.value
                        if self.__touched and ('x' in self.__pos) and ('y' in self.__pos):
                            pos = self.get_screen_coord()
                            print('touched ({}, {})'.format(pos[0], pos[1]))
                            self.__queue.put({'touched': True, 'pos': pos, 'raw': self.__pos})
                            self.__touched = False

# ------------------------------------------------------------------------------
class TimerPool:
    def __init__(self):
        self.__users = []
        self.__terminated = False
        self.__queue = queue.Queue()
        self.__lock = threading.Lock()
        self.__thread = threading.Thread(target=self.execute)
        self.__thread.start()

    def quit(self):
        self.__terminated = True
        self.__thread.join()

    def get_expired(self):
        return self.__queue.get() if not self.__queue.empty() else None

    def execute(self):
        while not self.__terminated:
            time.sleep(0.1)
            self.__lock.acquire()
            canceled = []
            for user in self.__users:
                if time.time() >= user['timeout']['start'] + user['timeout']['value']:
                    widget = user['widget']
                    print('timer expired ({})'.format(widget.id))
                    self.__queue.put(widget)
                    canceled.append(widget.id)
            self.__users = [u for u in self.__users if u['widget'].id not in canceled]
            self.__lock.release()

    def use(self, widget, timeout, idle=False):
        self.__lock.acquire()
        self.__users.append({
            'widget': widget, 
            'timeout': {
                'value': timeout,
                'start': time.time()
            },
            'idle': idle
        })
        print('timer start ({})'.format(widget.id))
        self.__lock.release()

    def cancel(self, widget):
        self.__lock.acquire()
        self.__users = [u for u in self.__users if u['widget'].id != widget.id]
        # print('timer canceled ({})'.format(widget.id))
        self.__lock.release()

    def reset(self):
        self.__lock.acquire()
        for user in self.__users:
            if user['idle']:
                user['timeout']['start'] = time.time()
            print('timer reset ({})'.format(user['widget'].id))
        self.__lock.release()

# ------------------------------------------------------------------------------
class UIWidget:
    timer = TimerPool()

    def __init__(self, parent=None):
        self.__parent = parent
        self.__enable = True
        self.__visible = True
        self.__captured = False
        self.__children = []
        self.__canvas = None
        self.__tag = None
        if self.__parent:
            self.__parent.add_child(self)
        self.__events = {
            'touch': self.on_touched,
            'release': self.on_released
        }

    def __del__(self):
        self.__children = []

    @property
    def parent(self):
        return self.__parent

    @property
    def id(self):
        return id(self)

    @property
    def canvas(self):
        return self.__canvas

    @property
    def tag(self):
        return self.__tag
    @tag.setter
    def tag(self, v):
        self.__tag = v

    @property
    def client_rect(self):
        return self.__client_rect

    @property
    def captured(self):
        return self.__captured

    def add_child(self, child):
        self.__children.append(child)

    def create(self, rect):
        self.__canvas = Canvas(rect)
        rect = Rect(rect)
        self.__position = rect.topleft
        rect.topleft = (0, 0)
        self.__client_rect = rect.copy()
        self.__screen_offset = self.client_to_screen((0, 0))

    def on_touched(self, pos):
        pass

    def on_released(self, pos):
        pass

    def client_to_screen(self, pt):
        parent = self.__parent
        delta = self.__position
        while parent:
            delta = parent.client_to_parent(delta)
            parent = parent.parent
        return (pt[0]+delta[0], pt[1]+delta[1])

    def client_to_parent(self, pt):
        return (pt[0]+self.__position[0], pt[1]+self.__position[1])

    def screen_to_client(self, pt):
        delta = self.client_to_screen((0, 0))
        return (pt[0]-delta[0], pt[1]-delta[1])

    def handle_touch_event(self, event):
        for child in self.__children:
            if child.handle_touch_event(event):
                return True

        if event['touched']:
            if (not self.is_enabled()) or (not self.is_visible()):
                return False
            pos = self.screen_to_client(event['pos'])
            if self.__client_rect.collidepoint(pos):
                self.__captured = True
                self.trigger_event('touch', pos)
                return True
        else:
            if self.__captured:
                self.__captured = False
                self.trigger_event('release')
                return True

        return False

    def attach_event(self, etype, callback):
        self.__events[etype] = callback

    def trigger_event(self, etype, param=None):
        if etype in self.__events:
            self.__events[etype](param)

    def render(self):
        if not self.is_visible():
            return
        self.__canvas.blit(self.__screen_offset)
        for child in self.__children:
            child.render()
        Canvas.update()

    def refresh(self):
        if not self.is_visible():
            return
        self.draw()
        self.render()

    def enable(self):
        self.__enable = True
    def disable(self):
        self.__enable = False
    def is_enabled(self):
        if self.__enable:
            if not self.__parent or self.__parent.is_enabled():
                return True
        return False

    def show(self):
        self.__visible = True
        self.refresh()
    def hide(self):
        UIWidget.timer.cancel(self)
        self.__visible = False
    def is_visible(self):
        if self.__visible:
            if not self.__parent or self.__parent.is_visible():
                return True
        return False

    def get_child_by_id(self, target_id):
        f = [c for c in self.__children if c.id == target_id]
        return f[0] if f else None

    def draw(self):
        for child in self.__children:
            child.draw()
        pass

    def set_timeout(self, timeout, idle=False):
        UIWidget.timer.use(self, timeout, idle)

    def on_timeout(self):
        print('timeout')
        pass

# ------------------------------------------------------------------------------
class Desktop(UIWidget):
    BACKGROUND_COLOR = (0x0D, 0x00, 0x15)

    def __init__(self):
        Canvas.initialize()
        super().__init__()
        self.hide()
        self.create((0, 0, Canvas.SCREEN_WIDTH, Canvas.SCREEN_HEIGHT))
    
    def draw(self):
        print('[Desktop] draw')
        super().draw()
        self.canvas.clear(Desktop.BACKGROUND_COLOR)

# ------------------------------------------------------------------------------
class Label(UIWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.__color = {
            'text': Canvas.LIGHTGRAY,
            'back': Desktop.BACKGROUND_COLOR
        }
        self.__text = ''
        self.__alignment = 'topleft'

    @property
    def text_color(self):
        return self.__color['text']
    @text_color.setter
    def text_color(self, col):
        self.__color['text'] = col
        self.refresh()

    @property
    def back_color(self):
        return self.__color['back']
    @back_color.setter
    def back_color(self, col):
        self.__color['back'] = col
        self.refresh()

    @property
    def text(self):
        return self.__text
    @text.setter
    def text(self, s):
        self.__text = s
        self.refresh()

    @property
    def alignment(self):
        return self.__alignment
    @alignment.setter
    def alignment(self, align):
        self.__alignment = align
        self.refresh()

    def draw(self):
        super().draw()
        self.canvas.draw_text_rect(self.client_rect, self.__text, self.__alignment, self.__color['text'], self.__color['back'])

# ------------------------------------------------------------------------------
class PaintBox(UIWidget):
    def __init__(self, parent, proc):
        super().__init__(parent)
        self.__paint = proc
    
    def draw(self):
        super().draw()
        self.__paint(self)

# ------------------------------------------------------------------------------
class Button(UIWidget):
    ACTIVE_COLOR = (0x17, 0x18, 0x4B)

    def __init__(self, parent, text='', icon=None):
        super().__init__(parent)
        self.__icon = icon if icon else None
        self.__text = text if not self.__icon else None
        self.__colors = {
            'normal':  {'bg': Canvas.BLACK, 'fg': (0x9E, 0xA1, 0xA3)},
            'active':  {'bg': (0x9E, 0xA1, 0xA3), 'fg': Canvas.BLACK},
            'disable': {'bg': Canvas.BLACK, 'fg': Canvas.DARKGRAY}
        }
        self.__customdraw = None

    @property
    def text(self):
        return self.__text
    @text.setter
    def text(self, text):
        self.__text = text
        self.__icon = None
        self.refresh()

    @property
    def icon(self):
        return self.__icon
    @icon.setter
    def icon(self, icon):
        self.__icon = icon
        self.__text = None
        self.refresh()

    def set_customdraw(self, proc):
        self.__customdraw = proc

    def on_touched(self, pos):
        super().on_touched(pos)
        self.refresh()

    def on_released(self, pos):
        super().on_released(pos)
        self.refresh()
        print('[click] {}'.format(self.id))
        self.trigger_event('click', self)
    
    def draw(self):
        super().draw()
        if self.__customdraw:
            self.__customdraw(self)
            return

        color = self.__colors['normal']
        if self.captured:
            color = self.__colors['active']
        elif not self.is_enabled():
            color = self.__colors['disable']
        self.canvas.clear(color['bg'])
        if self.__icon:
            self.canvas.draw_icon_center('small', self.client_rect.center, self.__icon, color['fg'])
        else:
            self.canvas.draw_text_rect(self.client_rect, self.__text, 'center', color['fg'])

# ------------------------------------------------------------------------------
class Popup(UIWidget):
    BORDER_COLOR = (0x9E, 0xA1, 0xA3)
    BACKGROUND_COLOR = Canvas.BLACK

    touch = None
    desktop = None

    def __init__(self):
        super().__init__()
        self.hide()

    @classmethod
    def initialize(cls, touch, desktop):
        cls.touch = touch
        cls.desktop = desktop

    @classmethod
    def terminate(cls):
        cls.touch = None
        cls.desktop = None

    def show(self):
        Popup.touch.add_event_listener(self)
        print('Popup is about to be shown...')
        super().show()

    def hide(self):
        super().hide()
        if Popup.touch and Popup.desktop:
            Popup.touch.remove_event_listener(self)
            Popup.desktop.refresh()

    def draw(self):
        super().draw()
        self.canvas.clear(Popup.BACKGROUND_COLOR)
        r = self.client_rect.copy()
        r.width = r.width - 2
        r.height = r.height - 2
        r.topleft = (1, 1)
        self.canvas.draw_rect(r, Popup.BORDER_COLOR)

    def handle_touch_event(self, event):
        print('Popup event handler')
        if super().handle_touch_event(event):
            return True
        # 非クライアント領域を対象としたタッチイベントを検出した場合は
        # 自身を閉じる
        self.hide()
        return False


if __name__ == '__main__':
    touch = TouchManager()
    while True:
        try:
            e = touch.peek_event()
            if e:
                print(e)

        except KeyboardInterrupt:
            touch.quit()
            break
