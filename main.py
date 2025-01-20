from presto import Presto
from picovector import PicoVector, Polygon, Transform, ANTIALIAS_FAST
import math
import time
import random

# **Optimized Presto Settings**
presto = Presto(full_res=False, ambient_light=True, layers=1)  
display = presto.display
WIDTH, HEIGHT = display.get_bounds()
CX, CY = WIDTH // 2, HEIGHT // 2  # Screen center
CAMZ, CAMY, CAMZ = 0, 0, 0
CAMRZ = 0

# **Define Colors**
BLACK = display.create_pen(0, 0, 0)  # Background
DARK_GREY = display.create_pen(50, 50, 50)  # Dark Grey Orbit Rings (Dotted)
WHITE = display.create_pen(255, 255, 255)  # Stars & Comets
SUN_COLOR = display.create_pen(255, 255, 0)  # Sun Core

# **Precompute Sin/Cos Tables for Faster Math**
SIN_TABLE = [math.sin(math.radians(i)) for i in range(360)]
COS_TABLE = [math.cos(math.radians(i)) for i in range(360)]

# **Initialize PicoVector**
vector = PicoVector(display)
vector.set_antialiasing(ANTIALIAS_FAST)

# **Starfield Background (Fixed)**
STARS = [((random.random()*2-1)*1.5, (random.random()*2-1)*1.5) for _ in range(50)]

T=0

# **Comet System**
comets = []

# **Sun & Camera Motion Variables**
sun_x_offset = 0
sun_y_offset = 0
sun_angle = 0  # Sun drifting angle

cam_x_offset = 0
cam_y_offset = 0
cam_angle = 0  # Camera panning angle

# **Planets: (Color, Orbit Radius, Orbital Speed, Size, Has Moons?)**
PLANETS = [
    (display.create_pen(255, 165, 0), 30, 4.15, 3, False, (255,165,0)),  # Mercury
    (display.create_pen(255, 255, 0), 50, 1.62, 5, False, (255,255,0)),  # Venus
    (display.create_pen(0, 100, 255), 70, 1.00, 6, True, (0,100,255)),   # Earth
    (display.create_pen(255, 0, 0), 90, 0.53, 5, False, (255,0,0)),    # Mars
    (display.create_pen(255, 200, 100), 120, 0.08, 12, True, (255,200,100)), # Jupiter
    (display.create_pen(200, 150, 100), 150, 0.03, 10, True, (200,150,100)), # Saturn
    (display.create_pen(100, 200, 255), 180, 0.011, 8, False, (100,200,255)), # Uranus
    (display.create_pen(50, 50, 255), 210, 0.006, 8, False, (50,50,255))  # Neptune
]

# **Moons: (Parent Index, Color, Orbit Radius, Orbital Speed, Size)**
MOONS = [
    (2, display.create_pen(200, 200, 200), 10, 5.0, 2),  # Earth's Moon
    (4, display.create_pen(255, 150, 50), 15, 6.5, 2),  # Io (Jupiter)
    (4, display.create_pen(255, 255, 255), 20, 4.8, 2),  # Europa (Jupiter)
    (4, display.create_pen(150, 150, 150), 25, 2.5, 3),  # Ganymede (Jupiter)
    (4, display.create_pen(120, 100, 90), 30, 1.2, 3),  # Callisto (Jupiter)
    (5, display.create_pen(255, 180, 100), 15, 3.1, 2),  # Titan (Saturn)
]

# **Camera Animation Variables**
tilt_angle = 0  # Slowly tilts the whole system

# **Store planet & moon angles**
planet_angles = [0 for _ in PLANETS]
moon_angles = [0 for _ in MOONS]

def update_camera():
    """Gently moves the camera focus in a subtle elliptical orbit."""
    global cam_x_offset, cam_y_offset, cam_angle

    cam_x_offset = int(12 * math.sin(math.radians(cam_angle)))
    cam_y_offset = int(7 * math.cos(math.radians(cam_angle)))
    cam_angle = (cam_angle + 0.01) % 360

def draw_sun():
    """Draws the Sun with gentle drifting motion."""
    global sun_x_offset, sun_y_offset, sun_angle

    sun_x_offset = 5/30 * math.cos(math.radians(sun_angle))
    sun_y_offset = 3/30 * math.sin(math.radians(sun_angle))
    sun_angle = (sun_angle + 0.02) % 360

    x, y, z = proj(sun_y_offset, sun_y_offset, 0)
    if z>0:
        sun = Polygon()
        sun.circle(0, 0, circR(15, z))

        t = Transform()
        t.translate(x, y)
        vector.set_transform(t)

        display.set_pen(SUN_COLOR)
        vector.draw(sun)

