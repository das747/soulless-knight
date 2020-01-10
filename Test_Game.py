import os
import sys
import math
import random
import csv

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
FPS = 30
clock = pygame.time.Clock()
level_seq = ('1', '2')  # последоваельность смены уровней
cur_level = 0  # текущий уровень в последовательности
size = width, height = 1000, 1000
screen = pygame.display.set_mode(size)
all_sprites = pygame.sprite.Group()  # группа для обновления
items = pygame.sprite.Group()  # все предметы
top_layer = pygame.sprite.Group()  # группа для отрисовки всего что над персонажем
bottom_layer = pygame.sprite.Group()  # группа для отриосвки всего что под персонажем


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
    screen.blit(text, (rect.x + rect.w // 2 - text.get_rect().w // 2, rect.y - 25 - text.get_rect().h))
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
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(x, y)

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(frame_location, self.rect.size)))


class Explosion(AnimatedSprite):
    # sheet_format = {'ring': (8, 5), 'flat_effect': (6, 5), 'shockwave': (4, 5), 'explosion': (6, 5),
    #                 'flame': (6, 5)}
    sheet_format = {'1': (8, 1), '2': (8, 1), '3': (10, 1), '4': (12, 1), '5': (22, 1), '6': (8, 1)}

    def __init__(self,  x, y, shape='1',):
        # sheet_name = shape + '_' + color + '.png'
        sheet_name = 'explosion-' + shape + '.png'
        super().__init__(*Explosion.sheet_format[shape], x, y, load_image('effects/' + sheet_name))
        self.rect.center = (x, y)
        self.anim_timer = 0
        self.add(top_layer)

    def update(self):
        self.anim_timer += 1 / FPS
        if self.anim_timer >= 0.5 / len(self.frames):
            self.cur_frame += 1
            self.anim_timer = 0

        self.image = self.frames[self.cur_frame]
        if self.cur_frame >= len(self.frames) - 1:
            self.kill()


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


class Bullet(AnimatedSprite):
    def __init__(self, x, y, direction, bullet_type=''):
        super().__init__(1, 1, x, y, load_image('weapons/bullet' + bullet_type + '.png'))
        self.rect.center = (x, y)
        for i, frame in enumerate(self.frames):
            self.frames[i] = pygame.transform.rotate(frame, math.degrees(direction))
        self.image = self.frames[self.cur_frame]
        self.add(player)
        self.speed = 30
        self.speed_y = -math.sin(direction) * self.speed
        self.speed_x = math.cos(direction) * self.speed

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % self.frame_lim
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(self.speed_x, self.speed_y)


