import os
import sys

import pygame

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

tile_width = tile_height = 40
FPS = 60
clock = pygame.time.Clock()
level_seq = ('1', '2')  # последоваельность смены уровней

# размеры экрана
FULL_SIZE = FULL_WIDTH, FULL_HEIGHT = pygame.display.get_window_size()
BASE_SIZE = BASE_WISTH, BASE_HEIGHT = 1080, 720
size = width, height = BASE_SIZE
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

    def update(self):
        self.anim_timer += 1 / FPS
        if self.anim_timer >= 0.1:
            self.cur_frame = (self.cur_frame + 1) % self.frame_lim + self.frame_lim * self.portal_type
            self.anim_timer = 0
        self.image = self.frames[self.cur_frame]


class Potion(AnimatedSprite):  # любое зелье
    # каждое зелье бафает определённые статы
    types = {'red': (2, 0, 0, 0, -1), 'blue': (0, 80, 0, 0, -1), 'green': (0, 0, 0, 5, 5),
             'yellow': (0, 0, 5, 0, 5)}

    def __init__(self, potion_type, x, y, size='small'):
        self.stats = (
            potion_type, *[i * 2 if size == 'big' else i for i in Potion.types[potion_type]])
        potion_name = '_'.join(['flask', size, potion_type, '1'])
        super().__init__(1, 1, x, y, load_image(potion_name + '.png'))
        self.add(items)

    def picked(self, obj):
        obj.heal(self.stats[1])
        obj.restore_mana(self.stats[2])
        obj.add_buff(self.stats[-3:])
        self.kill()

    def update(self):  # подсвечивается при подходе
        if not pygame.sprite.collide_mask(self, hero):
            self.image = self.frames[0]
        else:
            pass


class Hero(AnimatedSprite):
    # классы определяются статами
    types = {'knight': (6, 150, 5, 5), 'wizzard': (4, 250, 3, 6), 'lizard': (4, 150, 7, 7)}

    def __init__(self, hero_type, sex, pos_x, pos_y):
        self.health, self.mana, self.dmg, self.speed = Hero.types[hero_type]
        self.max_health, self.max_mana = self.health, self.mana
        # анимации ожидания и движения
        anim_sheets = (load_image('_'.join([hero_type, sex, 'idle', 'anim.png'])),
                       load_image('_'.join([hero_type, sex, 'run', 'anim.png'])))
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
        if keys[pygame.K_LEFT]:
            x = -1
            self.direction = True
        elif keys[pygame.K_RIGHT]:
            x = 1
            self.direction = False
        if keys[pygame.K_UP]:
            y = -1
        elif keys[pygame.K_DOWN]:
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


class ShowHero(AnimatedSprite):
    def __init__(self, x, y, hero_type, sex):
        anim_sheets = load_image('_'.join([hero_type, sex, 'idle', 'anim.png']))
        super().__init__(4, 1, x, y, anim_sheets)
        self.remove(all_sprites)
        self.anim_timer = 0

    def update(self):
        self.anim_timer += 1 / FPS

        if self.anim_timer >= 0.1:
            self.cur_frame = (self.cur_frame + 1) % self.frame_lim
            self.anim_timer = 0
        self.image = self.frames[self.cur_frame]


CHOOSE_IMAGE = load_image('choose_button.png', -1)
BACK_IMAGE = load_image('back_button.png', -1)
NEXT_IMAGE = load_image('next_button.png', -1)
WOMAN_IMAGE = load_image('woman_button.png', -1)
MAN_IMAGE = load_image('man_button.png', -1)
PREV_IMAGE = load_image('prev_button.png', -1)


