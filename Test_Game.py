import os
import sys
import multiprocessing

import pygame
import time

pygame.init()
pygame.display.set_mode((0, 0))


class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self):
        self.dx = 0
        self.dy = 0

    # сдвинуть объект obj на смещение камеры
    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    # позиционировать камеру на объекте target
    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - width // 2)
        self.dy = -(target.rect.y + target.rect.h // 2 - height // 2)


camera = Camera()
all_sprites = pygame.sprite.Group()

# os.environ['SDL_VIDEO_CENTERED'] = '0'
tile_width = tile_height = 40
FPS = 60
clock = pygame.time.Clock()
level_seq = ('1', '2')  # последоваельность смены уровней
# размеры экрана
fullscreen_size = fullscreen_width, fullscreen_height = pygame.display.get_window_size()
size = width, height = 1300, 700

# pos_x = fullscreen_width / 2 - width / 2
# pos_y = fullscreen_height / 2 - height / 2
# os.environ['SDL_VIDEO_WINDOW_POS'] = '%d,%d' % (pos_x, pos_y)
for i in list(os.environ):
    print(i)
screen = pygame.display.set_mode(size, pygame.NOFRAME)


def load_level(filename):  # загрузка уровня из текстового файла
    filename = "data/levels/" + filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]

    # и подсчитываем максимальную длину
    max_width = max(map(len, level_map))

    # дополняем каждую строку пустыми клетками ('.')
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


def load_image(name, color_key=None):  # загрузка изображения из папки data
    fullname = os.path.join('data', name)
    image = pygame.image.load(fullname)
    if color_key is not None:
        image = image.convert()
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


def generate_level(level, hero):  # прогрузка уровня
    all_sprites.remove(*items.sprites(), *top_layer.sprites(), *bottom_layer.sprites())
    items.empty()
    borders.empty()
    top_layer.empty()
    bottom_layer.empty()
    for y in range(len(level)):
        for x in range(len(level[y])):
            Floor(x, y)
            if level[y][x] == '#':
                Border(x, y)
                BottomWall(x, y)
                TopWall(x, y)
            elif level[y][x] == '@':
                hero.set_pos(x * tile_width, y * tile_height)
            elif level[y][x] == '*':
                Portal(x * tile_width, y * tile_height, 2)
    return len(level[0]), len(level)


