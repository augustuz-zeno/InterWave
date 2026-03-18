import hashlib
import numpy as np
import random
from PIL import Image, ImageFilter
import os

PALETTES = [
    ["#0f172a", "#38bdf8", "#1e293b"],
    ["#111827", "#a78bfa", "#1f2937"],
    ["#1e293b", "#f472b6", "#334155"],
    ["#0b3c5d", "#f2c94c", "#1d2731"],
    ["#1a1a2e", "#e94560", "#16213e"],
    ["#070a0d", "#4ade80", "#111827"],
]

def hex_to_rgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32)

def gradient_map(t, colors):
    c1, c2, c3 = colors
    t = np.clip(t, 0, 1)
    t = t[:, :, None]

    # плавный "дорогой" градиент (Bezier)
    return (
        c1 * (1 - t)**2 +
        2 * c2 * (1 - t) * t +
        c3 * t**2
    )

def layered_pattern(nx, ny):
    v = np.zeros_like(nx)
    for _ in range(4):
        f = np.random.uniform(2, 8)
        angle = np.random.uniform(0, np.pi)
        v += np.sin(f * (nx * np.cos(angle) + ny * np.sin(angle)))
    return v / 4

def generate_avatar(text, size=1024):
    # seed
    seed_hash = hashlib.md5(text.encode()).hexdigest()
    seed = int(seed_hash, 16) % (2**32)
    random.seed(seed)
    np.random.seed(seed)

    palette = random.choice(PALETTES)
    colors = [hex_to_rgb(c) for c in palette]

    # grid
    x = np.linspace(-1, 1, size)
    y = np.linspace(-1, 1, size)
    nx, ny = np.meshgrid(x, y)

    # лёгкий шум (убирает "идеальность")
    nx += np.random.normal(0, 0.01, nx.shape)
    ny += np.random.normal(0, 0.01, ny.shape)

    # случайный поворот
    angle = np.random.uniform(0, 2*np.pi)
    rx = nx * np.cos(angle) - ny * np.sin(angle)
    ry = nx * np.sin(angle) + ny * np.cos(angle)

    dist = np.sqrt(rx**2 + ry**2)

    # domain warping
    warp_strength = np.random.uniform(0.2, 0.4)
    p = np.random.uniform(0, np.pi)

    warp_x = rx + warp_strength * np.sin(ry * 3 + p)
    warp_y = ry + warp_strength * np.cos(rx * 3 - p)

    # паттерны (все смешиваются)
    waves = layered_pattern(warp_x, warp_y)
    radial = np.sin(dist * np.random.uniform(6, 12)) + 0.3 * np.sin(rx * 4)
    grid = np.sin(warp_x * 8) * np.sin(warp_y * 8)

    weights = np.random.dirichlet([1, 1, 1])
    v = weights[0]*waves + weights[1]*radial + weights[2]*grid

    # нормализация
    v = (v - v.min()) / (v.max() - v.min())

    # мягкие линии
    lines = np.abs(np.sin(v * np.pi * np.random.uniform(3, 6)))
    intensity = np.power(lines, np.random.uniform(2.0, 3.5))

    # цвет
    img_data = gradient_map(intensity, colors)

    # освещение
    dx = np.gradient(v, axis=1)
    dy = np.gradient(v, axis=0)
    light = (dx + dy)
    light = (light - light.min()) / (light.max() - light.min())
    img_data *= (0.75 + 0.25 * light[:, :, None])

    # виньетка
    vignette = 1 - (dist**2) * 0.5
    img_data *= np.clip(vignette, 0, 1)[:, :, None]

    # мягкая симметрия (НЕ зеркальная полностью)
    symmetry_strength = np.random.uniform(0.3, 0.8)
    mirror = img_data[:, :size//2][:, ::-1]
    img_data[:, size//2:] = (
        img_data[:, size//2:] * (1 - symmetry_strength) +
        mirror * symmetry_strength
    )

    # мягкое зерно
    grain = np.random.normal(0, 4, (size, size, 1))
    img_data += grain

    # контраст
    img_data = 255 * np.power(np.clip(img_data / 255, 0, 1), 0.9)

    # в изображение
    img = Image.fromarray(np.clip(img_data, 0, 255).astype(np.uint8))

    # glow
    glow = img.filter(ImageFilter.GaussianBlur(18))
    img = Image.blend(img, glow, alpha=0.25)

    # лёгкая хроматическая аберрация
    img_np = np.array(img).astype(np.float32)
    shift = 2
    img_np[shift:, :, 0] = img_np[:-shift, :, 0]
    img_np[:-shift, :, 2] = img_np[shift:, :, 2]

    img = Image.fromarray(np.clip(img_np, 0, 255).astype(np.uint8))

    return img


if __name__ == "__main__":
    nick = input("Ник: ").strip()
    if not nick:
        nick = f"user_{random.randint(1000, 9999)}"

    os.makedirs("output", exist_ok=True)

    img = generate_avatar(nick, size=1024)
    img = img.filter(ImageFilter.SMOOTH_MORE)

    path = os.path.join("output", f"avatar_{nick}.png")
    img.save(path)

    print(f"Готово! Сохранено в: {path}")