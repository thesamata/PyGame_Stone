import pygame
import json
import os
import random
from pygame.locals import *

# Pygame Başlatma
pygame.init()

# Saat ve FPS Ayarı
clock = pygame.time.Clock()
FPS = 60

# Oyun Ekranı Ayarları
bottomPanel = 150
screenWidth = 800
screenHeight = 400 + bottomPanel

screen = pygame.display.set_mode((screenWidth, screenHeight))
pygame.display.set_caption('İlde Stone Game')

# Fontlar
try:
    font = pygame.font.SysFont('Minecraft', 30)
except:
    font = pygame.font.SysFont('Arial', 24)

# Renkler
goldColor = (255, 215, 0)
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)
green = (0, 255, 0)

# Veri Yükleme
def load_data():
    default_data = {"Gold": 50, "Food": 10}
    path = os.path.join("character", "player_data.txt")
    if not os.path.exists("character"):
        os.makedirs("character")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            return default_data
    return default_data

C_Dictionary = load_data()
Gold = C_Dictionary["Gold"]
Food = C_Dictionary["Food"]

# Görsel Yükleme
def load_image(path, scale=None):
    if not os.path.exists(path):
        # Eğer dosya yoksa boş bir yüzey oluştur ki oyun çökmesin
        surf = pygame.Surface((50, 50))
        surf.fill((255, 0, 255))
        return surf
    img = pygame.image.load(path).convert_alpha()
    if scale:
        img = pygame.transform.scale(img, scale)
    return img

bgImage = load_image('img/Background/background.png')
startImage = load_image('img/Background/start.jpg')
panelImage = load_image('img/Icons/panel.png')
hearth_img = load_image('img/Icons/hearth.png')
meatImage = load_image('img/Icons/Meat.png', (40, 40))
coinImage = load_image('img/Icons/coin.png', (40, 40))

# Sesler ve Müzik
pygame.mixer.init()
try:
    PetEatSong = pygame.mixer.Sound('sound/petEat.mp3')
    PetLoveSong = pygame.mixer.Sound('sound/petLove.mp3')
    PetSleepSong = pygame.mixer.Sound('sound/petSleep.mp3')
    pygame.mixer.music.load('sound/gameLoop.mp3')
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1) # Döngü şeklinde çal
except Exception as e:
    print(f"Ses yükleme hatası: {e}")
    PetEatSong = PetLoveSong = PetSleepSong = None

# --- SINIFLAR ---

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(4, 8)
        self.vel_x = random.uniform(-3, 3)
        self.vel_y = random.uniform(-6, -2)
        self.lifetime = 255

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.lifetime -= 8
        if self.size > 0.2: self.size -= 0.1

    def draw(self, screen):
        if self.lifetime > 0:
            surf = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, self.lifetime), (int(self.size), int(self.size)), int(self.size))
            screen.blit(surf, (int(self.x), int(self.y)))

class Button():
    def __init__(self, x, y, text, width=150, height=60):
        self.rect = Rect(x, y, width, height)
        self.text = text
        self.color = (183, 73, 73)

    def draw(self, screen, mouse_pos, is_clicked):
        action = False
        draw_color = self.color
        
        if self.rect.collidepoint(mouse_pos):
            draw_color = (225, 30, 56)
            if is_clicked:
                action = True
                draw_color = (255, 0, 0)

        pygame.draw.rect(screen, draw_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, white, self.rect, 2, border_radius=10)
        
        text_img = font.render(self.text, True, white)
        text_rect = text_img.get_rect(center=self.rect.center)
        screen.blit(text_img, text_rect)
        return action