class Weapon(AnimatedSprite):
    types = {}
    with open('data/weapons/weapons_ref.csv') as ref:
        reader = csv.DictReader(ref)
        for line in reader:
            print(reader.fieldnames)
            types[line['name']] = line

    def __init__(self, name, x, y):
        self.name = name
        stats = Weapon.types[name]
        self.dmg = int(stats['damage'])
        self.mana_cost = int(stats['mana'])
        self.shoot_freq = float(stats['shots_per_second'])
        self.align_k = float(stats['align'])
        self.anim_length = float(stats['animation'])
        super().__init__(int(stats['frames']), 1, x, y, load_image('weapons/' + stats['image']))
        self.add(items)
        self.angle = None
        self.shooting = False
        self.picked_hero = None
        self.anim_timer = 0

        self.cooldown = 0

    def set_pos(self, x, y):
        self.rect.x, self.rect.y = x, y

    def align(self, rect):
        self.rect.centerx = rect.centerx
        self.rect.centery = rect.centery + rect.h // 2.5

    def picked(self, hero):
        hero.weapons.append(self)
        items.remove(self)
        player.add(self)
        self.picked_hero = hero

    def highlight(self):
        highlight(self.rect, self.name, self.mana_cost, self.dmg)

    def shoot(self):
        if self.cooldown <= 0:

            print(math.degrees(self.angle))
            base_rect = self.frames[0].get_rect()
            x = self.rect.centerx + math.cos(self.angle) * base_rect.w / 2 # - math.cos(self.angle) * self.rect.h / 2
            y = self.rect.centery - math.sin(self.angle) * base_rect.w / 2 # + math.sin(self.angle) * self.rect.h / 2
            Bullet(x, y, self.angle)
            self.shooting = True
            self.cooldown = 1 / self.shoot_freq

    def update(self):
        if self.shooting:
            self.anim_timer += 1 / FPS
            if self.anim_timer >= self.anim_length / self.frame_lim:
                self.cur_frame = (self.cur_frame + 1) % self.frame_lim
                self.shooting = not self.cur_frame == 0
                self.anim_timer = 0
        else:
            self.cur_frame = 0
        self.cooldown -= 1 / FPS
        self.image = self.frames[self.cur_frame]
        if self.picked_hero:
            new_image = pygame.Surface((int(self.image.get_rect().w * self.align_k),
                                        self.image.get_rect().h), pygame.SRCALPHA, 32)
            new_image.blit(self.image, (new_image.get_rect().w - self.image.get_rect().w, 0))
            self.image = new_image
            m_x, m_y = pygame.mouse.get_pos()
            angle = math.atan((hero.rect.y + hero.rect.h / 2 - m_y) /
                              (abs(hero.rect.x + hero.rect.w / 2 - m_x) + 1))
            old_rect = self.rect
            self.image = pygame.transform.rotate(self.image, math.degrees(angle))
            self.image = pygame.transform.flip(self.image, hero.direction, 0)
            self.rect = self.image.get_rect()
            self.rect.center = old_rect.center
            pygame.draw.rect(screen, (0, 0, 0), self.rect, 2)
            self.angle = angle
            if self.picked_hero.direction:
                self.angle = math.pi - self.angle


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
        self.weapons = []
        self.cur_weapon = 0
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

    def next_weapon(self):
        if self.weapons:
            self.cur_weapon = (self.cur_weapon + 1) % len(self.weapons)

    def heal(self, hp):
        self.health = min(self.health + hp, self.max_health)

    def restore_mana(self, mana):
        self.mana = min(self.mana + mana, self.max_mana)

    def add_buff(self, buff):
        self.buffs.append(list(buff))

    def set_pos(self, x, y):
        self.rect.x, self.rect.y = x, y

    def shoot(self):
        if self.weapons:
            self.weapons[self.cur_weapon].shoot()

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
            x = (x * (self.get_speed() ** 2 / (bool(x) + bool(y))) ** 0.5) #/ FPS * 10
            y = (y * (self.get_speed() ** 2 / (bool(x) + bool(y))) ** 0.5) #/ FPS * 10
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
        self.rect.h = self.image.get_rect().h
        self.rect.w = self.image.get_rect().w
        # self.mask = pygame.mask.from_surface(self.image)
        self.anim_timer += (1 / FPS)
        for buff in self.buffs:
            buff[-1] -= 1 / FPS
        self.buffs = list(filter(lambda b: b[-1] > 0, self.buffs))
        if self.anim_timer > 1 / self.get_speed():
            self.cur_frame = (self.cur_frame + 1) % self.frame_lim + self.frame_lim * self.is_running
            self.anim_timer = 0
        if self.weapons:
            self.weapons[self.cur_weapon].align(self.rect)

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
        # pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)


borders = pygame.sprite.Group()
decorations = pygame.sprite.Group()


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


level = load_level(f'level_{level_seq[cur_level]}.txt')
for i in level:
    print(*i)

hero = Hero('lizard', 'f', 0, 0)
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
Weapon('Револьвер', 150, 250)
Weapon('MP40', 150, 280)
Weapon('Гранатомёт', 150, 300)

running = True
pick_up = False

while running:
    pick_up = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                pick_up = True
            elif event.key == pygame.K_r:
                hero.next_weapon()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == pygame.BUTTON_LEFT:
                hero.shoot()
            # Explosion(*event.pos, random.choice(list(Explosion.sheet_format.keys())))
            # Bullet(*event.pos, hero.weapons[hero.cur_weapon].angle)
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
    all_sprites.update()
    pygame.display.flip()
    clock.tick(FPS)
