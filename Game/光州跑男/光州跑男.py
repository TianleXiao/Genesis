import pygame
import random
import sys
import time
import math
import json
import os

# 常量
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
GROUND_HEIGHT = 580
PLAYER_SPEED = 0  # 玩家不能自动前进
RUNNER_BASE_SPEED = 2
FPS = 60
JUMP_VELOCITY = -15
GRAVITY = 0.8

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (230, 30, 30)
BLUE = (0, 150, 255)
GREEN = (0, 200, 0)
YELLOW = (255, 255, 0)
BACKGROUND = (240, 245, 255)
ORANGE = (255, 160, 60)
SKIN = (255, 220, 180)
GRAY = (230, 230, 230)
DARK_GREEN = (0, 150, 0)
BROWN = (139, 69, 19)
LIGHT_BLUE = (173, 216, 230)
PURPLE = (128, 0, 128)

class GameState:
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3
    VICTORY = 4

class Player:
    def __init__(self):
        self.x = 100
        self.y = GROUND_HEIGHT - 100
        self.width = 60
        self.height = 100
        self.speed = PLAYER_SPEED
        self.jumping = False
        self.jump_velocity = 0
        self.run_animation = 0
        self.direction = 1

    def draw(self, screen):
        # 身体
        pygame.draw.rect(screen, BLUE, (self.x, self.y, self.width, self.height))
        
        # 头部
        pygame.draw.circle(screen, SKIN, (self.x + self.width // 2, self.y - 20), 20)
        
        # 眼睛
        pygame.draw.circle(screen, BLACK, (self.x + self.width // 2 - 7, self.y - 25), 3)
        pygame.draw.circle(screen, BLACK, (self.x + self.width // 2 + 7, self.y - 25), 3)
        
        # 嘴巴
        pygame.draw.arc(screen, BLACK, (self.x + self.width // 2 - 10, self.y - 15, 20, 15), 0, math.pi, 2)
        
        # 手臂
        hand_offset = 10 * math.sin(self.run_animation)
        self.draw_limb(screen, (self.x + 5, self.y + 30), (self.x - 10, self.y + 40 + hand_offset), SKIN, 4)
        self.draw_limb(screen, (self.x + self.width - 5, self.y + 30), (self.x + self.width + 10, self.y + 40 - hand_offset), SKIN, 4)
        
        # 腿部
        leg_offset = 15 * math.sin(self.run_animation)
        self.draw_limb(screen, (self.x + 15, self.y + self.height), (self.x + 15, self.y + self.height + 30 + leg_offset), BLACK, 4)
        self.draw_limb(screen, (self.x + 45, self.y + self.height), (self.x + 45, self.y + self.height + 30 - leg_offset), BLACK, 4)

    def draw_limb(self, screen, start_pos, end_pos, color, thickness):
        pygame.draw.line(screen, color, start_pos, end_pos, thickness)

    def update(self, delta_time):
        self.run_animation += 0.3
        
        # 玩家不能自动前进，只能通过打字前进
        
        # 限制玩家在屏幕内
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        
        # 跳跃物理
        if self.jumping:
            self.y += self.jump_velocity
            self.jump_velocity += GRAVITY
            if self.y >= GROUND_HEIGHT - 100:
                self.y = GROUND_HEIGHT - 100
                self.jumping = False

    def jump(self):
        if not self.jumping:
            self.jumping = True
            self.jump_velocity = JUMP_VELOCITY

class Runner:
    def __init__(self):
        self.x = 700
        self.y = GROUND_HEIGHT - 90
        self.width = 50
        self.height = 90
        self.color = ORANGE
        self.speed = RUNNER_BASE_SPEED
        self.run_animation = 0
        self.direction = 1  # 向右跑

    def draw(self, screen):
        # 如果跑者在屏幕内才绘制
        if -self.width <= self.x <= SCREEN_WIDTH:
            # 身体
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
            
            # 头部
            pygame.draw.circle(screen, SKIN, (self.x + self.width // 2, self.y - 15), 18)
            
            # 眼睛
            pygame.draw.circle(screen, BLACK, (self.x + self.width // 2 - 5, self.y - 20), 3)
            pygame.draw.circle(screen, BLACK, (self.x + self.width // 2 + 5, self.y - 20), 3)
            
            # 嘴巴
            pygame.draw.arc(screen, BLACK, (self.x + self.width // 2 - 8, self.y - 10, 16, 12), 0, math.pi, 2)
            
            # 腿部
            leg_offset = 12 * math.sin(self.run_animation + 1.5)
            self.draw_limb(screen, (self.x + 10, self.y + self.height), (self.x + 10, self.y + self.height + 25 + leg_offset), BLACK, 3)
            self.draw_limb(screen, (self.x + 40, self.y + self.height), (self.x + 40, self.y + self.height + 25 - leg_offset), BLACK, 3)

    def draw_limb(self, screen, start_pos, end_pos, color, thickness):
        pygame.draw.line(screen, color, start_pos, end_pos, thickness)

    def update(self, level):
        self.run_animation += 0.4
        self.speed = RUNNER_BASE_SPEED + math.log(max(1, level)) * 0.3
        
        # 只向右跑，可以跑出画面
        self.x += self.speed

class Obstacle:
    def __init__(self, x, width, height):
        self.x = x
        self.y = GROUND_HEIGHT - height
        self.width = width
        self.height = height
        self.color = BROWN
        
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        
    def update(self, speed):
        self.x -= speed
        
    def is_off_screen(self):
        return self.x + self.width < 0

class Game:
    def __init__(self):
        # 初始化Pygame和字体模块
        pygame.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("光州跑男 Gwangju Runner - 打字追逐")
        self.clock = pygame.time.Clock()

        # 使用默认字体
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        self.player = Player()
        self.runner = Runner()
        self.obstacles = []
        self.obstacle_timer = 0

        self.words = {
            "easy": ["quick", "chase", "speed", "race", "word", "type", "fast", "run", "jump", "dash"],
            "medium": ["escape", "catch", "pursuit", "sprint", "hurry", "track", "hunt", "follow", "overtake"],
            "hard": ["acceleration", "velocity", "momentum", "persistence", "determination", "endurance"]
        }
        self.current_word = ""
        self.user_input = ""
        self.score = 0
        self.level = 1
        self.state = GameState.PLAYING
        self.start_time = 0
        self.word_time_limit = 10
        self.high_scores = self.load_high_scores()
        self.select_word()

        # 背景元素
        self.clouds = [(random.randint(0, SCREEN_WIDTH), random.randint(50, 200), random.randint(30, 70)) for _ in range(5)]
        self.trees = [(random.randint(0, SCREEN_WIDTH), random.randint(30, 80)) for _ in range(3)]

    def load_high_scores(self):
        try:
            with open("high_scores.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return [0, 0, 0, 0, 0]

    def save_high_score(self):
        self.high_scores.append(self.score)
        self.high_scores = sorted(self.high_scores, reverse=True)[:5]
        try:
            with open("high_scores.json", "w") as f:
                json.dump(self.high_scores, f)
        except:
            pass

    def select_word(self):
        difficulty = "easy" if self.level < 5 else "medium" if self.level < 10 else "hard"
        self.current_word = random.choice(self.words[difficulty])
        self.user_input = ""
        self.start_time = time.time()
        self.word_time_limit = max(5, 15 - (self.level - 1) * 1)

    def get_distance(self):
        """计算玩家和跑者的距离"""
        return max(0, self.runner.x - self.player.x)

    def draw_background(self):
        # 天空
        self.screen.fill(LIGHT_BLUE)
        
        # 云朵
        for cloud in self.clouds:
            pygame.draw.circle(self.screen, WHITE, (cloud[0], cloud[1]), cloud[2])
            pygame.draw.circle(self.screen, WHITE, (cloud[0] + cloud[2]//2, cloud[1] - cloud[2]//3), cloud[2]//1.5)
            pygame.draw.circle(self.screen, WHITE, (cloud[0] + cloud[2], cloud[1]), cloud[2])
        
        # 地面
        pygame.draw.rect(self.screen, DARK_GREEN, (0, GROUND_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_HEIGHT))
        
        # 树
        for tree in self.trees:
            pygame.draw.rect(self.screen, BROWN, (tree[0], GROUND_HEIGHT - tree[1], 20, tree[1]))
            pygame.draw.circle(self.screen, GREEN, (tree[0] + 10, GROUND_HEIGHT - tree[1] - 20), 30)

    def draw_ui(self):
        # 分数和等级
        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        level_text = self.font.render(f"Level: {self.level}", True, BLACK)
        self.screen.blit(score_text, (20, 20))
        self.screen.blit(level_text, (20, 60))

        # 距离显示
        distance = self.get_distance()
        distance_text = self.font.render(f"Distance: {int(distance)}", True, PURPLE)
        self.screen.blit(distance_text, (SCREEN_WIDTH - 250, 20))

        # 输入框背景
        pygame.draw.rect(self.screen, GRAY, (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100))
        
        # 单词和输入
        word_text = self.font.render(f"Type: {self.current_word}", True, BLUE)
        input_text = self.font.render(f"Input: {self.user_input}", True, RED)
        self.screen.blit(word_text, (50, SCREEN_HEIGHT - 90))
        self.screen.blit(input_text, (50, SCREEN_HEIGHT - 50))

        # 时间进度条
        elapsed = time.time() - self.start_time
        time_left = max(0, self.word_time_limit - elapsed)
        progress_width = (time_left / self.word_time_limit) * 300
        pygame.draw.rect(self.screen, RED, (SCREEN_WIDTH - 350, SCREEN_HEIGHT - 50, 300, 15))
        pygame.draw.rect(self.screen, GREEN, (SCREEN_WIDTH - 350, SCREEN_HEIGHT - 50, progress_width, 15))

        # 等级进度条
        level_progress = min(1.0, self.score / (self.level * 100))
        pygame.draw.rect(self.screen, RED, (20, 100, 200, 10))
        pygame.draw.rect(self.screen, GREEN, (20, 100, 200 * level_progress, 10))
        
        # 操作提示
        controls_text = self.small_font.render("Type words correctly to chase! Space to jump, F1 to pause", True, BLACK)
        self.screen.blit(controls_text, (SCREEN_WIDTH // 2 - controls_text.get_width() // 2, SCREEN_HEIGHT - 120))

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.state == GameState.PLAYING:
                if event.key == pygame.K_RETURN:
                    if self.user_input == self.current_word:
                        # 正确输入奖励 - 玩家前进，跑者后退
                        self.player.x += 1000  # 玩家前进
                        self.runner.x -= 300  # 跑者后退
                        self.score += 10 * self.level
                        if self.score >= self.level * 100:
                            self.level += 1
                        self.select_word()
                    else:
                        # 错误输入惩罚 - 跑者前进
                        self.user_input = ""
                        self.runner.x += 20  # 跑者前进
                elif event.key == pygame.K_BACKSPACE:
                    self.user_input = self.user_input[:-1]
                elif event.key == pygame.K_SPACE:
                    self.player.jump()
                elif event.key == pygame.K_F1:
                    self.state = GameState.PAUSED
                else:
                    if len(self.user_input) < 20 and event.unicode.isprintable():
                        self.user_input += event.unicode
            elif self.state == GameState.PAUSED:
                if event.key == pygame.K_F1:
                    self.state = GameState.PLAYING
            elif self.state in (GameState.GAME_OVER, GameState.VICTORY):
                if event.key == pygame.K_r:
                    self.__init__()
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

    def update(self):
        if self.state == GameState.PLAYING:
            self.player.update(1)
            self.runner.update(self.level)
            
            # 更新障碍物
            for obstacle in self.obstacles[:]:
                obstacle.update(self.level * 2)
                if obstacle.is_off_screen():
                    self.obstacles.remove(obstacle)
            
            # 生成新障碍物
            self.obstacle_timer += 1
            if self.obstacle_timer > 180:
                if random.random() < 0.3 and self.level >= 3:
                    self.obstacles.append(Obstacle(SCREEN_WIDTH, 30, random.randint(20, 50)))
                self.obstacle_timer = 0
            
            # 检查单词时间限制
            if time.time() - self.start_time > self.word_time_limit:
                self.select_word()
            
            # 碰撞检测
            player_rect = pygame.Rect(self.player.x, self.player.y, self.player.width, self.player.height)
            runner_rect = pygame.Rect(self.runner.x, self.runner.y, self.runner.width, self.runner.height)
            
            # 检查与障碍物的碰撞
            for obstacle in self.obstacles:
                obstacle_rect = pygame.Rect(obstacle.x, obstacle.y, obstacle.width, obstacle.height)
                if player_rect.colliderect(obstacle_rect):
                    self.player.x -= 20
                    self.score = max(0, self.score - 5)
                    self.obstacles.remove(obstacle)
            
            # 检查与跑者的碰撞
            if player_rect.colliderect(runner_rect):
                self.state = GameState.VICTORY
                self.save_high_score()
            elif self.runner.x > SCREEN_WIDTH + 5000:  # 跑者跑出画面一定距离
                self.state = GameState.GAME_OVER
                self.save_high_score()

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        if self.state == GameState.VICTORY:
            text = self.font.render("VICTORY! You caught the runner!", True, YELLOW)
        else:
            text = self.font.render("GAME OVER! The runner escaped!", True, RED)
            
        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        restart_text = self.font.render("Press R to Restart or Q to Quit", True, WHITE)
        
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2 - 30))
        self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

        high_score_text = self.font.render("High Scores:", True, WHITE)
        self.screen.blit(high_score_text, (SCREEN_WIDTH // 2 - high_score_text.get_width() // 2, SCREEN_HEIGHT // 2 + 70))
        
        for i, score in enumerate(self.high_scores):
            score_text = self.small_font.render(f"{i+1}. {score}", True, WHITE)
            self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2 + 100 + i * 30))

    def draw_pause(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        text = self.font.render("PAUSED", True, WHITE)
        resume_text = self.font.render("Press F1 to Resume", True, WHITE)
        
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(resume_text, (SCREEN_WIDTH // 2 - resume_text.get_width() // 2, SCREEN_HEIGHT // 2 + 10))

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.handle_input(event)

            self.update()
            self.draw_background()
            
            # 绘制障碍物
            for obstacle in self.obstacles:
                obstacle.draw(self.screen)
                
            self.player.draw(self.screen)
            self.runner.draw(self.screen)
            self.draw_ui()
            
            if self.state in (GameState.GAME_OVER, GameState.VICTORY):
                self.draw_game_over()
            elif self.state == GameState.PAUSED:
                self.draw_pause()

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()