class GamePet():
    def __init__(self, x, y, name, stats):
        self.name = name
        self.hp = self.max_hp = stats[0]
        self.love = self.max_love = stats[1]
        self.hungry = self.max_hungry = stats[2]
        self.sleep = self.max_sleep = stats[3]
        
        self.animation_list = []
        self.frame_index = 0
        self.action = 0 # 0:idle, 1:love, 2:eat, 3:sleep
        self.update_time = pygame.time.get_ticks()
        self.is_alive = True
        
        actions = ['Idle', 'Love', 'Eat', 'Sleep']
        for act in actions:
            temp_list = []
            for i in range(8):
                path = f'img/{self.name}/{act}/{i}.png'
                img = load_image(path)
                img = pygame.transform.scale(img, (img.get_width() * 4, img.get_height() * 4))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        if self.hp <= 0:
            self.is_alive = False
            return

        cooldown = 150
        if pygame.time.get_ticks() - self.update_time > cooldown:
            self.update_time = pygame.time.get_ticks()
            self.frame_index = (self.frame_index + 1) % len(self.animation_list[self.action])
            if self.frame_index == 0 and self.action != 0:
                self.action = 0 # Idle'a dön
        
        self.image = self.animation_list[self.action][self.frame_index]

    def draw(self, screen):
        if self.is_alive:
            screen.blit(self.image, self.rect)
        else:
            txt = font.render(f"{self.name} Melek Oldu...", True, red)
            screen.blit(txt, (screenWidth//2 - 120, screenHeight//2 - 20))

class Bar():
    def __init__(self, x, y, title, color):
        self.x, self.y, self.title, self.color = x, y, title, color

    def draw(self, screen, value, max_value):
        ratio = max(0, min(value / max_value, 1))
        pygame.draw.rect(screen, (40, 40, 40), (self.x-2, self.y-2, 154, 24), border_radius=6)
        pygame.draw.rect(screen, (80, 0, 0), (self.x, self.y, 150, 20), border_radius=5)
        if ratio > 0:
            pygame.draw.rect(screen, self.color, (self.x, self.y, 150 * ratio, 20), border_radius=5)
        txt = font.render(self.title, True, white)
        screen.blit(txt, (self.x, self.y - 25))

# --- OYUN DÖNGÜSÜ ---

def save_game():
    with open(os.path.join("character", "player_data.txt"), "w") as f:
        json.dump({"Gold": Gold, "Food": Food}, f)

# --- OYUN BAŞLATMA ---
pet = GamePet(400, 320, "Kaya", [15, 10, 10, 10])
# Barların yerleşimi (Biraz daha aşağı ve sola hizalı)
hp_bar = Bar(25, 120, "Can", red)
love_bar = Bar(25, 170, "Sevgi", (255, 105, 180))
hungry_bar = Bar(25, 220, "Açlık", (255, 165, 0))
sleep_bar = Bar(25, 270, "Uyku", (100, 149, 237))

# Butonların dikey hizalamasını düzelttik
btn_y = 445
buttons = [
    Button(35, btn_y, 'Uyku'),
    Button(195, btn_y, 'Besle'),
    Button(355, btn_y, 'Market'),
    Button(580, btn_y + 5, 'Kaydet', width=110, height=50) # +5 ile dikey ortalandı
]
buttons[3].color = (60, 63, 65) # Daha şık bir koyu gri

particles = []
game_state = "START"
run = True

while run:
    clock.tick(FPS)
    mouse_pos = pygame.mouse.get_pos()
    is_clicked = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            is_clicked = True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            if game_state == "START" or not pet.is_alive:
                pet = GamePet(400, 320, "Kaya", [15, 10, 10, 10])
                game_state = "PLAY"

    if game_state == "START":
        screen.blit(startImage, (0, 0))
        overlay = pygame.Surface((screenWidth, screenHeight), pygame.SRCALPHA)
        overlay.fill((0,0,0,160))
        screen.blit(overlay, (0,0))
        txt = font.render("Baslatmak icin 'R' tusuna basin", True, white)
        screen.blit(txt, (screenWidth//2 - 180, screenHeight//2))
    
    elif game_state == "PLAY":
        screen.blit(bgImage, (0, 0))
        screen.blit(panelImage, (0, screenHeight - bottomPanel))

        if pet.is_alive:
            # Mantık
            pet.love -= 0.002
            pet.hungry -= 0.004
            pet.sleep -= 0.003
            if pet.hungry < 2 or pet.sleep < 2: pet.hp -= 0.01
            
            pet.love = max(0, min(pet.love, pet.max_love))
            pet.hungry = max(0, min(pet.hungry, pet.max_hungry))
            pet.sleep = max(0, min(pet.sleep, pet.max_sleep))
            pet.hp = max(0, min(pet.hp, pet.max_hp))

            # Barlar
            hp_bar.draw(screen, pet.hp, pet.max_hp)
            love_bar.draw(screen, pet.love, pet.max_love)
            hungry_bar.draw(screen, pet.hungry, pet.max_hungry)
            sleep_bar.draw(screen, pet.sleep, pet.max_sleep)

            # Buton İşlemleri
            if buttons[0].draw(screen, mouse_pos, is_clicked): # Uyku
                pet.sleep = pet.max_sleep
                pet.action = 3
                if PetSleepSong: PetSleepSong.play()
                for _ in range(10): particles.append(Particle(400, 320, (100, 149, 237)))

            if buttons[1].draw(screen, mouse_pos, is_clicked): # Besle
                if Food > 0:
                    Food -= 1
                    pet.hungry = min(pet.hungry + 3, pet.max_hungry)
                    pet.hp = min(pet.hp + 2, pet.max_hp)
                    pet.action = 2
                    if PetEatSong: PetEatSong.play()
                    for _ in range(15): particles.append(Particle(400, 320, (255, 165, 0)))
                    save_game()

            if buttons[2].draw(screen, mouse_pos, is_clicked): # Market
                if Gold >= 10:
                    Gold -= 10
                    Food += 5
                    save_game()
                    for _ in range(20): particles.append(Particle(mouse_pos[0], mouse_pos[1], goldColor))

            if buttons[3].draw(screen, mouse_pos, is_clicked): # Kaydet
                save_game()

            # Sevgi Sistemi
            if pet.rect.collidepoint(mouse_pos):
                pygame.mouse.set_visible(False)
                screen.blit(hearth_img, (mouse_pos[0]-15, mouse_pos[1]-15))
                if is_clicked:
                    Gold += 1
                    pet.love = min(pet.love + 1, pet.max_love)
                    pet.action = 1
                    if PetLoveSong: PetLoveSong.play()
                    particles.append(Particle(mouse_pos[0], mouse_pos[1], (255, 105, 180)))
                    save_game()
            else:
                pygame.mouse.set_visible(True)
        else:
            overlay = pygame.Surface((screenWidth, screenHeight), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            over_txt = font.render("OYUN BITTI! Yeniden baslatmak icin 'R' basin", True, white)
            screen.blit(over_txt, (screenWidth//2 - 250, screenHeight//2))

        # Partiküller
        for p in particles[:]:
            p.update()
            p.draw(screen)
            if p.lifetime <= 0: particles.remove(p)

        pet.update()
        pet.draw(screen)
        
        # Üst Bilgi (İkonları barlarla aynı hizaya (Y: 120 ve 170) taşıdık)
        info_x = screenWidth - 110
        screen.blit(coinImage, (info_x, 115)) # Can barı hizası (120 - biraz ofset)
        screen.blit(font.render(str(Gold), True, goldColor), (info_x + 50, 120))
        screen.blit(meatImage, (info_x, 165)) # Sevgi barı hizası (170 - biraz ofset)
        screen.blit(font.render(str(Food), True, white), (info_x + 50, 170))

    pygame.display.flip()

pygame.quit()
