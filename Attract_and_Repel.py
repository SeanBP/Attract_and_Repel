import pygame
import sys
import random
import math

# ---------------- Cellular Automata Core ---------------- #

def get_zero_grid(n):
    return [[0]*n for _ in range(n)]

def generate_random_grid(n, repel_percent, attract_percent):
    grid = []
    for _ in range(n):
        row = []
        for _ in range(n):
            rand = random.randint(1, 100)
            if rand <= repel_percent:              # repel (red)
                row.append(-1)
            elif rand <= repel_percent + attract_percent:  # attract (black)
                row.append(1)
            else:
                row.append(0)
        grid.append(row)
    return grid

def get_angle(grid, x, y, mult):
    dx = [-1,0,1,-1,1,-1,0,1]
    dy = [-1,-1,-1,0,0,1,1,1]
    vx = vy = 0
    for i in range(8):
        nx = (x+dx[i])%len(grid)
        ny = (y+dy[i])%len(grid)
        vx += dx[i]*mult*abs(grid[nx][ny])
        vy += dy[i]*mult*abs(grid[nx][ny])
    if vx==0 and vy==0:
        return None
    ang = math.degrees(math.atan2(-vy, vx))
    return ang+360 if ang<0 else ang

def get_neighbors_at_angle(x, y, size, angle):
    dx = [-1,0,1,-1,1,-1,0,1]
    dy = [-1,-1,-1,0,0,1,1,1]
    nbs=[]
    for i in range(8):
        nx=(x+dx[i])%size
        ny=(y+dy[i])%size
        ang_n=math.degrees(math.atan2(dy[i],-dx[i]))
        ang_n=ang_n+360 if ang_n<0 else ang_n
        if abs((ang_n-angle+180)%360-180)<45:
            nbs.append((ny,nx))
    return nbs

def next_step(grid):
    n=len(grid)
    new=get_zero_grid(n)
    for x in range(n):
        for y in range(n):
            if grid[x][y]!=0:
                ang=get_angle(grid,x,y,grid[x][y])
                if ang is not None:
                    nbs=get_neighbors_at_angle(x,y,n,ang)
                    for ny,nx in nbs:
                        new[nx][ny]+=grid[x][y]
    for i in range(n):
        for j in range(n):
            new[i][j]=1 if new[i][j]>0 else -1 if new[i][j]<0 else 0
    return new

# ---------------- Pygame UI ---------------- #

pygame.init()
FONT=pygame.font.SysFont("arial",20)
CELL_SIZE=20
FPS=15

WHITE=(255,255,255)
BLACK=(0,0,0)
RED=(255,0,0)
GRAY=(180,180,180)
BLUE=(0,120,255)
BG=(30,30,30)

def draw_button(screen,rect,text,active=False):
    pygame.draw.rect(screen,BLUE if active else GRAY,rect,border_radius=8)
    label=FONT.render(text,True,WHITE)
    screen.blit(label,label.get_rect(center=rect.center))

def draw_grid(screen,grid):
    n=len(grid)
    for y in range(n):
        for x in range(n):
            val=grid[y][x]
            color=WHITE if val==0 else BLACK if val==1 else RED
            pygame.draw.rect(screen,color,(x*CELL_SIZE,y*CELL_SIZE,CELL_SIZE-1,CELL_SIZE-1))

class InputBox:
    def __init__(self,x,y,w,h,text=''):
        self.rect=pygame.Rect(x,y,w,h)
        self.color_inactive=GRAY
        self.color_active=BLUE
        self.color=self.color_inactive
        self.text=text
        self.txt_surface=FONT.render(text,True,WHITE)
        self.active=False
    def handle_event(self,event):
        if event.type==pygame.MOUSEBUTTONDOWN:
            self.active=self.rect.collidepoint(event.pos)
            self.color=self.color_active if self.active else self.color_inactive
        if event.type==pygame.KEYDOWN and self.active:
            if event.key==pygame.K_RETURN:
                self.active=False
                self.color=self.color_inactive
            elif event.key==pygame.K_BACKSPACE:
                self.text=self.text[:-1]
            elif event.unicode.isdigit():
                self.text+=event.unicode
            self.txt_surface=FONT.render(self.text,True,WHITE)
    def draw(self,screen):
        screen.blit(self.txt_surface,(self.rect.x+5,self.rect.y+5))
        pygame.draw.rect(screen,self.color,self.rect,2)
    def get_value(self,default):
        try:
            val=int(self.text)
            return max(1,min(val,1000))
        except:
            return default

# ---------------- Rules Page ---------------- #

