import pygame
import math
import random
import struct

# Screen settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
SCREEN_TITLE = 'Mars Rover Driving Game'
WHITE_COLOR = (255, 255, 255)
BLACK_COLOR = (0, 0, 0)
RED_COLOR = (200, 30, 30)

class GameObject:
    def __init__(self, image_path, x, y, width, height):
        # Load and scale object image
        object_image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(object_image, (width, height))
        # Keep a copy of the original image for clean rotations
        self.original_image = self.image

        self.x_pos = x
        self.y_pos = y

        self.width = width
        self.height = height

    # Draw the object by blitting it onto the background(game_screen)
    def draw(self, background):
        background.blit(self.image, (self.x_pos, self.y_pos))

class Player(GameObject):
    # Rover movement speed
    SPEED = 8

    def __init__(self, image_path, x, y, width, height):
        super().__init__(image_path, x, y, width, height)
        self.angle = 0

    def move(self, dir_x, dir_y, max_width, max_height):
        # Move vertically and horizontally
        self.x_pos += dir_x * self.SPEED
        self.y_pos -= dir_y * self.SPEED  # dir_y > 0 means moving up

        # Rotate the sprite based on movement direction
        if dir_x > 0:
            self.angle = 270  # Facing Right
        elif dir_x < 0:
            self.angle = 90   # Facing Left
        elif dir_y > 0:
            self.angle = 0    # Facing Up
        elif dir_y < 0:
            self.angle = 180  # Facing Down

        # Apply rotation to the original scaled image
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        
        # Recalculate dimensions based on rotation to avoid collision offset glitches
        rect = self.image.get_rect(center=(self.x_pos + self.width/2, self.y_pos + self.height/2))
        self.x_pos = rect.x
        self.y_pos = rect.y

        # Keep the rover within horizontal screen bounds
        if self.x_pos < 0:
            self.x_pos = 0
        elif self.x_pos > max_width - self.width:
            self.x_pos = max_width - self.width

        # Keep the rover within vertical screen bounds
        if self.y_pos >= max_height - self.height:
            self.y_pos = max_height - self.height
        elif self.y_pos <= 0:
            self.y_pos = 0

    def detect_collision(self, other_body):
        # AABB bounding box collision check
        if self.y_pos > other_body.y_pos + other_body.height:
            return False
        if self.y_pos + self.height < other_body.y_pos:
            return False
        if self.x_pos > other_body.x_pos + other_body.width:
            return False
        if self.x_pos + self.width < other_body.x_pos:
            return False
        return True

class Enemy(GameObject):
    def __init__(self, image_path, x, y, width, height, speed, movement_type="horizontal"):
        super().__init__(image_path, x, y, width, height)
        self.speed = speed
        self.movement_type = movement_type
        self.base_y = y
        self.angle = 0.0

    def move(self, max_width):
        # Horizontal movement
        if self.x_pos <= 0:
            self.speed = abs(self.speed)
        elif self.x_pos >= max_width - self.width:
            self.speed = -abs(self.speed)
        self.x_pos += self.speed

        # If movement type is sine-wave, oscillate vertically
        if self.movement_type == "sine":
            self.angle += 0.05
            # Oscillate y_pos +/- 40 pixels around its base y coordinate
            self.y_pos = self.base_y + int(math.sin(self.angle) * 40)

