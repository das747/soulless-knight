import os
import random
import sys
import pygame
from pygame.display import set_mode

pygame.init()

import ctypes


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

user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
size = width, height = 1000, 770
screen = pygame.display.set_mode(size)
running = True
all_sprites = pygame.sprite.Group()


def draw_backpack():
    backpack = load_image("backpack.png", -1)
    screen.blit(backpack, (0, 0))


def load_level(filename):
    filename = "data/levels/" + filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]

    # и подсчитываем максимальную длину
    max_width = max(map(len, level_map))

    # дополняем каждую строку пустыми клетками ('.')
    return list(map(lambda x: x.ljust(max_width, ','), level_map))


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


def generate_level(level):
    new_player, i, j = None, None, None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '.':
                Floor(x, y)
            elif level[y][x] == '#':
                Border(x, y)
                if y + 1 != '#':
                    Botton_Wall(x, y)
            elif level[y][x] == '@':
                Floor(x, y)
                i, j = x, y
    Weapon(6, 15, 'one_punch')
    #Weapon(7, 17, 'one_punch')
    new_player = Knight(i, j)
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '#':
                Top_Wall(x, y)
    draw_backpack()
    # вернем игрока, а также размер поля в клетках
    return new_player


class Knight(pygame.sprite.Sprite):
    knight = load_image("Разбойник.png", -1)

    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites)
        self.image = Knight.knight
        self.add(hero)
        self.rect = self.image.get_rect()
        self.weapons = [0, 0]
        self.weapon_selected = 0
        # вычисляем маску для эффективного сравнения
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)

    def update(self, *args):
        args = args[0]
        speed = 5
        keys = pygame.key.get_pressed()
        x, y = 0, 0
        if keys[pygame.K_LEFT]:
            self.rect = self.rect.move(-speed, 0)
            x = -speed
            self.image = pygame.transform.flip(self.knight, 1, 0)
        elif keys[pygame.K_RIGHT]:
            self.rect = self.rect.move(speed, 0)
            x = speed
            self.image = self.knight
        while pygame.sprite.spritecollideany(self, borders):
            self.rect = self.rect.move(-x, 0)
        if keys[pygame.K_UP]:
            self.rect = self.rect.move(0, -speed)
            y = -speed
        elif keys[pygame.K_DOWN]:
            self.rect = self.rect.move(0, speed)
            y = speed
        while pygame.sprite.spritecollideany(self, borders):
            self.rect = self.rect.move(0, -y)

        if pygame.sprite.spritecollideany(self, weapon):
            weapon_bar = load_image("Weapon_bar.png", -1)
            gun = pygame.sprite.spritecollideany(self, weapon)
            font = pygame.font.Font(None, 50)
            text = font.render(gun.name, 1, (255, 255, 0))
            screen.blit(text, (width // 2 - 210, height - 150))
            screen.blit(weapon_bar, (width // 2 - 210, height - 120))

hero = pygame.sprite.Group()
borders = pygame.sprite.Group()
decorations = pygame.sprite.Group()
weapon = pygame.sprite.Group()


class Border(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites)
        self.add(borders)
        self.image = load_image("Wall.jpg", -1)
        self.rect = self.image.get_rect()
        # вычисляем маску для эффективного сравнения
        # self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


class Top_Wall(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites)
        self.add(decorations)
        self.image = load_image("wall_2.jpg", -1)
        self.rect = self.image.get_rect()
        # вычисляем маску для эффективного сравнения
        # self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y - 20)


class Botton_Wall(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites)
        self.add(decorations)
        self.image = load_image("wall_3.png", -1)
        self.rect = self.image.get_rect()
        # вычисляем маску для эффективного сравнения
        # self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y + 20)


class Floor(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites)
        self.add(decorations)
        self.image = load_image("floor.jpg", -1)
        self.rect = self.image.get_rect()
        # вычисляем маску для эффективного сравнения
        # self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


class Weapon(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, name):
        super().__init__(all_sprites)
        self.add(weapon)
        self.image = load_image("{}.png".format(name), -1)
        self.rect = self.image.get_rect()
        self.name = name
        # вычисляем маску для эффективного сравнения
        # self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


def terminate():
    pygame.quit()
    sys.exit()


clock = pygame.time.Clock()

level = load_level('level_1.txt')
for i in level:
    print(*i)
knight = generate_level(level)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()

    camera.update(knight)
    # обновляем положение всех спрайтов
    for sprite in all_sprites:
        camera.apply(sprite)
    screen.fill((0, 0, 0))
    all_sprites.draw(screen)
    all_sprites.update(pygame.event.get())
    pygame.display.flip()
    clock.tick(80)
