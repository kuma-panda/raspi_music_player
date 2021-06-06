import sys
import pygame
from pygame.locals import QUIT
 
def main(fontname, fontsize, text):
    pygame.init()
    surface = pygame.display.set_mode((1024, 600))
    print(surface.get_rect().width)
    print(surface.get_rect().height)
 
    clock = pygame.time.Clock() # Clockオブジェクト作成
    if fontname == 'sseg':
        my_font = pygame.font.Font('./res/LED7SEG_Standard.ttf', fontsize)
    else:
        my_font = pygame.font.Font('./res/rounded-mgenplus-1cp-medium.ttf', fontsize)
 
    # (テキスト, アンチエイリアス, カラー)を指定
    # text = jfont.render("パイソンで日本語表示", True, (0x88, 0xC0, 0xEF)) 
    text = my_font.render(text, True, (0x88, 0xC0, 0xEF)) 
    textpos = text.get_rect()
    print('width={}, height={}'.format(textpos.width, textpos.height))
    textpos.centerx = surface.get_rect().centerx  # X座標
    textpos.centery = surface.get_rect().centery   # Y座標
     
    while True: # イベントループ
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
 
        surface.fill((88, 90, 100))
        surface.blit(text, textpos)
        pygame.display.update()
        clock.tick(10)
 
if __name__ == '__main__':
    fontname = sys.argv[1]
    fontsize = int(sys.argv[2])
    text     = sys.argv[3]
    main(fontname, fontsize, text)