def hero_choose():
    heroes = list(Hero.types.keys())
    types = Hero.types
    cur_hero = 0
    sex = 'm'
    hero_image = ShowHero(0, 0, heroes[cur_hero], sex)
    while True:
        screen.fill((0, 0, 0))

        image = NEXT_IMAGE
        next_btn = image.get_rect().move(width // 2 + 300, height // 2)
        screen.blit(image, (width // 2 + 300, height // 2))

        image = BACK_IMAGE
        back_btn = image.get_rect().move(0, 0)
        screen.blit(image, (0, 0))

        image = WOMAN_IMAGE
        woman_btn = image.get_rect().move(width // 2 - 180, height // 2 + 100)
        screen.blit(image, (width // 2 - 180, height // 2 + 100))

        image = MAN_IMAGE
        man_btn = image.get_rect().move(width // 2 + 50, height // 2 + 100)
        screen.blit(image, (width // 2 + 50, height // 2 + 100))

        image = CHOOSE_IMAGE
        choose_btn = image.get_rect().move(width // 2 - 75, height // 2 + 200)
        screen.blit(image, (width // 2 - 75, height // 2 + 200))

        image = PREV_IMAGE
        prev_btn = image.get_rect().move(width // 2 - 300, height // 2)
        screen.blit(image, (width // 2 - 300, height // 2))

        characteristic = ['Количество жизней: {}'.format(types[heroes[cur_hero]][0]),
                          'Количество маны: {}'.format(types[heroes[cur_hero]][1]),
                          'Урон: {}'.format(types[heroes[cur_hero]][2]),
                          'Скорость бега: {}'.format(types[heroes[cur_hero]][3])]
        text_w = 0
        text_h = 0
        for i, stat in enumerate(characteristic):
            font = pygame.font.Font(None, 50)
            text = font.render(stat, 1, (100, 255, 100))
            text_x = width // 2 - 150
            text_y = height // 2 - text.get_height() // 2 - 300 + text_h
            text_w = max(text.get_width(), text_w)
            text_h += text.get_height()
            screen.blit(text, (text_x, text_y))
        pygame.draw.rect(screen, (0, 255, 0), (width // 2 - 160, text_y - text.get_height() * i - 10,
                                               text_w + 20, text_h + 20), 1)

        screen.blit(pygame.transform.scale(hero_image.image, (160, 280)), (width // 2 - 60,
                                                                           height // 2 - 200))

        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 30, pygame.mouse.get_pos()[1] - 30))
        pygame.display.flip()
        hero_image.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos  # gets mouse position
                if next_btn.collidepoint(mouse_pos):
                    cur_hero = (cur_hero + 1) % len(heroes)
                    hero_image = ShowHero(0, 0, heroes[cur_hero], sex)
                elif prev_btn.collidepoint(mouse_pos):
                    cur_hero = (cur_hero - 1) % len(heroes)
                    hero_image = ShowHero(0, 0,  heroes[cur_hero], sex)
                elif back_btn.collidepoint(mouse_pos):
                    return 0
                elif choose_btn.collidepoint(mouse_pos):
                    return heroes[cur_hero], sex
                elif man_btn.collidepoint(mouse_pos):
                    sex = 'm'
                    hero_image = ShowHero(0, 0, heroes[cur_hero], sex)
                elif woman_btn.collidepoint(mouse_pos):
                    sex = 'f'
                    hero_image = ShowHero(0, 0, heroes[cur_hero], sex)

        clock.tick(FPS)


PLAY_IMAGE = load_image('play_button.png', -1)
EXIT_IMAGE = load_image('exit_button.png', -1)
PAUSE_IMAGE = load_image('pause_menu.png', -1)


def pause():  # функция главного меню и паузы
    while True:
        screen.fill((0, 0, 0))
        bottom_layer.draw(screen)
        items.draw(screen)
        player.draw(screen)
        top_layer.draw(screen)
        image = PAUSE_IMAGE
        screen.blit(image, (100, 100))
        image = EXIT_IMAGE
        exit_btn = image.get_rect().move(400, 190)
        screen.blit(image, (400, 190))
        image = PLAY_IMAGE
        resume_btn = image.get_rect().move(150, 190)
        screen.blit(image, (150, 190))
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
        clock.tick(FPS)


FULL_IMAGE = load_image('full_disp.png', -1)


def menu():  # функция главного меню и паузы
    while True:
        screen.blit(background, (0, 0))

        image = EXIT_IMAGE
        exit_btn = image.get_rect().move(width - 300, 100)
        screen.blit(image, (width - 300, 100))

        image = PLAY_IMAGE
        resume_btn = image.get_rect().move(width - 300, 200)
        screen.blit(image, (width - 300, 200))

        image = FULL_IMAGE
        full_disp_btn = image.get_rect().move(width - 300, 300)
        screen.blit(image, (width - 300, 300))

        image = CHOOSE_IMAGE
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
                    return 'Resize'
                elif choose_btn.collidepoint(mouse_pos):
                    return 'Choose'

        clock.tick(FPS)


background = pygame.transform.scale(load_image('back.jpg'), size)
pygame.mouse.set_visible(False)  # делаем курсор невидимым
hero_creature, hero_sex = 'lizard', 'f'

main_menu = True
running = False
pick_up = False


while main_menu:
    all_sprites = pygame.sprite.Group()  # группа для обновления
    action = menu()  # нажатие кнопки

    if action == 'Play':  # кнопка "Запустить" включает игровой цикл
        running = True

    elif action == 'Exit':  # кнопка "Выйти" закрыает игру
        terminate()

    elif action == 'Resize':  # переключение в полноэкранный режим
        screen.fill((0, 0, 0))
        pygame.display.flip()
        if size == BASE_SIZE:
            size = width, height = FULL_SIZE
            screen = pygame.display.set_mode(size, pygame.NOFRAME | pygame.FULLSCREEN)
        else:
            size = width, height = BASE_SIZE
            screen = pygame.display.set_mode(size, pygame.NOFRAME)
        background = pygame.transform.scale(load_image('back.jpg'), size)

    elif action == 'Choose':  # переход в меню выбора персонажа
        action = hero_choose()
        if action:
            hero_creature, hero_sex = action

    cur_level = 0  # текущий уровень в последовательности

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

    pygame.display.flip()

    while running:
        pick_up = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    if pygame.sprite.spritecollideany(hero, items):
                        for item in items.sprites():
                            if pygame.sprite.collide_mask(hero, item):
                                item.picked(hero)
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

        # рисуем свой курсор
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 30, pygame.mouse.get_pos()[1] - 30))
        pygame.display.flip()
        all_sprites.update()
        clock.tick(FPS)
