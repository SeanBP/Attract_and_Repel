import pygame
import sys
import random
import math
import re
import pyperclip

# ---------------- Cellular Automata Core ---------------- #

def get_zero_grid(n):
    return [[0]*n for _ in range(n)]

def generate_random_grid(n, repel_percent, attract_percent):
    grid = []
    for _ in range(n):
        row = []
        for _ in range(n):
            rand = random.random() * 100
            if rand < repel_percent:
                row.append(-1)
            elif rand < repel_percent + attract_percent:
                row.append(1)
            else:
                row.append(0)
        grid.append(row)
    return grid

def get_angle_vectors(grid, x, y, mult):
    # Cardinal neighbors
    dx_card = [0, 0, -1, 1]
    dy_card = [-1, 1, 0, 0]
    vx_card = vy_card = 0
    for i in range(4):
        nx, ny = (x + dx_card[i]) % len(grid), (y + dy_card[i]) % len(grid)
        vx_card += dx_card[i] * mult * abs(grid[nx][ny])
        vy_card += dy_card[i] * mult * abs(grid[nx][ny])

    # Diagonal neighbors
    dx_diag = [-1, 1, -1, 1]
    dy_diag = [-1, -1, 1, 1]
    vx_diag = vy_diag = 0
    for i in range(4):
        nx, ny = (x + dx_diag[i]) % len(grid), (y + dy_diag[i]) % len(grid)
        vx_diag += dx_diag[i] * mult * abs(grid[nx][ny])
        vy_diag += dy_diag[i] * mult * abs(grid[nx][ny])

    if (vx_card or vy_card) and (vx_diag or vy_diag):
        angle_card = math.degrees(math.atan2(vy_card, vx_card))
        angle_diag = math.degrees(math.atan2(vy_diag, vx_diag))
        diff = (angle_card - angle_diag + 180) % 360 - 180
        if abs(diff) == 180:
            vx_card = vy_card = vx_diag = vy_diag = 0

    return (vx_card, vy_card), (vx_diag, vy_diag)

def get_neighbors_from_vector(x, y, n, vx, vy):
    if vx == 0 and vy == 0:
        return []
    angle = math.degrees(math.atan2(-vy, vx))
    angle = angle + 360 if angle < 0 else angle

    dx = [-1,0,1,-1,1,-1,0,1]
    dy = [-1,-1,-1,0,0,1,1,1]
    neighbors = []
    for i in range(8):
        nx = (x + dx[i]) % n
        ny = (y + dy[i]) % n
        ang_n = math.degrees(math.atan2(dy[i], -dx[i]))
        ang_n = ang_n + 360 if ang_n < 0 else ang_n
        if abs((ang_n - angle + 180) % 360 - 180) == 0:
            neighbors.append((ny, nx))
    return neighbors

def next_step(grid):
    n = len(grid)
    new = get_zero_grid(n)
    for x in range(n):
        for y in range(n):
            if grid[x][y] != 0:
                (vx_card, vy_card), (vx_diag, vy_diag) = get_angle_vectors(grid, x, y, grid[x][y])
                nbs_card = set(get_neighbors_from_vector(x, y, n, vx_card, vy_card))
                nbs_diag = set(get_neighbors_from_vector(x, y, n, vx_diag, vy_diag))
                all_nbs = nbs_card.union(nbs_diag)
                for ny, nx in all_nbs:
                    new[nx][ny] += grid[x][y]
    for i in range(n):
        for j in range(n):
            new[i][j] = 1 if new[i][j] > 0 else -1 if new[i][j] < 0 else 0
    return new

# ---------------- Pygame UI ---------------- #

pygame.init()
FONT = pygame.font.SysFont("arial",20)
CELL_SIZE = 20
FPS = 15

WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)
GRAY = (180,180,180)
BLUE = (0,120,255)
BG = (30,30,30)

def draw_button(screen, rect, text, active=False):
    pygame.draw.rect(screen, BLUE, rect, border_radius=8)  # always blue
    label = FONT.render(text, True, WHITE)
    screen.blit(label, label.get_rect(center=rect.center))

