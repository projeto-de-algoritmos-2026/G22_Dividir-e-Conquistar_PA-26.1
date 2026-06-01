import pygame
import random
import math
from constantes import *
from entidades import Player, Bullet, Zombie
from algoritmos import median_of_medians, merge_groups_by_closest
from algoritmos import dist as alg_dist


class Jogo:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((LARGURA, ALTURA))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)
        self.player = Player()
        self.bullets = []
        self.zombies = []
        self.groups = {}
        self.start_ticks = pygame.time.get_ticks()
        self.hordes_spawned = 0
        self.horde_count = 5
        self.horde_size = 8
        self.victory = False
        self.victory_time = 0
        self.game_over = False
        self.game_over_time = 0
        self.shake_timer = 0.0
        self.shake_magnitude = 0.0
        self.flash_timer = 0.0

        self.started = False
        self.start_button = pygame.Rect(LARGURA//2-80, ALTURA//2-20, 160, 40)

    def spawn_wave(self, count):
        min_sep = 80
        start_idx = len(self.zombies)
        for _ in range(count):
            attempts = 0
            while True:
                x = random.randint(20, LARGURA-20)
                y = random.randint(20, ALTURA-20)
                ok = True
                for z in self.zombies:
                    if math.hypot(z.pos[0]-x, z.pos[1]-y) < min_sep:
                        ok = False; break
                attempts += 1
                if ok or attempts > 30:
                    break
            strength = random.randint(5, 50)
            self.zombies.append(Zombie(x, y, strength))
        for idx in range(start_idx, len(self.zombies)):
            gid = max(self.groups.keys(), default=-1) + 1
            self.groups[gid] = set([idx])

    def choose_alpha(self, indices):
        strengths = [self.zombies[i].strength for i in indices]
        if not strengths:
            return None
        med = median_of_medians(strengths, len(strengths)//2)
        best = indices[0]
        best_diff = abs(self.zombies[best].strength - med)
        for i in indices:
            d = abs(self.zombies[i].strength - med)
            if d < best_diff:
                best = i; best_diff = d
        return best

    def assign_group_ids(self):
        for gid, s in self.groups.items():
            for idx in s:
                self.zombies[idx].group_id = gid

    def apply_alpha_buffs(self):
        for z in self.zombies:
            z.speed = z.base_speed
            z.group_strength = z.strength
        for gid, s in self.groups.items():
            size = len(s)
            if size <= 1:
                continue
            strength_mul = 1.0 + 0.06 * (size - 1)
            speed_mul = 1.0 + 0.04 * (size - 1)
            for idx in s:
                z = self.zombies[idx]
                z.group_strength = int(z.strength * strength_mul)
                z.speed = z.base_speed * speed_mul

    def run(self):
        running = True
        try:
            while running:
                dt = self.clock.tick(60)/1000.0
                t = (pygame.time.get_ticks() - self.start_ticks)/1000.0 if self.started else 0.0

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        mx, my = event.pos
                        if not self.started:
                            if self.start_button.collidepoint(mx, my):
                                self.started = True
                                self.start_ticks = pygame.time.get_ticks()
                                self.spawn_wave(10)
                                self.groups = {i:{i} for i in range(len(self.zombies))}
                            continue
                        if self.game_over:
                            continue
                        self.bullets.append(Bullet(self.player.pos[0], self.player.pos[1], mx, my))
                    elif event.type == pygame.KEYDOWN:
                        if self.game_over:
                            if event.key == pygame.K_r:
                                self.__init__()
                                continue
                            if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                                running = False
                                break
                        if self.victory:
                            if event.key == pygame.K_r:
                                self.__init__()
                                continue
                            if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                                running = False
                                break

                mouse_pos = pygame.mouse.get_pos()
                self.player.set_aim(mouse_pos)

                if not self.started:
                    self.screen.fill(BLACK)
                    title = self.font.render('Zombie Survival: Alpha Horde', True, WHITE)
                    instr = self.font.render('Clique em Iniciar para começar', True, WHITE)
                    pygame.draw.rect(self.screen, (50,150,50), self.start_button)
                    btn_txt = self.font.render('Iniciar', True, WHITE)
                    self.screen.blit(title, (LARGURA//2 - title.get_width()//2, ALTURA//2 - 120))
                    self.screen.blit(instr, (LARGURA//2 - instr.get_width()//2, ALTURA//2 - 80))
                    self.screen.blit(btn_txt, (self.start_button.x + self.start_button.width//2 - btn_txt.get_width()//2,
                                               self.start_button.y + self.start_button.height//2 - btn_txt.get_height()//2))
                    pygame.display.flip()
                    continue

                if self.game_over:
                    self.screen.fill(BLACK)
                    go_txt = self.font.render('GAME OVER', True, (240,80,80))
                    sub_txt = self.font.render(f'Tempo sobrevivido: {int(self.game_over_time)}s    Hordas alcançadas: {self.hordes_spawned}', True, WHITE)
                    hint = self.font.render('Pressione R para reiniciar, Q ou ESC para sair.', True, WHITE)
                    self.screen.blit(go_txt, (LARGURA//2 - go_txt.get_width()//2, ALTURA//2 - 60))
                    self.screen.blit(sub_txt, (LARGURA//2 - sub_txt.get_width()//2, ALTURA//2 - 20))
                    self.screen.blit(hint, (LARGURA//2 - hint.get_width()//2, ALTURA//2 + 20))
                    pygame.display.flip()
                    continue

                if self.victory:
                    self.screen.fill((50,120,50))
                    vtxt = self.font.render('VOCÊ VENCEU!', True, WHITE)
                    info = self.font.render(f'Hordas derrotadas: {self.hordes_spawned}/{self.horde_count}    Tempo: {int(self.victory_time)}s', True, WHITE)
                    hint2 = self.font.render('Pressione R para jogar novamente, Q para sair.', True, WHITE)
                    self.screen.blit(vtxt, (LARGURA//2 - vtxt.get_width()//2, ALTURA//2 - 60))
                    self.screen.blit(info, (LARGURA//2 - info.get_width()//2, ALTURA//2 - 20))
                    self.screen.blit(hint2, (LARGURA//2 - hint2.get_width()//2, ALTURA//2 + 20))
                    pygame.display.flip()
                    continue

                if len(self.zombies) == 0 and self.hordes_spawned < self.horde_count:
                    self.hordes_spawned += 1
                    self.spawn_wave(self.horde_size)
                    new_indices = list(range(len(self.zombies) - self.horde_size, len(self.zombies)))
                    ai = self.choose_alpha(new_indices)
                    if ai is not None:
                        self.zombies[ai].is_alpha = True

                if self.hordes_spawned >= self.horde_count and len(self.zombies) == 0:
                    if not self.victory:
                        self.victory = True
                        self.victory_time = t

                merge_threshold = 20 + min(200, int(t*1.0))
                self.groups = merge_groups_by_closest(self.zombies, self.groups, merge_threshold)
                self.assign_group_ids()
                for gid, s in list(self.groups.items()):
                    members = list(s)
                    if not members:
                        continue
                    strengths = [self.zombies[i].strength for i in members]
                    med = median_of_medians(strengths, len(strengths)//2)
                    best_idx = members[0]
                    best_diff = abs(self.zombies[best_idx].strength - med)
                    for idx in members:
                        d = abs(self.zombies[idx].strength - med)
                        if d < best_diff:
                            best_idx = idx
                            best_diff = d
                    for idx in members:
                        self.zombies[idx].is_alpha = False
                    self.zombies[best_idx].is_alpha = True
                self.apply_alpha_buffs()

                self.player.update(dt)
                for b in self.bullets:
                    b.update()
                self.bullets = [b for b in self.bullets if 0<=b.pos[0]<=LARGURA and 0<=b.pos[1]<=ALTURA]

                for z in self.zombies:
                    if alg_dist(z.pos, self.player.pos) < z.radius + self.player.radius:
                        eff_strength = getattr(z, 'group_strength', z.strength)
                        damage = max(3, int(8 * (eff_strength / 30.0)))
                        if self.player.take_damage(damage):
                            self.shake_timer = 0.35
                            self.shake_magnitude = min(18, 8 * (eff_strength / 30.0) + 4)
                            self.flash_timer = 0.18
                            pygame.display.flip()
                            pygame.time.delay(120)
                            if self.player.health <= 0:
                                self.game_over = True
                                self.game_over_time = t

                for b in list(self.bullets):
                    for z in self.zombies:
                        if alg_dist(b.pos, z.pos) < b.radius + z.radius:
                            z.health -= 25
                            try:
                                self.bullets.remove(b)
                            except ValueError:
                                pass
                            break

                alive = []
                old_to_new = {}
                for i,z in enumerate(self.zombies):
                    if z.health > 0:
                        old_to_new[i] = len(alive)
                        alive.append(z)
                if len(alive) != len(self.zombies):
                    new_groups = {}
                    for gid,s in self.groups.items():
                        new_set = set()
                        for idx in s:
                            if idx in old_to_new:
                                new_set.add(old_to_new[idx])
                        if new_set:
                            new_groups[gid] = new_set
                    self.groups = new_groups
                    self.zombies = alive

                for z in self.zombies:
                    z.update(self.player.pos)

                temp = pygame.Surface((LARGURA, ALTURA))
                temp.fill(BLACK)
                for gid,s in self.groups.items():
                    members = list(s)
                    for i in range(len(members)):
                        for j in range(i+1, len(members)):
                            a = self.zombies[members[i]].pos
                            b = self.zombies[members[j]].pos
                            pygame.draw.line(temp, GRAY, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 2)

                for b in self.bullets:
                    b.draw(temp)
                for z in self.zombies:
                    z.draw(temp)
                self.player.draw(temp)

                txt = self.font.render(f'Time: {int(t)}s  Zombies: {len(self.zombies)}  Groups: {len(self.groups)}', True, WHITE)
                temp.blit(txt, (10,10))
                horde_txt = self.font.render(f'Horda: {self.hordes_spawned}/{self.horde_count}', True, WHITE)
                temp.blit(horde_txt, (10, 72))
                hb_x, hb_y, hb_w, hb_h = 10, 50, 200, 16
                health_frac = max(0.0, min(1.0, self.player.health / 100.0))
                pygame.draw.rect(temp, (80,80,80), (hb_x-2, hb_y-2, hb_w+4, hb_h+4))
                pygame.draw.rect(temp, (150,0,0), (hb_x, hb_y, int(hb_w*(1-health_frac)), hb_h))
                pygame.draw.rect(temp, (0,180,0), (hb_x, hb_y, int(hb_w*health_frac), hb_h))
                health_text = self.font.render(f'Vida: {int(self.player.health)}/100', True, WHITE)
                temp.blit(health_text, (hb_x + hb_w + 8, hb_y - 2))
                txt2 = self.font.render('Mover: WASD. Atirar: mouse click. Mate todos os zumbis de cada horda.', True, WHITE)
                temp.blit(txt2, (10, 34))
                target = self.horde_count
                current = self.hordes_spawned
                remaining = max(0, target - current)
                prog_txt = self.font.render(f'Faltam {remaining} hordas para vitória', True, WHITE)
                temp.blit(prog_txt, (LARGURA - prog_txt.get_width() - 12, 10))
                bar_w = 140
                bar_h = 12
                bx = LARGURA - bar_w - 12
                by = 36
                pygame.draw.rect(temp, (60,60,60), (bx-2, by-2, bar_w+4, bar_h+4))
                fill = int(bar_w * min(1.0, current / float(target)))
                pygame.draw.rect(temp, (40,160,40), (bx, by, fill, bar_h))
                pygame.draw.rect(temp, (120,120,120), (bx+fill, by, bar_w-fill, bar_h))

                ox = oy = 0
                if self.shake_timer > 0:
                    self.shake_timer -= dt
                    import random as _r
                    ox = int((_r.random()*2-1) * self.shake_magnitude)
                    oy = int((_r.random()*2-1) * self.shake_magnitude)
                if self.flash_timer > 0:
                    self.flash_timer -= dt
                    flash = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
                    alpha = max(0, min(255, int(180 * (self.flash_timer / 0.18))))
                    flash.fill((255, 40, 40, alpha))
                    temp.blit(flash, (0,0), special_flags=pygame.BLEND_RGBA_ADD)

                self.screen.fill(BLACK)
                self.screen.blit(temp, (ox, oy))
                pygame.display.flip()
        except Exception:
            import traceback, sys
            traceback.print_exc()
            try:
                pygame.time.delay(800)
            except Exception:
                pass
            raise
        finally:
            pygame.quit()