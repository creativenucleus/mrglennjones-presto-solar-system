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
STARS = [(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(50)]

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
    (display.create_pen(255, 165, 0), 30, 4.15, 3, False),  # Mercury
    (display.create_pen(255, 255, 0), 50, 1.62, 5, False),  # Venus
    (display.create_pen(0, 100, 255), 70, 1.00, 6, True),   # Earth
    (display.create_pen(255, 0, 0), 90, 0.53, 5, False),    # Mars
    (display.create_pen(255, 200, 100), 120, 0.08, 12, True), # Jupiter
    (display.create_pen(200, 150, 100), 150, 0.03, 10, True), # Saturn
    (display.create_pen(100, 200, 255), 180, 0.011, 8, False), # Uranus
    (display.create_pen(50, 50, 255), 210, 0.006, 8, False)  # Neptune
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

    sun_x_offset = int(5 * math.cos(math.radians(sun_angle)))
    sun_y_offset = int(3 * math.sin(math.radians(sun_angle)))
    sun_angle = (sun_angle + 0.02) % 360

    vector.set_transform(Transform())

    sun = Polygon()
    sun.circle(0, 0, 25)

    t = Transform()
    t.translate(CX + sun_x_offset, CY + sun_y_offset)
    vector.set_transform(t)

    display.set_pen(SUN_COLOR)
    vector.draw(sun)

def draw_planets():
    """Draws planets orbiting the drifting Sun, with smooth size scaling."""
    for i, (color, radius, speed, size, has_moons) in enumerate(PLANETS):
        planet_angles[i] = (planet_angles[i] + speed) % 360
        angle_index = int(planet_angles[i])

        x = CX + sun_x_offset + int(radius * COS_TABLE[angle_index])
        y = CY + sun_y_offset + int(radius * SIN_TABLE[angle_index])

        if has_moons:
            draw_moons(i, x, y)

        planet = Polygon()
        planet.circle(0, 0, size)

        t = Transform()
        t.translate(x, y)
        vector.set_transform(t)
        display.set_pen(color)
        vector.draw(planet)

def draw_moons(parent_index, px, py):
    """Draws moons orbiting their parent planets."""
    for j, (p_index, color, orbit_radius, speed, size) in enumerate(MOONS):
        if p_index == parent_index:
            moon_angles[j] = (moon_angles[j] + speed) % 360
            angle_index = int(moon_angles[j])

            mx = px + int(orbit_radius * COS_TABLE[angle_index])
            my = py + int(orbit_radius * SIN_TABLE[angle_index])

            moon = Polygon()
            moon.circle(0, 0, size)

            t = Transform()
            t.translate(mx, my)
            vector.set_transform(t)
            display.set_pen(color)
            vector.draw(moon)

def draw_orbits():
    """Draws orbit rings using small dotted circles."""
    for _, radius, _, _, _ in PLANETS:
        display.set_pen(DARK_GREY)
        for angle in range(0, 360, 10):  
            x = CX + int(radius * COS_TABLE[angle])
            y = CY + int(radius * SIN_TABLE[angle])
            display.pixel(x, y)  

def draw_stars():
    """Draws a dynamic starfield."""
    for x, y in STARS:
        display.set_pen(WHITE)
        display.pixel(x, y)

def draw_comets():
    """Draws comets moving across the screen."""
    for x, y, _, _ in comets:
        display.set_pen(WHITE)
        display.pixel(int(x), int(y))

def spawn_comet():
    """Randomly spawns a comet."""
    if random.random() < 0.005:  
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 3)
        comets.append([x, y, angle, speed])

def update_comets():
    """Moves comets across the screen."""
    for comet in comets:
        comet[0] += math.cos(comet[2]) * comet[3]
        comet[1] += math.sin(comet[2]) * comet[3]
    comets[:] = [c for c in comets if 0 <= c[0] < WIDTH and 0 <= c[1] < HEIGHT]

while True:
    display.set_pen(BLACK)
    display.clear()

    update_camera()
    spawn_comet()
    update_comets()

    draw_comets()
    draw_stars()
    draw_orbits()
    draw_planets()
    draw_sun()

    presto.update()
    time.sleep(0.01)