class Game:
    TICK_RATE = 60

    def __init__(self, image_path, title, width, height):
        self.width = width
        self.height = height
        # create the window of specified size in which to display the game
        self.game_screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        
        # Load the background image
        background_image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(background_image, (width, height))

        # Synthesize audio effects
        pygame.mixer.init(frequency=22050, size=-16, channels=1)
        self.crash_sound = pygame.mixer.Sound(buffer=self._generate_crash_sound())
        self.win_sound = pygame.mixer.Sound(buffer=self._generate_victory_fanfare())
        self.explosion_sound = pygame.mixer.Sound(buffer=self._generate_explosion_sound())

        # Load meteor sprite
        self.meteor_img = pygame.transform.scale(pygame.image.load('Assets/meteor.png'), (50, 50))

    def _generate_crash_sound(self):
        # Generate white noise with exponential decay to simulate a crash/explosion
        sample_rate = 22050
        duration = 1.2
        num_samples = int(sample_rate * duration)
        samples = []
        for i in range(num_samples):
            val = random.randint(-32768, 32767)
            t = i / sample_rate
            decay = math.exp(-3.5 * t)
            sample = int(val * decay)
            sample = max(-32768, min(32767, sample))
            samples.append(struct.pack('<h', sample))
        return b''.join(samples)

    def _generate_victory_fanfare(self):
        # Synthesize a bright arpeggio fanfare simulating trumpet notes
        sample_rate = 22050
        notes = [523.25, 659.25, 783.99, 1046.50]  # C5, E5, G5, C6
        durations = [0.12, 0.12, 0.12, 0.6]
        samples = []
        for freq, dur in zip(notes, durations):
            num_samples = int(sample_rate * dur)
            for i in range(num_samples):
                t = i / sample_rate
                # Fundamental + harmonics to simulate a brass/trumpet timbre
                val = (math.sin(2 * math.pi * freq * t) + 
                       0.55 * math.sin(4 * math.pi * freq * t) + 
                       0.25 * math.sin(6 * math.pi * freq * t))
                sample_val = int(val / 1.8 * 32767)
                
                # Attack/decay envelope for each note
                envelope = 1.0
                if t < 0.02:
                    envelope = t / 0.02
                elif t > dur - 0.05:
                    envelope = (dur - t) / 0.05
                
                sample = int(sample_val * envelope)
                sample = max(-32768, min(32767, sample))
                samples.append(struct.pack('<h', sample))
        return b''.join(samples)

    def _generate_explosion_sound(self):
        # Generate heavy low-frequency rumble for a meteor explosion
        sample_rate = 22050
        duration = 1.8
        num_samples = int(sample_rate * duration)
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            # Sliding frequency from 100Hz down to 20Hz + heavy noise
            freq = 100 * (1.0 - t * 0.6)
            tone = math.sin(2 * math.pi * freq * t) * 0.7
            noise = random.uniform(-0.3, 0.3)
            val = tone + noise
            
            # Slow exponential decay
            decay = math.exp(-2.5 * t)
            sample = int(val * decay * 32767)
            sample = max(-32768, min(32767, sample))
            samples.append(struct.pack('<h', sample))
        return b''.join(samples)

    def run_game_loop(self, level_speed):
        is_game_over = False
        did_win = False
        dir_x = 0
        dir_y = 0
        clock = pygame.time.Clock()
        
        # Load font for messages
        font = pygame.font.SysFont(None, 75)
        hud_font = pygame.font.SysFont(None, 36)

        # Create player rover
        player = Player('Assets/rover.png', 375, 700, 50, 50)
        
        # Create destination
        dest = GameObject('Assets/destination.png', 375, 50, 50, 50)
        dest_angle = 0
        
        # Create enemies:
        enemy_0 = Enemy('Assets/hazard.png', 20, 450, 50, 50, level_speed * 3, "horizontal")
        enemy_1 = Enemy('Assets/hazard.png', 730, 300, 50, 50, level_speed * 4, "sine")
        enemy_2 = Enemy('Assets/hazard.png', 20, 180, 50, 50, level_speed * 5, "horizontal")

        # Determine level number
        level_num = int((level_speed - 1) * 2) + 1
        
        # Meteor strike parameters (Active at Level 7 and above)
        meteor_active = (level_num >= 7)
        meteor_struck = [False, False, False]
        meteor_craters = [None, None, None]
        meteor_x = [0, 0, 0]
        meteor_y = [-100, -250, -400]  # Sequenced spawn offsets
        meteor_target_x = [0, 0, 0]
        meteor_target_y = [0, 0, 0]
        meteor_speeds = [6, 8, 10]    # Variable landing rates
        
        if meteor_active:
            for i in range(3):
                # Pick target spots away from player start and destination
                meteor_target_x[i] = random.randint(100, 650)
                meteor_target_y[i] = random.randint(200, 550)
                meteor_x[i] = meteor_target_x[i]

        # Gameplay loop
        while not is_game_over:
            # gets all the events occurring at any given time
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    is_game_over = True
                    did_win = False
                # Detect key press
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        dir_y = 1
                    elif event.key == pygame.K_DOWN:
                        dir_y = -1
                    elif event.key == pygame.K_LEFT:
                        dir_x = -1
                    elif event.key == pygame.K_RIGHT:
                        dir_x = 1
                # Detect key release
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                        dir_y = 0
                    if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                        dir_x = 0
                print(event)

            # Draw background
            self.game_screen.blit(self.image, (0, 0))
            
            # Draw HUD (Level Indicator)
            level_text = hud_font.render(f"Level: {level_num}  (Speed: {level_speed:.1f})", True, BLACK_COLOR)
            self.game_screen.blit(level_text, (20, 20))
            
            # Animate the destination landing pad (rotate it slowly)
            dest_angle = (dest_angle + 2) % 360
            dest.image = pygame.transform.rotate(dest.original_image, dest_angle)
            dest_rect = dest.image.get_rect(center=(375 + 25, 50 + 25))
            self.game_screen.blit(dest.image, dest_rect.topleft)

            # Handle 3 sequenced meteors updating and drawing
            if meteor_active:
                collision_hit = False
                for i in range(3):
                    if not meteor_struck[i]:
                        # Update falling position
                        meteor_y[i] += meteor_speeds[i]
                        
                        # Draw a flashing red crosshair warning at target destination (before impact)
                        if (pygame.time.get_ticks() // 150) % 2 == 0:
                            pygame.draw.circle(self.game_screen, RED_COLOR, (meteor_target_x[i] + 25, meteor_target_y[i] + 25), 30, 3)
                            pygame.draw.line(self.game_screen, RED_COLOR, (meteor_target_x[i] - 5, meteor_target_y[i] + 25), (meteor_target_x[i] + 55, meteor_target_y[i] + 25), 2)
                            pygame.draw.line(self.game_screen, RED_COLOR, (meteor_target_x[i] + 25, meteor_target_y[i] - 5), (meteor_target_x[i] + 25, meteor_target_y[i] + 55), 2)
                        
                        # Only blit and check collision if meteor is visible on screen
                        if meteor_y[i] > -50:
                            self.game_screen.blit(self.meteor_img, (meteor_x[i], meteor_y[i]))
                            
                            # Check collision with falling meteor
                            meteor_rect = pygame.Rect(meteor_x[i], meteor_y[i], 50, 50)
                            player_rect = pygame.Rect(player.x_pos, player.y_pos, player.width, player.height)
                            if player_rect.colliderect(meteor_rect):
                                is_game_over = True
                                did_win = False
                                text = font.render('You Lose!', True, RED_COLOR)
                                self.game_screen.blit(text, (275, 350))
                                pygame.display.update()
                                self.crash_sound.play()
                                clock.tick(1)
                                collision_hit = True
                                break
                        
                        # Trigger strike and crater creation once reaching target
                        if meteor_y[i] >= meteor_target_y[i]:
                            meteor_struck[i] = True
                            self.explosion_sound.play()
                            meteor_craters[i] = GameObject('Assets/hazard.png', meteor_target_x[i], meteor_target_y[i], 50, 50)
                    
                    # Draw static crater if struck and check collision
                    if meteor_craters[i]:
                        meteor_craters[i].draw(self.game_screen)
                        if player.detect_collision(meteor_craters[i]):
                            is_game_over = True
                            did_win = False
                            text = font.render('You Lose!', True, RED_COLOR)
                            self.game_screen.blit(text, (275, 350))
                            pygame.display.update()
                            self.crash_sound.play()
                            clock.tick(1)
                            collision_hit = True
                            break
                            
                if collision_hit:
                    break

            # Move and draw the player rover
            player.move(dir_x, dir_y, self.width, self.height)
            player.draw(self.game_screen)

            # Move and draw enemy positions
            enemy_0.move(self.width)
            enemy_0.draw(self.game_screen)

            if level_speed > 1.5:
                enemy_1.move(self.width)
                enemy_1.draw(self.game_screen)
            if level_speed > 3.0:
                enemy_2.move(self.width)
                enemy_2.draw(self.game_screen)

            # Collision detection logic with standard hazards
            if player.detect_collision(enemy_0):
                is_game_over = True
                did_win = False
                text = font.render('You Lose!', True, RED_COLOR)
                self.game_screen.blit(text, (275, 350))
                pygame.display.update()
                self.crash_sound.play()
                clock.tick(1)
                break
            elif level_speed > 1.5 and player.detect_collision(enemy_1):
                is_game_over = True
                did_win = False
                text = font.render('You Lose!', True, RED_COLOR)
                self.game_screen.blit(text, (275, 350))
                pygame.display.update()
                self.crash_sound.play()
                clock.tick(1)
                break
            elif level_speed > 3.0 and player.detect_collision(enemy_2):
                is_game_over = True
                did_win = False
                text = font.render('You Lose!', True, RED_COLOR)
                self.game_screen.blit(text, (275, 350))
                pygame.display.update()
                self.crash_sound.play()
                clock.tick(1)
                break
            elif player.detect_collision(dest):
                is_game_over = True
                did_win = True
                text = font.render('You Win!', True, BLACK_COLOR)
                self.game_screen.blit(text, (275, 350))
                pygame.display.update()
                self.win_sound.play()
                clock.tick(1)
                break

            # update graphics
            pygame.display.update()
            clock.tick(self.TICK_RATE)

        # Restart loop on win, exit on loss
        if did_win:
            self.run_game_loop(level_speed + 0.5)
        else:
            return

if __name__ == '__main__':
    # Initialize pygame
    pygame.init()
    
    new_game = Game('Assets/terrain.jpg', SCREEN_TITLE, SCREEN_WIDTH, SCREEN_HEIGHT)
    # Start the game loop at level 1 speed
    new_game.run_game_loop(1)
    
    pygame.quit()