class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x,y,w,h)
        self.color_inactive = GRAY
        self.color_active = BLUE
        self.color = self.color_inactive
        self.text = text
        self.txt_surface = FONT.render(text, True, WHITE)
        self.active = False
    def handle_event(self,event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
                self.color = self.color_inactive
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
            self.txt_surface = FONT.render(self.text, True, WHITE)
    def draw(self, screen):
        screen.blit(self.txt_surface,(self.rect.x+5,self.rect.y+5))
        pygame.draw.rect(screen, self.color, self.rect, 2)
    def get_value(self, default, min_val=0, max_val=1000, as_float=False):
        try:
            val = float(self.text) if as_float else int(self.text)
            val = max(min_val, min(val, max_val))
            return val
        except:
            return default

# ---------------- Rules ---------------- #

RULES_TEXT = [
    "Cell States:",
    "- Empty (0): inactive",
    "- Positive (1): attracted to neighbors",
    "- Negative (-1): repeled from neighbors",
    "",
    "Step Update Rules:",
    "1. Compute Vectors:",
    "   - Around an active cell, compute two unit vectors from its neighbors:",
    "   - Cardinal: N, S, E, W neighbors weighted by absolute values",
    "   - Diagonal: NE, NW, SE, SW neighbors weighted by absolute values",
    "   - If the two vectors are exactly opposite, cancel both",
    "",
    "2. Apply Influence:",
    "   - Choose neighbors along the vector's direction",
    "   - Add the cell's value (+1 or -1) to each selected neighbor in a new grid",
    "   - Do not double-count if selected by both vectors",
    "",
    "3. Resolve New States:",
    "   - Set cell to 1 if total > 0",
    "   - Set cell to -1 if total < 0",
    "   - Set cell to 0 if total == 0"
]

def show_rules():
    screen_width, screen_height = 680, 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Rules")
    rules_font = pygame.font.SysFont("arial", 20)  # smaller font
    line_height = 25
    bottom_margin = 60
    btn_back = pygame.Rect((screen_width-100)//2, screen_height - bottom_margin + 10, 100, 30)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and btn_back.collidepoint(event.pos):
                running=False
        screen.fill(BG)
        y = 20
        for line in RULES_TEXT:
            if y + line_height < screen_height - bottom_margin:
                screen.blit(rules_font.render(line, True, WHITE), (20, y))
                y += line_height
        draw_button(screen, btn_back, "Back")
        pygame.display.flip()

# ---------------- Menu ---------------- #

def menu():
    screen = pygame.display.set_mode((400,450))
    pygame.display.set_caption("Attract and Repel - Menu")
    grid_box = InputBox(200,120,80,30,"300")
    repel_box = InputBox(200,170,80,30,"0.05")
    attract_box = InputBox(200,220,80,30,"20")
    boxes = [grid_box, repel_box, attract_box]
    start_btn = pygame.Rect(140,280,120,40)
    rules_btn = pygame.Rect(140,330,120,40)

    while True:
        screen.fill(BG)
        screen.blit(FONT.render("Attract and Repel", True, WHITE),(120,60))
        screen.blit(FONT.render("Grid Size:",True,WHITE),(80,125))
        screen.blit(FONT.render("% Attract:",True,WHITE),(80,175))
        screen.blit(FONT.render("% Repel:",True,WHITE),(80,225))
        for box in boxes: box.draw(screen)
        draw_button(screen,start_btn,"Start")
        draw_button(screen,rules_btn,"Rules")
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit();sys.exit()
            for box in boxes: box.handle_event(event)
            if event.type==pygame.MOUSEBUTTONDOWN:
                if start_btn.collidepoint(event.pos):
                    g = int(grid_box.get_value(30,1,380))
                    r = repel_box.get_value(2,0,100,as_float=True)
                    a = attract_box.get_value(50,0,100,as_float=True)
                    return g,r,a
                elif rules_btn.collidepoint(event.pos):
                    show_rules()
                    screen = pygame.display.set_mode((400,450))

# ---------------- Export ---------------- #

def export_to_conway_clipboard(grid):
    n = len(grid)
    lines = []
    for y in range(n):
        row_cells = []
        for x in range(n):
            cell = grid[y][x]
            row_cells.append("A" if cell == 1 else "B" if cell == -1 else ".")
        # compress runs
        compressed = ""
        run_char = row_cells[0]
        run_count = 1
        for ch in row_cells[1:]:
            if ch == run_char:
                run_count += 1
            else:
                compressed += f"{run_count}{run_char}" if run_count > 1 else run_char
                run_char = ch
                run_count = 1
        compressed += f"{run_count}{run_char}" if run_count > 1 else run_char
        lines.append(compressed + "$")

    pattern = "\n".join(lines) + "!"
    full_text = f"x = {n}, y = {n}, rule = Attract_and_Repel\n" + pattern
    pyperclip.copy(full_text)
    print("Full grid copied to clipboard!")


def import_from_clipboard():
    text = pyperclip.paste().strip()
    if not text.startswith("x ="):
        print("Invalid pattern format")
        return None

    try:
        header, pattern = text.split("\n", 1)
    except ValueError:
        print("Invalid pattern format")
        return None

    match = re.search(r"x\s*=\s*(\d+)\s*,\s*y\s*=\s*(\d+)", header)
    if not match:
        print("Header parse failed")
        return None
    x = int(match.group(1))
    y = int(match.group(2))
    size = max(x, y)
    grid = [[0] * size for _ in range(size)]

    lines = pattern.replace("!", "").split("$")
    for row_idx, line in enumerate(lines):
        if row_idx >= y or not line:
            continue
        col = 0
        i = 0
        while i < len(line) and col < x:
            if line[i].isdigit():
                num = ""
                while i < len(line) and line[i].isdigit():
                    num += line[i]
                    i += 1
                if i < len(line):
                    ch = line[i]
                    count = int(num)
                    val = 1 if ch == "A" else -1 if ch == "B" else 0
                    for _ in range(count):
                        if col < x:
                            grid[row_idx][col] = val
                            col += 1
            else:
                ch = line[i]
                val = 1 if ch == "A" else -1 if ch == "B" else 0
                grid[row_idx][col] = val
                col += 1
            i += 1

    print("Grid imported from clipboard")
    return grid


# ---------------- Import ---------------- #

def import_from_clipboard():
    text = pyperclip.paste().strip()
    if not text.startswith("x ="):
        print("Invalid pattern format")
        return None

    try:
        header, pattern = text.split("\n", 1)
    except ValueError:
        print("Invalid pattern format")
        return None

    match = re.search(r"x\s*=\s*(\d+)\s*,\s*y\s*=\s*(\d+)", header)
    if not match:
        print("Header parse failed")
        return None
    x = int(match.group(1))
    y = int(match.group(2))

    size = max(x, y)
    grid = [[0] * size for _ in range(size)]


    lines = pattern.replace("!", "").split("$")
    for row_idx, line in enumerate(lines):
        if row_idx >= y:
            break
        if line == "":
            # empty row
            continue
        col = 0
        i = 0
        while i < len(line) and col < x:
            if line[i].isdigit():
                num = ""
                while i < len(line) and line[i].isdigit():
                    num += line[i]
                    i += 1
                if i < len(line):
                    cell_char = line[i]
                    count = int(num)
                    val = 1 if cell_char == "A" else -1 if cell_char == "B" else 0
                    for _ in range(count):
                        if col < x:
                            grid[row_idx][col] = val
                            col += 1
            else:
                ch = line[i]
                val = 1 if ch == "A" else -1 if ch == "B" else 0
                grid[row_idx][col] = val
                col += 1
            i += 1
    print("Grid imported from clipboard")
    return grid

# ---------------- Simulation ---------------- #

def run_simulation():
    FIXED_WIDTH, FIXED_HEIGHT = 760, 760  # grid area
    BUTTON_HEIGHT = 60

    while True:
        size, r, a = menu()

        # compute exact float cell size to fill the grid area
        CELL_SIZE = FIXED_WIDTH / size
        grid_display_size = CELL_SIZE * size
        screen = pygame.display.set_mode((FIXED_WIDTH, FIXED_HEIGHT + BUTTON_HEIGHT))
        pygame.display.set_caption("Attract and Repel")
        grid = generate_random_grid(size, r, a)
        paused = True
        clock = pygame.time.Clock()

        # buttons
        BUTTON_HEIGHT = 60
        BTN_H = 30  # actual button height

        btn_y = FIXED_HEIGHT + (BUTTON_HEIGHT - BTN_H) // 2

        btn_play = pygame.Rect(20, btn_y, 80, BTN_H)
        btn_step = pygame.Rect(120, btn_y, 80, BTN_H)
        btn_restart = pygame.Rect(220, btn_y, 100, BTN_H)
        btn_menu = pygame.Rect(340, btn_y, 100, BTN_H)
        btn_export = pygame.Rect(460, btn_y, 100, BTN_H)
        btn_import = pygame.Rect(580, btn_y, 100, BTN_H)


        def draw_grid(screen, grid):
            n = len(grid)
            for y in range(n):
                for x in range(n):
                    val = grid[y][x]
                    color = BLACK if val == 0 else WHITE if val == 1 else RED
                    rect_size = max(int(CELL_SIZE), 1)
                    pygame.draw.rect(screen, color,
                                     (int(x * CELL_SIZE), int(y * CELL_SIZE), rect_size, rect_size))

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    # grid click
                    if my < FIXED_HEIGHT and paused:
                        cx, cy = int(mx / CELL_SIZE), int(my / CELL_SIZE)
                        if 0 <= cx < size and 0 <= cy < size:
                            grid[cy][cx] = {0: 1, 1: -1, -1: 0}[grid[cy][cx]]

                    # buttons
                    elif btn_play.collidepoint(event.pos):
                        paused = not paused
                    elif btn_step.collidepoint(event.pos) and paused:
                        grid = next_step(grid)
                    elif btn_restart.collidepoint(event.pos):
                        grid = generate_random_grid(size, r, a)
                    elif btn_menu.collidepoint(event.pos):
                        running = False
                    elif btn_export.collidepoint(event.pos) and paused:
                        export_to_conway_clipboard(grid)
                    elif btn_import.collidepoint(event.pos) and paused:
                        imported = import_from_clipboard()
                        if imported:
                            grid = imported
                            size = len(grid)
                            CELL_SIZE = FIXED_WIDTH / size

            if not paused:
                grid = next_step(grid)

            screen.fill(BG)
            draw_grid(screen, grid)
            draw_button(screen, btn_play, "Pause" if not paused else "Play", active=True)
            draw_button(screen, btn_step, "Step")
            draw_button(screen, btn_restart, "Restart")
            draw_button(screen, btn_menu, "Menu")
            draw_button(screen, btn_export, "Export")
            draw_button(screen, btn_import, "Import", active=True)
            pygame.display.flip()
            clock.tick(FPS)


if __name__=="__main__":
    run_simulation()