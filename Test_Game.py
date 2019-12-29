import os
import sys

import pygame

pygame.init()


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
size = width, height = 600, 600
screen = pygame.display.set_mode(size)
all_sprites = pygame.sprite.Group()


def load_level(filename):
    filename = "data/levels/" + filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]

    # и подсчитываем максимальную длину
    max_width = max(map(len, level_map))

    # дополняем каждую строку пустыми клетками ('.')
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    image = pygame.image.load(fullname).convert()
    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


def generate_level(level, hero_type, sex):  # параметры персонажа надо получить из стартового меню
    new_player, x, y = None, None, None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '#':
                Border(x, y)
            elif level[y][x] == '@':
                new_player = Hero(hero_type, sex, x, y)
    # вернем игрока, а также размер поля в клетках
    return new_player


class AnimatedSprite(pygame.sprite.Sprite):  # база для анимированных спрайтов, режет листы анимаций
    def __init__(self, columns, rows, x, y, *sheets):
        super().__init__(all_sprites)
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


class Potion(AnimatedSprite):  # любое зелье
    # каждое зелье бафает определённые статы
    types = {'red': (2, 0, 0, 0)}

    def __init__(self, potion_type, x, y, size='small'):
        self.health, self.mana, self.dmg, self.speed = [i * (1 + (size == 'big')) for i in
                                                        Potion.types[potion_type]]
        potion_name = '_'.join(['flask', size, potion_type])
        super().__init__(1, 1, x, y, load_image(potion_name + '.png'),
                         load_image(potion_name + '_1.png'))

    def update(self):  # подсвечивается при подходе
        if not pygame.sprite.collide_mask(self, hero):
            self.image = self.frames[1]
        else:
            self.image = self.frames[0]


class Hero(AnimatedSprite):
    # классы определяются статами
    types = {'knight': (6, 150, 5, 5), 'wizzard': (4, 250, 3, 6), 'lizzard': (4, 150, 7, 7)}

    def __init__(self, hero_type, sex, pos_x, pos_y):
        self.heath, self.mana, self.dmg, self.speed = Hero.types[hero_type]
        # анимации ожидания и движения
        anim_sheets = (load_image('_'.join([hero_type, sex, 'idle', 'anim.png']), -1),
                       load_image('_'.join([hero_type, sex, 'run', 'anim.png']), -1))
        super().__init__(4, 1, pos_x * tile_width, pos_y * tile_height, *anim_sheets)
        self.direction = False
        self.is_running = False
        self.anim_timer = 0

    def get_pos(self):  # потом пригодится
        return self.rect.x + self.rect.w // 2, self.rect.y + self.rect.h // 2

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
            x = x * (self.speed ** 2 / (bool(x) + bool(y))) ** 0.5
            y = y * (self.speed ** 2 / (bool(x) + bool(y))) ** 0.5
            self.rect = self.rect.move(x, 0)
            if any([pygame.sprite.collide_mask(self, border) for border in borders]):
                self.rect = self.rect.move(-x, 0)
            self.rect = self.rect.move(0, y)
            if any([pygame.sprite.collide_mask(self, border) for border in borders]):
                self.rect = self.rect.move(0, -y)
        else:
            self.is_running = False
            while any([pygame.sprite.collide_mask(self, border) for border in borders]):
                self.rect = self.rect.move(0, 1)

    def update(self, *args):  # здесь отрисовка
        self.move()
        self.image = pygame.transform.flip(self.frames[self.cur_frame], self.direction, 0)
        self.mask = pygame.mask.from_surface(self.image)
        self.anim_timer += (1 / FPS)
        if self.anim_timer > 0.02 * self.speed:
            self.cur_frame = (self.cur_frame + 1) % 4 + 4 * self.is_running
            self.anim_timer = 0


borders = pygame.sprite.Group()


class Border(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites)
        self.add(borders)
        self.image = load_image("Wall.jpg", -1)
        # вычисляем маску для эффективного сравнения
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


def terminate():
    pygame.quit()
    sys.exit()


clock = pygame.time.Clock()

level = load_level('level_1.txt')
for i in level:
    print(*i)

hero = generate_level(level, 'wizzard', 'f')
player = pygame.sprite.Group(hero)
Potion('red', 150, 150)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()
    camera.update(hero)
    # обновляем положение всех спрайтов
    for sprite in all_sprites:
        camera.apply(sprite)
    screen.fill((0, 0, 0))
    all_sprites.draw(screen)
    player.draw(screen)
    pygame.display.flip()
    all_sprites.update()
    clock.tick(FPS)