@micropython.native
def rot(a, b, r):
#    s = SIN_TABLE[r%360]
#    c = COS_TABLE[r%360]
    s = math.sin(r/57.29)
    c = math.cos(r/57.29)
    return c*a - s*b, s*a + c*b

@micropython.native
def proj(x,y,z):   
    x, y = rot(x, y, CAMRZ)
    y, z = rot(y, z, CAMRX)
    
    z = z + 30
    if z == 0:
        z = 0.0001
    
    dz=800*(6/(z-CAMZ+6))
    return CX+(x-CAMX)*dz, CY+(y-CAMY)*dz, dz

def circR(size, z):
    return max(1, min(40, 0.002 * (size * z)))

def draw_planets():
    """Draws planets orbiting the drifting Sun, with smooth size scaling."""
    for i, (color, radius, speed, size, has_moons, _) in enumerate(PLANETS):
        planet_angles[i] = (planet_angles[i] + speed) % 360
        angle_index = int(planet_angles[i])

        x = radius * COS_TABLE[angle_index] / 250
        y = radius * SIN_TABLE[angle_index] / 250
        z = 0
        
        if has_moons:
            draw_moons(i, x, y, z)

        x, y, z = proj(x, y, z)
        if z > 0:
            planet = Polygon()
            planet.circle(0, 0, circR(size, z))
            t = Transform()
            t.translate(x, y)
            vector.set_transform(t)
            display.set_pen(color)
            vector.draw(planet)

def draw_moons(parent_index, px, py, pz):
    """Draws moons orbiting their parent planets."""
    for j, (p_index, color, orbit_radius, speed, size) in enumerate(MOONS):
        if p_index == parent_index:
            moon_angles[j] = (moon_angles[j] + speed) % 360
            angle_index = int(moon_angles[j])

            mx = px + (orbit_radius * COS_TABLE[angle_index]) / 250
            my = py + (orbit_radius * SIN_TABLE[angle_index]) / 250
            mz = pz

            mx, my, mz = proj(mx, my, mz)
            if mz > 0:
                moon = Polygon()
                moon.circle(0, 0, circR(size, mz))

                t = Transform()
                t.translate(mx, my)
                vector.set_transform(t)
                display.set_pen(color)
                vector.draw(moon)

def draw_orbits():
    """Draws orbit rings using small dotted circles."""
    for pen, radius, _, _, _, rgbs in PLANETS:
        display.set_pen(display.create_pen(rgbs[0]//4,rgbs[1]//4,rgbs[2]//4))
        iPen = 0
        for angle in range(0, 360, 10):
            x = radius * COS_TABLE[angle] / 250
            y = radius * SIN_TABLE[angle] / 250
            x, y, z = proj(x, y, 0)
            display.pixel(int(x), int(y))

def draw_stars():
    """Draws a dynamic starfield."""
    for x, y in STARS:
        display.set_pen(WHITE)
        x, y, z = proj(x, y, 0)
        display.pixel(int(x), int(y))

def draw_comets():
    """Draws comets moving across the screen."""
    for x, y, _, _ in comets:
        x, y, z = proj(x, y, 0)
        display.set_pen(WHITE)
        display.pixel(int(x), int(y))

def spawn_comet():
    """Randomly spawns a comet."""
    if random.random() < 0.005:  
        x = random.random()*2-1
        y = random.random()*2-1
        angle = random.uniform(0, 2 * math.pi)
        speed = (.1+random.random()*.9)*.01
        comets.append([x, y, angle, speed])

def update_comets():
    """Moves comets across the screen."""
    for comet in comets:
        comet[0] += math.cos(comet[2]) * comet[3]
        comet[1] += math.sin(comet[2]) * comet[3]
    comets[:] = [c for c in comets if -1 <= c[0] < 1 and -1 <= c[1] < 1]

while True:
    display.set_pen(BLACK)
    display.clear()

    CAMZ = 15 + SIN_TABLE[T%360] * 10
    CAMX = 0
    CAMX = math.sin(T*.02) * .2
    CAMRZ = -T
    CAMRX = 65+math.sin(T*.04) * 10
    
    update_camera()
    spawn_comet()
    update_comets()

    draw_comets()
    draw_stars()
    draw_orbits()
    draw_planets()
    
    draw_sun()

    presto.update()
    T=T+1
    time.sleep(1/60)

