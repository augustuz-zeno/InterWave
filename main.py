import hashlib
import numpy as np
import random
from PIL import Image, ImageFilter

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
    return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)])

def generate_avatar(text, size=1024):
    seed_hash = hashlib.md5(text.encode()).hexdigest()
    seed = int(seed_hash, 16) % (2**32)
    
    random.seed(seed)
    np.random.seed(seed)

    palette = random.choice(PALETTES)
    colors = [hex_to_rgb(c) for c in palette]
    bg, accent = colors[0], colors[1]

    x = np.linspace(-1, 1, size)
    y = np.linspace(-1, 1, size)
    nx, ny = np.meshgrid(x, y)

    # Усложненная формула узора
    f1, f2 = np.random.uniform(3.0, 8.0, 2)
    p = np.random.uniform(0, np.pi)
    dist = np.sqrt(nx**2 + ny**2)
    
    v = (np.sin(f1 * nx + p) * np.cos(f2 * ny) + 
         np.sin(dist * 5 - p) * 0.5 +
         np.cos(nx * ny * 4))

    v = (v - v.min()) / (v.max() - v.min())
    # Более интересные изолинии
    lines = np.abs(np.sin(v * np.pi * 6))
    intensity = np.power(lines, 3.0)

    # Рендеринг каналов
    img_data = np.zeros((size, size, 3), dtype=np.float32)
    for i in range(3):
        img_data[:, :, i] = bg[i] * (1 - intensity) + accent[i] * intensity

    # Хроматическая аберрация (сдвиг красного и синего)
    shift = 4
    img_data[shift:, :, 0] = img_data[:-shift, :, 0] # Сдвиг R
    img_data[:-shift, :, 2] = img_data[shift:, :, 2] # Сдвиг B

    # Виньетка
    vignette = 1 - (dist**2) * 0.5
    img_data *= np.clip(vignette, 0, 1)[:, :, np.newaxis]

    # Пленочное зерно
    grain = np.random.normal(0, 8, (size, size, 3))
    img_data = np.clip(img_data + grain, 0, 255)

    return Image.fromarray(img_data.astype(np.uint8))

if __name__ == "__main__":
    nick = input("Ник (пусто для случайного): ").strip()
    if not nick:
        nick = f"user_{random.randint(1000, 9999)}"
        
    img = generate_avatar(nick)
    
    # Небольшое размытие в конце для мягкости
    img = img.filter(ImageFilter.SMOOTH_MORE)
    
    path = f"avatar_{nick}.png"
    img.save(path)
    print(f"Готово! Сохранено как {path}")