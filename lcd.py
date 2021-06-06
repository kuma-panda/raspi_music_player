import pygame
from pygame.locals import *
import os
import sys
import time
import threading
import queue
from select import select
from PIL import Image
from evdev import (InputDevice, ecodes)

# ------------------------------------------------------------------------------
class LCD:
    WIDTH  = 320
    HEIGHT = 240
    FONT_PATH = './res/rounded-mgenplus-1cp-medium.ttf'
    SSEG_PATH = './res/DSEG7Classic-Italic.ttf'
    ICON_PATH = './res/MaterialIcons-Regular.ttf'

    def __init__(self):
        os.putenv('SDL_FBDEV', '/dev/fb1')
        pygame.init()
        pygame.mouse.set_visible(False)
        self.__screen = pygame.display.set_mode((LCD.WIDTH, LCD.HEIGHT))
        self.__dirty_rect = Rect(0, 0, 0, 0)
        self.__fonts = {
            16:     pygame.font.Font(LCD.FONT_PATH, 16),
            'sseg': pygame.font.Font(LCD.SSEG_PATH, 28),
            'icon_small': pygame.font.Font(LCD.ICON_PATH, 24),
            'icon_large': pygame.font.Font(LCD.ICON_PATH, 36)
        }
        self.__curren_font_size = 16

        self.__icon_code = {}
        with open('./res/codepoints', 'r') as fp:
            lines = fp.readlines()
            for line in lines:
                v = line.strip().split(' ')
                self.__icon_code[v[0]] = int(v[1], 16)        

        self.clear((0x21, 0x04, 0x39))
        self.update()

    def set_font_size(self, size):
        if size not in self.__fonts:
            self.__fonts[size] = pygame.font.Font(FONT_PATH, size)
        self.__curren_font_size = size

    def update(self):
        pygame.display.update(self.__dirty_rect)
        self.__dirty_rect = Rect(0, 0, 0, 0)

    def clear(self, color):
        self.__screen.fill(color)
        self.__dirty_rect = Rect(0, 0, LCD.WIDTH, LCD.HEIGHT)

    def draw_line(self, start, end, color, width=1):
        pygame.draw.line(self.__screen, color, start, end, width)
        r = Rect(start, (end[0]-start[0], end[1]-start[1]))
        self.__dirty_rect.union_ip(r)

    def fill_rect(self, rect, color):
        pygame.draw.rect(self.__screen, color, rect)
        self.__dirty_rect.union_ip(rect)

    def draw_rect(self, rect, color, width=1):
        pygame.draw.rect(self.__screen, color, rect, width)
        self.__dirty_rect.union_ip(rect)

    def draw_text(self, pos, text, fgcol, bkcol=None):
        font = self.__fonts[self.__curren_font_size]
        surface = font.render(text, True, fgcol, bkcol)
        size = surface.get_size()
        self.__screen.blit(surface, pos)
        self.__dirty_rect.union_ip(Rect(pos, size))
        return size

    def draw_text_rect(self, bound_rect, text, alignment, fgcol, bkcol=None):
        font = self.__fonts[self.__curren_font_size]
        surface = font.render(text, True, fgcol, bkcol)
        text_rect = surface.get_rect()
        bound_rect = Rect(bound_rect)
        if alignment == 'bottomleft': # 左下揃え
            text_rect.bottomleft = bound_rect.bottomleft
        elif alignment == 'midleft':    # 左中央揃え
            text_rect.midleft = bound_rect.midleft
        elif alignment == 'midtop':     # 上中央揃え
            text_rect.midtop = bound_rect.midtop
        elif alignment == 'center':     # 中央揃え
            text_rect.center = bound_rect.center
        elif alignment == 'midbottom':
            text_rect.midbottom = bound_rect.midbottom
        elif alignment == 'topright':
            text_rect.topright = bound_rect.topright
        elif alignment == 'midright':
            text_rect.midright = bound_rect.midright
        elif alignment == 'bottomright':
            text_rect.bottomright = bound_rect.bottomright
        else:  # 左上揃え（デフォルト）
            text_rect.topleft = bound_rect.topleft
        self.__screen.set_clip(bound_rect)
        if bkcol:
            self.fill_rect(bound_rect, bkcol)
        self.__screen.blit(surface, text_rect)
        self.__screen.set_clip(None)
        self.__dirty_rect.union_ip(bound_rect)

    def draw_text_rect_wrap(self, bound_rect, text, alignment, fgcol, bkcol=None):
        font = self.__fonts[self.__curren_font_size]
        bound_rect = Rect(bound_rect)
        words = text.split(' ')
        line = words.pop(0)
        surfaces = []
        while len(words) > 0:
            if font.size(line)[0] >= bound_rect.width:
                surfaces.append(font.render(line, True, fgcol, bkcol))
                line = ''
            if line:
                line += ' '
            line += words.pop(0)
        if line:
            surfaces.append(font.render(line, True, fgcol, bkcol))

        x = bound_rect.right if alignment == 'right' else bound_rect.left
        y = bound_rect.top

        self.__screen.set_clip(bound_rect)
        if bkcol:
            self.fill_rect(bound_rect, bkcol)

        for surface in surfaces:
            text_rect = surface.get_rect()
            if alignment == 'right':
                text_rect.topright = (x, y)
            else:
                text_rect.topleft = (x, y)
            self.__screen.blit(surface, text_rect)
            y += text_rect.height
    
        self.__screen.set_clip(None)
        self.__dirty_rect.union_ip(bound_rect)

    def draw_sseg(self, pos, text, fgcol, bkcol=None):
        font = self.__fonts['sseg']
        surface = font.render(text, True, fgcol, bkcol)
        size = surface.get_size()
        self.__screen.blit(surface, pos)
        self.__dirty_rect.union_ip(Rect(pos, size))
        return size

    def draw_icon(self, ls, pos, name, fgcol, bkcol=None):
        font = self.__fonts['icon_{}'.format(ls)]
        surface = font.render(chr(self.__icon_code[name]), True, fgcol, bkcol)
        size = surface.get_size()
        self.__screen.blit(surface, pos)
        self.__dirty_rect.union_ip(Rect(pos, size))
        return size

    def draw_icon_center(self, ls, pos, name, fgcol, bkcol=None):
        font = self.__fonts['icon_{}'.format(ls)]
        surface = font.render(chr(self.__icon_code[name]), True, fgcol, bkcol)
        rect = surface.get_rect()
        rect.center = pos
        self.__screen.blit(surface, rect)
        self.__dirty_rect.union_ip(rect)
        return rect

    def draw_image(self, path, rect):
        # path が指す画像は PNG を想定している。
        # PNG 画像は直接 pygame.image.load で読み込めないので、Pillow を使う
        buffer = Image.open(path).convert('RGB')
        image = pygame.image.fromstring(buffer.tobytes(), buffer.size, buffer.mode).convert()
        image = pygame.transform.scale(image, Rect(rect).size)
        self.__screen.blit(image, rect)
        return rect