def highlight(rect, title, *stats):
    font = pygame.font.Font(None, 25)
    text = font.render('E) ' + title, 1, (255, 255, 255))
    screen.blit(text,
                (rect.x + rect.w // 2 - text.get_rect().w // 2, rect.y - 25 - text.get_rect().h))
    pygame.draw.polygon(screen, (255, 255, 255), ((rect.x + rect.w // 2, rect.y),
                                                  (rect.x + rect.w // 2 - 15, rect.y - 15),
                                                  (rect.x + rect.w // 2 + 15, rect.y - 15)))


class AnimatedSprite(pygame.sprite.Sprite):  # база для анимированных спрайтов, режет листы анимаций
    def __init__(self, columns, rows, x, y, *sheets):
        super().__init__(all_sprites)
        self.frame_lim = columns
        self.frames = []
        for sheet in sheets:
            self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(frame_location, self.rect.size)))


class Portal(AnimatedSprite):
    def __init__(self, x, y, portal_type=0):
        self.portal_type = portal_type
        super().__init__(3, 4, x, y, load_image('portal.png'))
        self.anim_timer = 0
        self.add(items)

    def picked(self, hero):
        global cur_level
        cur_level = (cur_level + 1) % len(level_seq)
        generate_level(load_level(f'level_{level_seq[cur_level]}.txt'), hero)

    def highlight(self):
        highlight(self.rect, 'Портал')

    def update(self):
        self.anim_timer += 1 / FPS
        if self.anim_timer >= 0.1:
            self.cur_frame = (self.cur_frame + 1) % self.frame_lim + self.frame_lim * self.portal_type
            self.anim_timer = 0
        self.image = self.frames[self.cur_frame]


class Potion(AnimatedSprite):  # любое зелье
    # каждое зелье бафает определённые статы
    types = {'red': ('здоровья', 2, 0, 0, 0, -1), 'blue': ('маны', 0, 80, 0, 0, -1),
             'green': ('скорости', 0, 0, 0, 5, 5), 'yellow': ('урона', 0, 0, 5, 0, 5)}

    def __init__(self, potion_type, x, y, size='small'):
        self.size = size
        self.name = Potion.types[potion_type][0]
        self.stats = Potion.types[potion_type][1:]

        potion_name = '_'.join(['flask', size, potion_type, '1'])
        super().__init__(1, 1, x, y, load_image(potion_name + '.png'))
        self.add(items)

    def picked(self, obj):
        obj.heal(self.stats[0] * (1 + (self.size == 'big')))
        obj.restore_mana(self.stats[1] * (1 + (self.size == 'big')))
        obj.add_buff([stat * 2 if self.size == 'big' else stat for stat in self.stats[-3:]])
        self.kill()

    def highlight(self):
        title = 'большое ' * (self.size == 'big') + 'зелье ' + self.name
        highlight(self.rect, title.capitalize())

    # def update(self):  # подсвечивается при подходе
    #     if not pygame.sprite.collide_mask(self, hero):
    #         self.image = self.frames[0]


# class Button(pygame.sprite.Sprite):
#     def __init__(self, x, y, picture):
#         self.image = load_image('exit_button.png', -1)
#         # self.image = Botton.exit_botton
#         self.rect_image = self.image.get_rect().move(x, y)
#         self.rect = pygame.Rect(x, y, 177, 56)
#         screen.blit(self.image, (x, y))
#
#     def dar(self):
#         if self.rect_image.collidepoint(pygame.mouse.get_pos()):
#             print(3)


class Hero(AnimatedSprite):
    # классы определяются статами
    types = {'knight': (6, 150, 5, 5), 'wizzard': (4, 250, 3, 6), 'lizard': (4, 150, 7, 7)}
    stat_bar = load_image("hero_bar.png", -1)

    def __init__(self, hero_type, sex, pos_x, pos_y):
        self.health, self.mana, self.dmg, self.speed = Hero.types[hero_type]
        self.max_health, self.max_mana = self.health, self.mana
        self.v = 0
        # анимации ожидания и движения
        anim_sheets = (load_image('_'.join([hero_type, sex, 'idle', 'anim.png'])),
                       load_image('_'.join([hero_type, sex, 'run', 'anim.png'])))
        # загрузка картинки через название и пол персонажа
        super().__init__(4, 1, pos_x * tile_width, pos_y * tile_height, *anim_sheets)
        mask_surface = pygame.Surface((40, 70), pygame.SRCALPHA, 32)
        self.frames = [pygame.transform.scale(frame, (32, 56)) for frame in self.frames]
        for frame in self.frames:
            mask_surface.blit(frame, (0, 0))
            mask_surface.blit(pygame.transform.flip(frame, True, False), (0, 0))
        self.mask = pygame.mask.from_surface(mask_surface)
        self.buffs = []
        self.direction = False
        self.is_running = False
        self.anim_timer = 0

    def get_pos(self):  # потом пригодится
        return self.rect.x + self.rect.w // 2, self.rect.y + self.rect.h // 2

    def get_health(self):
        return self.health

    def get_mana(self):
        return self.mana

    def get_dmg(self):
        return self.dmg + sum([buff[0] for buff in self.buffs])

    def get_speed(self):
        return self.speed + sum([buff[1] for buff in self.buffs])

    def heal(self, hp):
        self.health = min(self.health + hp, self.max_health)

    def restore_mana(self, mana):
        self.mana = min(self.mana + mana, self.max_mana)

    def add_buff(self, buff):
        self.buffs.append(list(buff))

    def set_pos(self, x, y):
        self.rect.x, self.rect.y = x, y

    def move(self):  # отслеживание перемещения
        keys = pygame.key.get_pressed()
        x, y = 0, 0
        if pygame.mouse.get_pos()[0] < width // 2:
            self.direction = True
        else:
            self.direction = False
        if keys[pygame.K_a]:
            x = -1
        elif keys[pygame.K_d]:
            x = 1
        if keys[pygame.K_w]:
            y = -1
        elif keys[pygame.K_s]:
            y = 1
        if x or y:
            self.is_running = True
            x = x * (self.get_speed() ** 2 / (bool(x) + bool(y))) ** 0.5
            y = y * (self.get_speed() ** 2 / (bool(x) + bool(y))) ** 0.5
            self.rect = self.rect.move(x, 0)
            if any([pygame.sprite.collide_mask(self, border) for border in borders]):
                self.rect = self.rect.move(-x, 0)
            self.rect = self.rect.move(0, y)
            if any([pygame.sprite.collide_mask(self, border) for border in borders]):
                self.rect = self.rect.move(0, -y)
        else:
            self.is_running = False
            # while any([pygame.sprite.collide_mask(self, border) for border in borders]):
            #     self.rect = self.rect.move(0, 1)

    def update(self, *args):  # здесь отрисовка
        self.move()
        self.image = pygame.transform.flip(self.frames[self.cur_frame], self.direction, 0)
        # self.mask = pygame.mask.from_surface(self.image)
        self.anim_timer += (1 / FPS)
        for buff in self.buffs:
            buff[-1] -= 1 / FPS
        self.buffs = list(filter(lambda b: b[-1] > 0, self.buffs))
        if self.anim_timer > 1 / self.get_speed():
            self.cur_frame = (self.cur_frame + 1) % self.frame_lim + self.frame_lim * self.is_running
            self.anim_timer = 0

        # рисуем кол-во жизней и маны героя
        font = pygame.font.Font(None, 30)
        health = font.render(str(self.get_health()) + '/' + str(self.max_health), 1, (255, 255, 255))
        mana = font.render(str(self.get_mana()) + '/' + str(self.max_mana), 1, (255, 255, 255))
        screen.blit(Hero.stat_bar, (0, 0))
        pygame.draw.rect(screen, (255, 64, 69),
                         (54, 18, int(175 / (self.max_health / self.get_health())), 18), 0)
        pygame.draw.rect(screen, (72, 114, 164),
                         (54, 49, int(175 / (self.max_mana / self.get_mana())), 18), 0)
        screen.blit(health, (120, 18))
        screen.blit(mana, (100, 49))


borders = pygame.sprite.Group()
decorations = pygame.sprite.Group()
cursor = pygame.transform.scale(load_image('cursor.jpg', -1), (60, 60))


class Border(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites, borders, bottom_layer)
        self.image = load_image("Wall.jpg")
        # вычисляем маску для эффективного сравнения
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


class TopWall(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites, decorations, top_layer)
        self.image = load_image("wall_top.jpg")
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y - 20)


class BottomWall(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites, decorations, bottom_layer)
        self.image = load_image("wall_bottom.png")
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y + 20)


class Floor(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites, decorations, bottom_layer)
        self.image = load_image("floor.jpg")
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


def terminate():
    pygame.quit()
    sys.exit()


main_menu = True
running = False
pick_up = False


class ShowHero(AnimatedSprite):
    def __init__(self, x, y, hero_type, sex):
        anim_sheets = load_image('_'.join([hero_type, sex, 'idle', 'anim.png']))
        super().__init__(4, 1, 0, 0, anim_sheets)
        self.anim_timer = 0

    def update(self):
        self.anim_timer += 1 / FPS

        if self.anim_timer >= 0.1:
            self.cur_frame = (self.cur_frame + 1) % self.frame_lim
            self.anim_timer = 0
        self.image = self.frames[self.cur_frame]


def hero_choose():
    heroes = ['knight', 'wizzard', 'lizard']
    types = {'knight': (6, 150, 5, 5), 'wizzard': (4, 250, 3, 6), 'lizard': (4, 150, 7, 7)}
    cur_hero = 0
    sex = 'm'
    hero_image = ShowHero(1, 1, heroes[cur_hero], sex)
    while True:
        image = load_image('next_button.png', -1)
        next_btn = image.get_rect().move(width // 2 + 300, height // 2)
        screen.blit(image, (width // 2 + 300, height // 2))

        image = load_image('back_button.png', -1)
        back_btn = image.get_rect().move(0, 0)
        screen.blit(image, (0, 0))

        image = load_image('woman_button.png', -1)
        woman_btn = image.get_rect().move(width // 2 - 180, height // 2 + 100)
        screen.blit(image, (width // 2 - 180, height // 2 + 100))

        image = load_image('man_button.png', -1)
        man_btn = image.get_rect().move(width // 2 + 50, height // 2 + 100)
        screen.blit(image, (width // 2 + 50, height // 2 + 100))

        image = load_image('choose_button.png', -1)
        choose_btn = image.get_rect().move(width // 2 - 75, height // 2 + 200)
        screen.blit(image, (width // 2 - 75, height // 2 + 200))

        image = load_image('prev_button.png', -1)
        prev_btn = image.get_rect().move(width // 2 - 300, height // 2)
        screen.blit(image, (width // 2 - 300, height // 2))

        characteristic = ['Количество жизней: {}'.format(types[heroes[cur_hero]][0]),
                          'Количество маны: {}'.format(types[heroes[cur_hero]][1]),
                          'Урон: {}'.format(types[heroes[cur_hero]][2]),
                          'Скорость бега: {}'.format(types[heroes[cur_hero]][3])]
        text_w = 0
        text_h = 0
        text_x = 0
        text_y = 0
        for i in range(len(characteristic)):
            font = pygame.font.Font(None, 50)
            text = font.render(characteristic[i], 1, (100, 255, 100))
            text_x = width // 2 - 150
            text_y = height // 2 - text.get_height() // 2 - 300 + text.get_height() * i
            text_w = max(text.get_width(), text_w)
            text_h += text.get_height()
            screen.blit(text, (text_x, text_y))
        pygame.draw.rect(screen, (0, 255, 0), (width // 2 - 160, text_y - text.get_height() * i - 10,
                                               text_w + 20, text_h + 20), 1)

        screen.blit(pygame.transform.scale(hero_image.image, (160, 280)), (width // 2 - 60, height // 2 - 200))

        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 30, pygame.mouse.get_pos()[1] - 30))
        hero_image.update()
        pygame.display.flip()
        screen.fill((0, 0, 0))
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos  # gets mouse position
                if next_btn.collidepoint(mouse_pos):
                    cur_hero = (cur_hero + 1) % 3
                    hero_image = ShowHero(1, 1, heroes[cur_hero], sex)
                elif prev_btn.collidepoint(mouse_pos):
                    cur_hero = (cur_hero - 1) % 3
                    print(cur_hero)
                    hero_image = ShowHero(1, 1, heroes[cur_hero], sex)
                elif back_btn.collidepoint(mouse_pos):
                    return 0
                elif choose_btn.collidepoint(mouse_pos):
                    return heroes[cur_hero], sex
                elif man_btn.collidepoint(mouse_pos):
                    sex = 'm'
                    hero_image = ShowHero(1, 1, heroes[cur_hero], sex)
                elif woman_btn.collidepoint(mouse_pos):
                    sex = 'f'
                    hero_image = ShowHero(1, 1, heroes[cur_hero], sex)


def pause():  # функция главного меню и паузы
    while True:
        bottom_layer.draw(screen)
        items.draw(screen)
        player.draw(screen)
        top_layer.draw(screen)
        image = load_image('pause_menu.png', -1)
        screen.blit(image, (100, 100))
        image = load_image('exit_button.png', -1)
        exit_btn = image.get_rect().move(400, 190)
        screen.blit(image, (400, 190))

        image = load_image('play_button.png', -1)
        resume_btn = image.get_rect().move(150, 190)
        screen.blit(image, (150, 190))
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 30, pygame.mouse.get_pos()[1] - 30))
        pygame.display.flip()
        screen.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos  # gets mouse position
                if resume_btn.collidepoint(mouse_pos):
                    return 'Play'
                elif exit_btn.collidepoint(mouse_pos):
                    return 'Exit'


def menu():  # функция главного меню и паузы
    while True:
        screen.blit(fon, (0, 0))
        image = load_image('exit_button.png', -1)
        exit_btn = image.get_rect().move(width - 300, 100)
        screen.blit(image, (width - 300, 100))

        image = load_image('play_button.png', -1)
        resume_btn = image.get_rect().move(width - 300, 200)
        screen.blit(image, (width - 300, 200))

        image = load_image('full_disp.png', -1)
        full_disp_btn = image.get_rect().move(width - 300, 300)
        screen.blit(image, (width - 300, 300))

        image = load_image('choose_button.png', -1)
        choose_btn = image.get_rect().move(width - 300, 400)
        screen.blit(image, (width - 300, 400))

        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 30, pygame.mouse.get_pos()[1] - 30))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos  # gets mouse position
                if resume_btn.collidepoint(mouse_pos):
                    return 'Play'
                elif exit_btn.collidepoint(mouse_pos):
                    return 'Exit'
                elif full_disp_btn.collidepoint(mouse_pos):
                    if size == (fullscreen_width, fullscreen_height):
                        return 'Not_full'
                    else:
                        return 'Full'
                elif choose_btn.collidepoint(mouse_pos):
                    return 'Choose'


hero = Hero('lizard', 'f', 0, 0)
pygame.mouse.set_visible(False)  # делаем курсор невидимым
hero_creature, hero_sex = 'lizard', 'f'
while main_menu:

    fon = pygame.transform.scale(load_image('menu_background.jpg'), size)
    screen.blit(fon, (0, 0))

    action = menu()
    if action == 'Play':  # проверяем нажата ли кнопка начала игры, если да, то запускаем
        running = True
    elif action == 'Exit':
        terminate()
    elif action == 'Full':
        fullscreen_size, size = size, fullscreen_size
        fullscreen_width, fullscreen_height, width, height = width, height, fullscreen_width, fullscreen_height
        screen = pygame.display.set_mode((width, height), pygame.NOFRAME | pygame.FULLSCREEN)

    elif action == 'Not_full':
        fullscreen_size, size = size, fullscreen_size
        fullscreen_width, fullscreen_height, width, height = width, height, fullscreen_width, fullscreen_height
        screen = pygame.display.set_mode(size, pygame.NOFRAME)
    elif action == 'Choose':
        action = hero_choose()
        print(action)
        if action:
            hero_creature, hero_sex = action

    cur_level = 0  # текущий уровень в последовательности
    all_sprites = pygame.sprite.Group()  # группа для обновления
    items = pygame.sprite.Group()  # все предметы
    top_layer = pygame.sprite.Group()  # группа для отрисовки всего что над персонажем
    bottom_layer = pygame.sprite.Group()  # группа для отрисoвки всего что под персонажем

    level = load_level(f'level_{level_seq[cur_level]}.txt')
    for i in level:
        print(*i)

    hero = Hero(hero_creature, hero_sex, 0, 0)
    generate_level(level, hero)
    player = pygame.sprite.Group(hero)

    Potion('red', 150, 150)
    Potion('blue', 175, 150)
    Potion('green', 200, 150)
    Potion('yellow', 225, 150)
    Potion('red', 150, 175, size='big')
    Potion('blue', 175, 175, size='big')
    Potion('green', 200, 175, size='big')
    Potion('yellow', 225, 175, size='big')

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()

    pygame.display.flip()

    while running:
        pick_up = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    pick_up = True
                elif event.key == pygame.K_ESCAPE:  # игра оставнавливается, если нажать Esc
                    if pause() == 'Exit':
                        running = False

        camera.update(hero)
        # обновляем положение всех спрайтов
        for sprite in all_sprites:
            camera.apply(sprite)
        screen.fill((0, 0, 0))
        bottom_layer.draw(screen)
        items.draw(screen)
        player.draw(screen)
        top_layer.draw(screen)

        pick = pygame.sprite.spritecollide(hero, items, 0, pygame.sprite.collide_mask)
        if pick:
            pick[0].highlight()
            if pick_up:
                pick[0].picked(hero)

        # рисуем свой курсор
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 30, pygame.mouse.get_pos()[1] - 30))
        pygame.display.flip()
        clock.tick(FPS)
        all_sprites.update()
