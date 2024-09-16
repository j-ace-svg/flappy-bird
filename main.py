import pygame
from pygame.locals import *
import random
import os

pygame.mixer.pre_init(44100, -16, 2, 2048) # setup mixer to avoid sound lag
pygame.init()

clock = pygame.time.Clock()
fps = 60

screen_width = 864
screen_height = 936

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Flappy Bird')

#define font
font = pygame.font.SysFont('Bauhaus 93', 60)

#define colors
white = (255, 255, 255)

#define game variables
ground_scroll = 0
scroll_speed = 20
max_speed = 15
flying = False
game_over = False
was_flying = False
game_was_over = True
flappy_left_x = 150 # Original: 75
pipe_gap = 180
pipe_frequency = 1500 # milliseconds
start_pipe_delay = pipe_frequency - ((screen_width - flappy_left_x) / scroll_speed) / fps * 1000
next_pipe = 0
score = 0
spawn_count = 0
collide = False
start_time = 0
mouse_was_pressed = False
playtrack_index = 0

#load images
bg = pygame.image.load(os.path.join('img', 'bg.png'))
ground_img = pygame.image.load(os.path.join('img', 'ground.png'))
button_img = pygame.image.load(os.path.join('img', 'restart.png'))

#load music
playtrack = [
    {
        "song": os.path.join('music', 'Forever Bound - Stereo Madness.opus'),
        "base_rate": 1500,
        "timing": [
                [15, 2],
            ],
    },
    {
        "song": os.path.join('music', 'Oli Parker - Destination Stank Station.opus'),
        "base_rate": 60 / 115 * 4 * 1000, # 60 seconds / 114 bpm * 4 beats/measure * 1000 ms/s
        "timing": [
                #[0, 1 / 1.75],
                [1, 1],
                [11, 3],
                [20, 1]
            ],
    }
]
lobbytrack = [
    ''
]


def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


def reset_game():
    global target_group, flappy, score, spawn_count
    target_group.empty()
    flappy.rect.x = 100
    flappy.rect.y = int(screen_height / 2)
    flappy.vel = 0
    score = 0
    spawn_count = 0
    return score

class Bird(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        self.index = 0
        self.counter = 0
        for num in range(1, 4):
            img = pygame.image.load(f'img/bird{num}.png')
            self.images.append(img)
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.midleft = [x, y]
        self.vel = 0
        self.clicked = False

        self.lastClickSide = 0
        self.leftWasHeld = False
        self.rightWasHeld = False

    def update(self):

        if flying == True:
            #gravity
            if abs(self.vel) > max_speed and not game_over:
                self.vel = max_speed * abs(self.vel) / self.vel
            if self.rect.bottom < 768:
                self.rect.y += self.vel


        if game_over == False:
            #jump
            left_clicked = pygame.mouse.get_pressed()[0] == 1
            right_clicked = pygame.mouse.get_pressed()[2] == 1
            if left_clicked and not self.leftWasHeld:
                self.leftWasHeld = True
                if self.lastClickSide == 0: self.vel -= 2
                self.lastClickSide = 1
            if not left_clicked:
                self.leftWasHeld = False
                if self.lastClickSide == 1:
                    if right_clicked:
                        self.lastClickSide = 2
                    else:
                        self.lastClickSide = 0
            if right_clicked and not self.rightWasHeld:
                self.rightWasHeld = True
                if self.lastClickSide == 0: self.vel += 2
                self.lastClickSide = 2
            if not right_clicked:
                self.rightWasHeld = False
                if self.lastClickSide == 2:
                    if left_clicked:
                        self.lastClickSide = 1
                    else:
                        self.lastClickSide = 0
            match (self.lastClickSide):
                case 0:
                    if self.vel != 0:
                        self.vel -= 0.5 * abs(self.vel) / self.vel
                case 1:
                    self.vel -= 1
                case 2:
                    self.vel += 1

            #handle the animation
            self.counter += 1
            flap_cooldown = 5

            if self.counter > flap_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images):
                    self.index = 0
            self.image = self.images[self.index]

            #rotate the bird
            self.image = pygame.transform.rotate(self.images[self.index], self.vel * -2)
        #else:
        #    self.image = pygame.transform.rotate(self.images[self.index], -90)