# ------------------------------------------------------------------------------
class TouchManager:
    def __init__(self):
        self.__device = InputDevice('/dev/input/event0')
        self.__touched = False
        self.__pos = {}
        self.__queue = queue.Queue()
        self.__terminated = False
        self.__thread = threading.Thread(target=self.execute)
        self.__thread.start()

    def quit(self):
        self.__terminated = True
        self.__thread.join()

    def peek_event(self):
        return self.__queue.get() if not self.__queue.empty() else None

    def get_screen_coord(self):
        x, y = self.__pos['x'], self.__pos['y']
        screen_x = min(max(0, int(320 * (y - 3600) / (300 - 3600))), 319)
        screen_y = min(max(0, int(240 * (x - 400) / (3700 - 400))), 239)
        return (screen_x, screen_y)

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
                            self.__queue.put({'touched': False, 'pos': self.get_screen_coord()})
                    if event.type == ecodes.EV_ABS:
                        if event.code == ecodes.ABS_X:
                            self.__pos['x'] = event.value 
                        if event.code == ecodes.ABS_Y:
                            self.__pos['y'] = event.value
                        if self.__touched and ('x' in self.__pos) and ('y' in self.__pos):
                            print('touched')
                            self.__queue.put({'touched': True, 'pos': self.get_screen_coord()})
                            self.__touched = False

