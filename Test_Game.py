import os
import random
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

size = width, height = 600, 600
screen = pygame.display.set_mode(size)
running = True
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


def generate_level(level):
    new_player, x, y = None, None, None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '#':
                Border(x, y)
            elif level[y][x] == '@':
                new_player = Knight(x, y)
    # вернем игрока, а также размер поля в клетках
    return new_player


class Knight(pygame.sprite.Sprite):
    knight = load_image("Knight2.png", -1)

    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites)
        self.image = Knight.knight
        self.rect = self.image.get_rect()
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
        # all_sprites.draw(screen)


borders = pygame.sprite.Group()


class Border(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites)
        self.add(borders)
        self.image = load_image("Wall.jpg", -1)
        self.rect = self.image.get_rect()
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

knight = generate_level(level)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()

    camera.update(knight)
    # обновляем положение всех спрайтов
    for sprite in all_sprites:
        camera.apply(sprite)
    screen.fill((255, 255, 255))
    all_sprites.draw(screen)
    all_sprites.update(event)

    pygame.display.flip()
    clock.tick(60)