class Target(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('img/target.png')
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.safe = False
        #position 1 is from the top, -1 is from the bottom
        #if position == 1:
        #    self.image = pygame.transform.flip(self.image, False, True)
        #    self.rect.bottomleft = [x, y - int(pipe_gap / 2)]
        #if position == -1:
        #    self.rect.topleft = [x, y + int(pipe_gap / 2)]

    def update(self):
        global flappy, game_over
        self.rect.x -= scroll_speed
        if self.safe:
            self.image.fill((150, 150, 150, 127))
        if self.rect.right < 0:
            if not self.safe:
                if not game_over: flappy.vel = -10
                game_over = True
            self.kill()


class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def draw(self, mouse_held):

        action = False

        #get mouse position
        pos = pygame.mouse.get_pos()

        #check if mouse is over the button
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1:
                action = True

        #draw button
        screen.blit(self.image, (self.rect.x, self.rect.y))

        return action and not mouse_held


bird_group = pygame.sprite.Group()
target_group = pygame.sprite.Group()

flappy = Bird(flappy_left_x, int(screen_height / 2))

bird_group.add(flappy)

#create a restart button instance
button = Button(screen_width // 2 - 50, screen_height // 2 - 100, button_img)

pygame.mixer.music.load(playtrack[0]["song"])
playtrack_timing_queue = playtrack[0]["timing"]
playtrack_timing_section_start = 0

run = True
while run:

    clock.tick(fps)

    #draw background
    screen.blit(bg, (0,0))

    bird_group.draw(screen)
    bird_group.update()
    target_group.draw(screen)

    #draw the ground
    screen.blit(ground_img, (ground_scroll, 768))

    #check missed targets
    if len(target_group) > 0:
        if bird_group.sprites()[0].rect.left > target_group.sprites()[0].rect.right:
            if collide:
                collide = False
                target_group.sprites()[0].safe = True

    draw_text(str(score), font, white, int(screen_width / 2), 20)

    #look for collision
    if pygame.sprite.groupcollide(bird_group, target_group, False, False) or flappy.rect.top < 0:
        if collide == False:
            score += 1
            collide = True
    #check if bird has hit the ground
    if flappy.rect.bottom >= 768:
        game_over = True
        flying = False

    if game_over == False and flying == True:
        # generate new pipes
        time_now = pygame.time.get_ticks()
        if time_now > next_pipe:
            print(playtrack_timing_queue)
            if len(playtrack_timing_queue) > 0 and spawn_count == playtrack_timing_queue[0][0]:
                pipe_frequency = playtrack[playtrack_index]["base_rate"] / playtrack_timing_queue[0][1]
                playtrack_timing_section_start = next_pipe
                spawn_count = 0
                playtrack_timing_queue.pop(0)
            spawn_count += 1
            pipe_height = random.randint(-100, 100)
            #btm_pipe = Target(screen_width, int(screen_height / 2) + pipe_height, -1)
            #top_pipe = Target(screen_width, int(screen_height / 2) + pipe_height, 1)
            target = Target(screen_width, int(screen_height / 2) + pipe_height)
            print(target.safe)
            target_group.add(target)
            next_pipe = playtrack_timing_section_start + spawn_count * pipe_frequency + start_pipe_delay
            print(spawn_count, time_now - start_time)


        #scroll the ground
        ground_scroll -= scroll_speed
        if abs(ground_scroll) > 35:
            ground_scroll = 0

        target_group.update()

    if game_over and not game_was_over:
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        playtrack_index = random.randint(0, len(playtrack) - 1)
        pygame.mixer.music.load(playtrack[playtrack_index]["song"])

    was_flying = flying
    game_was_over = game_over

    #check for game over and reset
    if game_over == True and game_was_over == True:
        if flying: flappy.vel += 0.5
        flappy.image = pygame.transform.rotate(flappy.images[flappy.index], pow(abs(flappy.vel + 10), 1.5) * 1 + (flappy.vel + 10) * 0.5)
        if button.draw(mouse_was_pressed):
            game_over = False
            flying = False
            score = reset_game()

    mouse_was_pressed = pygame.mouse.get_pressed()[0]

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.MOUSEBUTTONDOWN and flying == False and game_over == False:
            flying = True
            start_time = pygame.time.get_ticks()
            playtrack_timing_section_start = start_time
            next_pipe = start_time + start_pipe_delay
            flappy.vel = 0
            pipe_frequency = playtrack[playtrack_index]["base_rate"]
            print(pipe_frequency)
            playtrack_timing_queue = playtrack[playtrack_index]["timing"].copy()
            if playtrack_timing_queue[0][0] == 0:
                pipe_frequency = pipe_frequency / playtrack_timing_queue[0][1]
                playtrack_timing_queue.pop(0)
            pygame.mixer.music.play()

    pygame.display.update()

pygame.quit()
