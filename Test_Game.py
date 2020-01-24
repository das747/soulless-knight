import os
import sys
import math
import csv

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
level_seq = ('1', '3')  # последоваельность смены уровней

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


def is_wall(x_pos, y_pos):
    for tile in borders.sprites():
        rect = pygame.Rect(tile.rect)
        rect.y -= 10
        rect.h = tile_height
        if rect.collidepoint(x_pos, y_pos):
            return True
    return False


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
    all_sprites.remove(*items.sprites(), *top_layer.sprites(), *bottom_layer.sprites(),
                       enemies.sprites())
    items.empty()
    borders.empty()
    top_layer.empty()
    bottom_layer.empty()
    obstacles.empty()
    enemies.empty()
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
    screen.blit(text, (rect.x + rect.w // 2 - text.get_rect().w // 2,
                       rect.y - 25 - text.get_rect().h))
    pygame.draw.polygon(screen, (255, 255, 255), ((rect.x + rect.w // 2, rect.y),
                                                  (rect.x + rect.w // 2 - 15, rect.y - 15),
                                                  (rect.x + rect.w // 2 + 15, rect.y - 15)))
    if stats:
        rect = Weapon.stat_bar.get_rect()
        screen.blit(Weapon.stat_bar, (width // 2 - rect.w // 2, height - rect.h))
        for i, stat in enumerate(stats):
            text = font.render(str(stat), 1, (255, 255, 255))
            screen.blit(text,
                        (width // 2 - rect.w // 2 + rect.w // 3 * (i + 0.5) + text.get_rect().w // 2,
                         height - rect.h // 2 - text.get_rect().h // 2))


def draw_HUD(hero):
    font = pygame.font.Font(None, 30)
    health = font.render(str(hero.get_health()) + '/' + str(hero.max_health), 1, (255, 255, 255))
    mana = font.render(str(hero.get_mana()) + '/' + str(hero.max_mana), 1, (255, 255, 255))
    armor = font.render(str(hero.armor) + '/' + str(hero.max_armor), 1, (255, 255, 255))
    for i in range(3):
        pygame.draw.rect(screen, (163, 132, 102),
                         (48, 13 + 31 * i, 185, 26), 0)
    if hero.get_health():
        pygame.draw.rect(screen, (255, 64, 69),
                         (49, 13, int(185 / (hero.max_health / hero.get_health())), 26), 0)
    if hero.armor:
        pygame.draw.rect(screen, (150, 150, 150),
                         (49, 44, int(185 / (hero.max_armor / hero.armor)), 26), 0)
    if hero.get_mana():
        pygame.draw.rect(screen, (72, 114, 164),
                         (49, 75, int(185 / (hero.max_mana / hero.get_mana())), 26), 0)
    screen.blit(Hero.stat_bar, (0, 0))
    screen.blit(health, (120, 18))
    screen.blit(armor, (120, 49))
    screen.blit(mana, (100, 80))


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
        self.anim_timer = 0

    def get_pos(self):
        return self.rect.centerx, self.rect.centery

    def set_pos(self, x, y):
        self.rect.x, self.rect.y = x, y

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(frame_location, self.rect.size)))


class Explosion(AnimatedSprite):
    # sheet_format = {'ring': (8, 5), 'flat_effect': (6, 5),
    #                 'shockwave': (4, 5), 'explosion': (6, 5), 'flame': (6, 5)}
    sheet_format = {'1': (8, 1), '2': (8, 1), '3': (10, 1), '4': (12, 1), '5': (22, 1), '6': (8, 1)}

    def __init__(self, x, y, shape='1'):
        # sheet_name = shape + '_' + color + '.png'
        sheet_name = 'explosion-' + shape + '.png'
        super().__init__(*Explosion.sheet_format[shape], x, y, load_image('effects/' + sheet_name))
        self.rect.center = (x, y)
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
    types = {'bullet': {'a': 0, 'speed': 300, 'image': 'bullet3.png', 'frames': 1, 'explosion': '1'},
             'missile': {'a': 400, 'speed': 200, 'image': 'missle.png', 'frames': 8, 'explosion': '4'}}

    def __init__(self, x, y, direction, damage, bullet_type='bullet'):
        self.damage = damage
        self.type = bullet_type
        self.direction = direction
        stats = Bullet.types[bullet_type]
        super().__init__(stats['frames'], 1, x, y, load_image('weapons/' + stats['image']))
        self.rect.center = (x, y)
        for i, frame in enumerate(self.frames):
            self.frames[i] = pygame.transform.rotate(frame, math.degrees(direction))
        self.image = self.frames[self.cur_frame]
        self.speed_y = -math.sin(direction) * stats['speed']
        self.speed_x = math.cos(direction) * stats['speed']
        self.move_x, self.move_y = 0, 0

    def update(self):
        self.anim_timer += 1 / FPS
        if self.anim_timer >= 0.5 / self.frame_lim:
            self.cur_frame = min(self.cur_frame + 1, self.frame_lim - 1)
            self.anim_timer = 0
        self.image = self.frames[self.cur_frame]
        self.speed_x += Bullet.types[self.type]['a'] * math.cos(self.direction) / FPS
        self.speed_y -= Bullet.types[self.type]['a'] * math.sin(self.direction) / FPS
        self.rect = self.rect.move(int(self.move_x), int(self.move_y))
        self.move_x = self.move_x - int(self.move_x) + self.speed_x / FPS
        self.move_y = self.move_y - int(self.move_y) + self.speed_y / FPS
        coll = pygame.sprite.spritecollide(self, all_sprites, 0)
        obst_coll = pygame.sprite.Group(*[sprite for sprite in coll if obstacles.has(sprite)])
        if obst_coll.sprites():
            mask_coll = pygame.sprite.spritecollide(self, obst_coll, 0, pygame.sprite.collide_mask)
            if mask_coll:
                enemy_coll = [sprite for sprite in mask_coll if enemies.has(sprite)]
                if player.has(self) and not pygame.sprite.collide_mask(self, hero):
                    Explosion(*self.rect.center, Bullet.types[self.type]['explosion'])
                    self.kill()
                    for enemy in enemy_coll:
                        enemy.hit(self.damage)
                elif enemies.has(self) and mask_coll != enemy_coll:
                    Explosion(*self.rect.center, Bullet.types[self.type]['explosion'])
                    self.kill()
                    hero.hit(self.damage)
        elif coll[0] == self:
            self.kill()


class Weapon(AnimatedSprite):
    types = {}
    with open('data/weapons/weapons_ref.csv') as ref:
        reader = csv.DictReader(ref)
        for line in reader:
            types[line['name']] = line

    stat_bar = load_image('stat_bar.png')

    def __init__(self, name, x, y):
        self.name = name
        stats = Weapon.types[name]
        self.dmg = int(stats['damage'])
        self.mana_cost = int(stats['mana'])
        self.shoot_freq = float(stats['shots_per_second'])
        self.align_k = float(stats['align'])
        self.anim_length = float(stats['animation'])
        self.bullet_type = stats['bullet']
        shoot_x, shoot_y = [int(i) for i in stats['shoot_point'].split(';')]
        super().__init__(int(stats['frames']), 1, x, y, load_image('weapons/' + stats['image']))
        self.rect.w *= self.align_k
        shoot_x += self.rect.w // 2
        shoot_y -= self.rect.h // 2
        self.shoot_radius = (shoot_x ** 2 + shoot_y ** 2) ** 0.5
        self.shoot_angle = (math.atan(shoot_y / shoot_x))
        # print(self.rect.w, self.rect.h)
        # print(self.shoot_angle, self.shoot_freq)
        self.add(items)
        self.angle = None
        self.shooting = False
        self.picked_hero = None
        self.cooldown = 0

    def align(self, rect):
        self.rect.centerx = rect.centerx
        self.rect.centery = rect.centery + rect.h // 2.5

    def drop(self, pos):
        if player.has(self):
            self.remove(player)
        else:
            self.remove(enemies)
        self.add(items)
        self.picked_hero.weapons.remove(self)
        self.set_pos(*pos)
        self.picked_hero = None

    def picked(self, character):
        character.weapons.insert(0, self)
        if len(character.weapons) > character.inventory_size:
            character.weapons[1].drop(character.get_pos())

        items.remove(self)
        if player.has(character):
            self.add(player)
        else:
            self.add(enemies)
        self.picked_hero = character

    def highlight(self):
        highlight(self.rect, self.name, self.dmg, self.mana_cost, self.shoot_freq)

    def shoot(self):
        if self.cooldown <= 0:
            y = self.rect.centery - self.shoot_radius * math.sin(self.shoot_angle + self.angle)
            if not self.picked_hero.direction:
                x = self.rect.centerx + self.shoot_radius * math.cos(self.shoot_angle + self.angle)

            else:
                x = self.rect.centerx - self.shoot_radius * math.cos(self.shoot_angle + self.angle)
                self.angle = math.pi - self.angle

            shot = Bullet(x, y, self.angle, self.dmg + self.picked_hero.get_dmg(), self.bullet_type)
            if player.has(self):
                player.add(shot)
            else:
                enemies.add(shot)
            self.shooting = True
            self.cooldown = 1 / self.shoot_freq * self.picked_hero.speed / self.picked_hero.get_speed()

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
            if self is self.picked_hero.get_current_weapon():
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
                # pygame.draw.rect(screen, (0, 0, 0), self.rect, 2)
                self.angle = angle
                # if self.picked_hero.direction:
                #     self.angle = math.pi - self.angle
            else:
                self.image = pygame.Surface((0, 0), pygame.SRCALPHA, 32)


class Character(AnimatedSprite):
    def __init__(self, x, y, stats, *sheets):
        # инициализируем статы
        self.health, self.mana, self.dmg, self.speed = stats
        self.max_health, self.max_mana = self.health, self.mana
        super().__init__(4, 1, x, y, *sheets)
        self.add(obstacles)
        # вычисление маски по максимальной форме
        mask_surface = pygame.Surface((100, 100), pygame.SRCALPHA, 32)
        self.frames = [pygame.transform.scale2x(frame) for frame in self.frames]
        for frame in self.frames:
            mask_surface.blit(frame, (0, 0))
            mask_surface.blit(pygame.transform.flip(frame, True, False), (0, 0))
        self.mask = pygame.mask.from_surface(mask_surface)
        # вспомогательные атрибуты
        self.direction = False
        self.is_running = False
        self.move_x = self.move_y = 0
        self.buffs = []
        self.weapons = []
        self.stun = 0

    # методы для измерения характеристик
    def get_health(self):
        return self.health

    def get_mana(self):
        return self.mana

    def get_dmg(self):
        return self.dmg + sum([buff[0] for buff in self.buffs])

    def get_speed(self):
        return self.speed + sum([buff[1] for buff in self.buffs])

    def get_current_weapon(self):
        if self.weapons:
            return self.weapons[0]

    # методы для изменения характеристик
    def heal(self, hp):
        self.health = min(self.health + hp, self.max_health)

    def restore_mana(self, mana):
        self.mana = min(self.mana + mana, self.max_mana)

    def add_buff(self, buff):
        self.buffs.append(list(buff))

    def hit(self, dmg):
        if not self.stun:
            self.health = max(self.health - dmg, 0)
            self.stun = 0.3

    # методы движения
    def define_movement(self):  # определение направления движения
        return 0, 0

    def move(self, x, y):  # перемещение модели и проверка столкновения со стенами
        if x or y:
            self.is_running = True
            self.move_x += (x * ((self.get_speed() * 40) ** 2 / (bool(x) + bool(y))) ** 0.5) / FPS
            self.move_y += (y * ((self.get_speed() * 40) ** 2 / (bool(x) + bool(y))) ** 0.5) / FPS
            self.rect = self.rect.move(int(self.move_x), 0)
            collide = pygame.sprite.spritecollide(self, borders, 0, pygame.sprite.collide_mask)
            if collide:
                if not (len(collide) == 1 and self in collide):
                    self.rect = self.rect.move(-int(self.move_x), 0)
            self.move_x -= int(self.move_x)
            self.rect = self.rect.move(0, self.move_y)
            collide = pygame.sprite.spritecollide(self, borders, 0, pygame.sprite.collide_mask)
            if collide:
                if not (len(collide) == 1 and self in collide):
                    self.rect = self.rect.move(0, -self.move_y)
            self.move_y -= int(self.move_y)

    def update(self, *args):  # просчёт динамических характеристик
        self.stun = max(0, self.stun - 1 / FPS)
        if not self.stun:
            self.move(*self.define_movement())

        self.anim_timer += (1 / FPS)
        if self.anim_timer > 1 / self.get_speed():
            self.cur_frame = (self.cur_frame + 1) % self.frame_lim + self.frame_lim * self.is_running
            self.anim_timer = 0
        self.image = pygame.transform.flip(self.frames[self.cur_frame], self.direction, 0)
        self.rect.h = self.image.get_rect().h
        self.rect.w = self.image.get_rect().w

        for buff in self.buffs:
            buff[-1] -= 1 / FPS
        self.buffs = list(filter(lambda b: b[-1] > 0, self.buffs))
        if self.weapons:
            self.get_current_weapon().align(self.rect)

        self.is_running = False
        # pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)


class Hero(Character):
    # классы определяются статами
    types = {'knight': (6, 150, 5, 5), 'wizzard': (4, 250, 3, 6), 'lizard': (4, 150, 7, 7)}
    stat_bar = load_image("hero_bar.png")

    def __init__(self, hero_type, sex, pos_x, pos_y):
        # анимации ожидания и движения
        anim_sheets = (load_image('_'.join([hero_type, sex, 'idle', 'anim.png'])),
                       load_image('_'.join([hero_type, sex, 'run', 'anim.png'])))
        # загрузка картинки через название и пол персонажа
        stats = Hero.types[hero_type]
        super().__init__(pos_x * tile_width, pos_y * tile_height, stats, *anim_sheets)
        hit_frame = load_image('_'.join([hero_type, sex, 'hit', 'anim.png']))
        self.frames.append(pygame.transform.scale2x(hit_frame))
        self.inventory_size = 2
        self.armor = self.max_armor = self.max_health
        self.armor_cd = 0

    def next_weapon(self):
        if len(self.weapons) > 1:
            self.weapons.insert(0, self.weapons.pop())

    def hit(self, dmg):
        self.armor, dmg = max(0, self.armor - dmg), max(0, dmg - self.armor)
        self.armor_cd = 4
        super().hit(dmg)

    def shoot(self):
        if self.weapons:
            weapon = self.get_current_weapon()
            if self.get_mana() >= weapon.mana_cost:
                self.mana -= weapon.mana_cost
                weapon.shoot()

    def define_movement(self):  # отслеживание перемещения
        keys = pygame.key.get_pressed()
        x, y = 0, 0
        if pygame.mouse.get_pos()[0] < width // 2:
            self.direction = True
        else:
            self.direction = False
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            x = -1
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            x = 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            y = -1
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            y = 1
        return x, y

    def update(self):
        super().update()
        if self.armor != self.max_armor:
            self.armor_cd -= 1 / FPS
            if self.armor_cd <= 0:
                self.armor += 1
                self.armor_cd = 1
        if self.stun:
            self.image = self.frames[-1]


class Enemy(Character):
    fractions = ('zoombie', 'demon', 'orc')

    def __init__(self, x, y, name, stats):
        anim_sheets = (load_image('characters/' + '_'.join([name, 'idle', 'anim.png'])),
                       load_image('characters/' + '_'.join([name, 'run', 'anim.png'])))
        super().__init__(x, y, stats, *anim_sheets)
        self.add(enemies, borders)
        self.too_close = False
        self.norm_distance = 150

    def update(self, *arg):
        super().update()
        if pygame.sprite.collide_mask(self, hero):
            hero.hit(self.dmg)
            self.too_close = True
        if self.get_health() == 0:
            self.kill()


class Rusher(Enemy):
    """самые маленькие противники, просто бегут на игрока,
    после столкновения с игроком немного отходят
    бегают быстрее всех персонажей, только атака столкновением"""
    def __init__(self, x, y, fraction='zombie'):
        super().__init__(x, y, 'tiny_' + fraction, (10, 0, 1, 3))
        self.norm_distance = 100

    def define_movement(self):
        hero_x, hero_y = hero.get_pos()
        if self.too_close:
            x = -1 + (not (hero_x - self.rect.centerx > 20)) + (self.rect.centerx - hero_x > 20)
            y = -1 + (not (hero_y - self.rect.centery > 20)) + (self.rect.centery - hero_y > 20)
            self.too_close = ((abs(self.rect.y - hero_y) ** 2 +
                               abs(self.rect.x - hero_x) ** 2) ** 0.5 < self.norm_distance)
        else:
            x = 1 - (not (hero_x - self.rect.centerx > 20)) - (self.rect.centerx - hero_x > 20)
            y = 1 - (not (hero_y - self.rect.centery > 20)) - (self.rect.centery - hero_y > 20)
        self.direction = x == -1
        return x, y


class Summoner(Enemy):
    """маги, умеют кастовать Rusher'ов, стараются держаться на расстоянии от игрока, не преследуют
    если игрок подходит слишеом близко могут атаковать или телепортироваться"""
    def __init__(self, x, y, fraction='zombie'):
        super().__init__(x, y, 'magic_' + fraction, (20, 0, 4, 6))
        self.fraction = fraction
        self.norm_distance = 150
        self.min_distance = 100
        self.max_distance = 250
        self.cast_cd = 0

    def define_movement(self):
        hero_x, hero_y = hero.get_pos()
        hero_dist = (abs(self.rect.y - hero_y) ** 2 + abs(self.rect.x - hero_x) ** 2) ** 0.5
        x, y = 0, 0
        if self.too_close:
            x = -1 + (not (hero_x - self.rect.centerx > 20)) + (self.rect.centerx - hero_x > 20)
            y = -1 + (not (hero_y - self.rect.centery > 20)) + (self.rect.centery - hero_y > 20)
            self.too_close = hero_dist < self.norm_distance
            self.direction = x == -1
        else:
            self.too_close = hero_dist < self.min_distance
            if hero_dist > self.max_distance:
                x = 1 - (not (hero_x - self.rect.centerx > 20)) - (self.rect.centerx - hero_x > 20)
                y = 1 - (not (hero_y - self.rect.centery > 20)) - (self.rect.centery - hero_y > 20)
                self.direction = x == -1
            elif not self.cast_cd:
                if not is_wall(self.rect.left - 20, self.rect.centery):
                    Rusher(self.rect.left - 20, self.rect.centery, self.fraction)
                if not is_wall(self.rect.centerx, self.rect.top - 30):
                    Rusher(self.rect.centerx, self.rect.top - 30, self.fraction)
                if not is_wall(self.rect.right + 40, self.rect.centery):
                    Rusher(self.rect.right + 20, self.rect.centery, self.fraction)
                if not is_wall(self.rect.centerx, self.rect.bottom + 40):
                    Rusher(self.rect.centerx, self.rect.bottom + 20, self.fraction)
                self.cast_cd += 15
        return x, y

    def update(self):
        super().update()
        self.cast_cd = max(0, self.cast_cd - 1 / FPS)


class Fighter(Enemy):
    """обычные бойцы, стреляют по кд, держатся на расстоянии, но не отходят далеко """
    def __init__(self, x, y, fraction='zombie'):
        super().__init__(x, y, 'warrior_' + fraction, (20, 0, 4, 5))


class Elemental(Enemy):
    """те же Fighter'ы но со стихийными пулями(демоны - огонь, зомби - заморозка, орки - яд)"""
    def __init__(self, x, y, fraction='zombie'):
        super().__init__(x, y, 'element_' + fraction, (25, 0, 4, 5))


class Guard(Enemy):
    """тяжёлые бойцы, мало двигаются, старются идти к игроку,
    стреляют масиированно, возможно атака по площади
    в целом медленные, большой кд"""
    def __init__(self, x, y, fraction='zombie'):
        super().__init__(x, y, 'big_' + fraction, (45, 0, 6, 3))


borders = pygame.sprite.Group()
cursor = pygame.transform.scale(load_image('cursor.jpg', -1), (60, 60))
obstacles = pygame.sprite.Group()


class Border(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites, borders, bottom_layer, obstacles)
        self.image = load_image("Wall.jpg")
        # вычисляем маску для эффективного сравнения
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y)


class TopWall(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites, top_layer, obstacles)
        self.image = load_image("wall_top.jpg")
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y - 20)


class BottomWall(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites, bottom_layer, obstacles)
        self.image = load_image("wall_bottom.png")
        self.rect = self.image.get_rect().move(tile_width * pos_x, tile_height * pos_y + 20)


class Floor(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites, bottom_layer)
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
                    hero_image = ShowHero(0, 0, heroes[cur_hero], sex)
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
    enemies = pygame.sprite.Group()

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
    Weapon('Револьвер', 150, 250)
    Weapon('MP40', 150, 280)
    Weapon('Гранатомёт', 150, 300)
    Summoner(200, 300, 'zombie')
    # Rusher(250, 300, 'demon')
    # Rusher(160, 300, 'orc')

    while running:
        pick_up = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # игра оставнавливается, если нажать Esc
                    if pause() == 'Exit':
                        running = False
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
        enemies.draw(screen)
        top_layer.draw(screen)
        draw_HUD(hero)
        pick = pygame.sprite.spritecollide(hero, items, 0, pygame.sprite.collide_mask)
        if pick:
            pick[0].highlight()
            if pick_up:
                pick[0].picked(hero)
        screen.blit(cursor, (pygame.mouse.get_pos()[0] - 30, pygame.mouse.get_pos()[1] - 30))
        pygame.display.flip()
        all_sprites.update()
        clock.tick(FPS)