RULES_TEXT = [
    "Cell States:",
    "- Empty (0) : no effect",
    "- Attract (1) : pulls neighbors",
    "- Repel (-1) : pushes neighbors",
    "",
    "Neighborhood:",
    "- Each cell interacts with 8 surrounding neighbors",
    "- Grid wraps around edges",
    "",
    "Step Update Rules:",
    "1. Compute Influence Vector",
    "   - For each cell, sum vectors from its 8 neighbors:",
    "     * dx, dy = neighbor offsets",
    "     * neighbor value = 1 (Attract), -1 (Repel), 0 (Empty)",
    "     * Multiply offsets by neighbor value and cell state",
    "   - Sum all contributions to get the cell's influence vector",
    "   - Direction gives dominant influence",
    "2. Select Target Neighbors",
    "   - Sector = 1 neighbor; between sectors = 2 neighbors",
    "3. Apply Influence",
    "   - Add +1/-1 to selected neighbor(s)",
    "4. Resolve New States",
    "   - Cells with positive values become Attract cells",
    "   - Cells with negative values become Repel cells",
    "   - Cells with zero value become Empty cells"
]


def show_rules():
    screen_width, screen_height = 600, 730  # increased height
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Rules")
    
    line_height = 25
    margin_top = 20
    bottom_margin = 60  # reserve space for back button
    btn_height = 30
    btn_back = pygame.Rect((screen_width-100)//2, screen_height - bottom_margin + 10, 100, btn_height)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and btn_back.collidepoint(event.pos):
                running = False
        
        screen.fill(BG)
        y = margin_top
        for line in RULES_TEXT:
            if y + line_height < screen_height - bottom_margin:
                screen.blit(FONT.render(line, True, WHITE), (20, y))
                y += line_height
        draw_button(screen, btn_back, "Back")
        pygame.display.flip()


# ---------------- Menu ---------------- #

def menu():
    screen=pygame.display.set_mode((400,450))
    pygame.display.set_caption("Attract and Repel - Menu")

    grid_box=InputBox(200,120,80,30,"30")
    repel_box=InputBox(200,170,80,30,"2")
    attract_box=InputBox(200,220,80,30,"50")
    boxes=[grid_box,repel_box,attract_box]

    start_btn=pygame.Rect(140,280,120,40)
    rules_btn=pygame.Rect(140,330,120,40)

    while True:
        screen.fill(BG)

        # Title
        title_surf = FONT.render("Attract and Repel", True, WHITE)
        screen.blit(title_surf, title_surf.get_rect(center=(200, 60)))

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
                    g=grid_box.get_value(30)
                    r=repel_box.get_value(2)
                    a=attract_box.get_value(50)
                    return g,r,a
                elif rules_btn.collidepoint(event.pos):
                    show_rules()
                    screen=pygame.display.set_mode((400,450))  # reset menu size


# ---------------- Simulation ---------------- #

def run_simulation():
    while True:
        size,r,a=menu()
        grid=generate_random_grid(size,r,a)
        width,height=size*CELL_SIZE,size*CELL_SIZE+60
        screen=pygame.display.set_mode((width,height))
        pygame.display.set_caption("Attract and Repel")

        paused=True
        clock=pygame.time.Clock()
        btn_play=pygame.Rect(20,height-50,80,30)
        btn_step=pygame.Rect(120,height-50,80,30)
        btn_restart=pygame.Rect(220,height-50,100,30)
        btn_menu=pygame.Rect(340,height-50,100,30)

        running=True
        while running:
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    pygame.quit();sys.exit()
                if event.type==pygame.MOUSEBUTTONDOWN:
                    if btn_play.collidepoint(event.pos):
                        paused=not paused
                    elif btn_step.collidepoint(event.pos) and paused:
                        grid=next_step(grid)
                    elif btn_restart.collidepoint(event.pos):
                        grid=generate_random_grid(size,r,a)
                    elif btn_menu.collidepoint(event.pos):
                        running=False
                    elif paused:
                        mx,my=event.pos
                        if my<size*CELL_SIZE:
                            cx,cy=mx//CELL_SIZE,my//CELL_SIZE
                            grid[cy][cx]={0:1,1:-1,-1:0}[grid[cy][cx]]

            if not paused:
                grid=next_step(grid)

            screen.fill(BG)
            draw_grid(screen,grid)
            draw_button(screen,btn_play,"Pause" if not paused else "Play",active=True)
            draw_button(screen,btn_step,"Step")
            draw_button(screen,btn_restart,"Restart")
            draw_button(screen,btn_menu,"Menu")
            pygame.display.flip()
            clock.tick(FPS)

# ---------------- Run ---------------- #
if __name__=="__main__":
    run_simulation()
