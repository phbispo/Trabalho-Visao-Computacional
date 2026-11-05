"""Gera imagens temáticas de alta resolução para as fases do quebra-cabeça.

Cria ilustrações ricas em detalhes visuais e cores para cada fase:
1. Fase 1 (2x2): Espaço Cósmico (Foguete, planetas e estrelas)
2. Fase 2 (3x2): Floresta Mágica (Montanhas, pinheiros, sol e lago)
3. Fase 3 (3x3): Robô Futurista (Robô amigável, circuitos neon e engrenagens)
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

PASTA_ASSETS = Path(__file__).parent / "assets"
PASTA_ASSETS.mkdir(parents=True, exist_ok=True)
TAMANHO = (600, 600)


def gerar_fase1_espaco():
    """Gera ilustração do tema Espaço Cósmico (600x600)."""
    img = Image.new("RGBA", TAMANHO, (15, 12, 40, 255))
    draw = ImageDraw.Draw(img)

    # 1. Nebulosa de fundo (gradientes circulares)
    for r, cor in [(280, (60, 20, 100, 40)), (200, (120, 40, 140, 50)), (130, (30, 80, 180, 60))]:
        temp = Image.new("RGBA", TAMANHO, (0, 0, 0, 0))
        d_temp = ImageDraw.Draw(temp)
        d_temp.ellipse([300 - r, 300 - r, 300 + r, 300 + r], fill=cor)
        temp = temp.filter(ImageFilter.GaussianBlur(40))
        img = Image.alpha_composite(img, temp)
    draw = ImageDraw.Draw(img)

    # 2. Estrelas aleatórias com tamanhos variados
    rng = random.Random(42)
    for _ in range(120):
        sx, sy = rng.randint(10, 590), rng.randint(10, 590)
        s_raio = rng.choice([1, 2, 3])
        brilho = rng.randint(180, 255)
        cor_estrela = (brilho, brilho, rng.randint(220, 255), 255)
        draw.ellipse([sx - s_raio, sy - s_raio, sx + s_raio, sy + s_raio], fill=cor_estrela)
        if s_raio == 3 and rng.random() > 0.6:
            draw.line([(sx - 6, sy), (sx + 6, sy)], fill=(255, 255, 255, 200), width=1)
            draw.line([(sx, sy - 6), (sx, sy + 6)], fill=(255, 255, 255, 200), width=1)

    # 3. Planeta com anéis (canto superior esquerdo)
    px, py, pr = 160, 170, 75
    draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(230, 140, 60, 255), outline=(255, 180, 100, 255), width=3)
    # Faixas do planeta
    draw.arc([px - pr + 8, py - 30, px + pr - 8, py + 30], 0, 180, fill=(200, 100, 40, 255), width=12)
    draw.arc([px - pr + 15, py - 50, px + pr - 15, py + 10], 0, 180, fill=(250, 190, 90, 255), width=8)
    # Anel de Saturno
    anel = Image.new("RGBA", TAMANHO, (0, 0, 0, 0))
    d_anel = ImageDraw.Draw(anel)
    d_anel.ellipse([px - 140, py - 35, px + 140, py + 35], outline=(240, 210, 140, 220), width=10)
    d_anel.ellipse([px - 125, py - 25, px + 125, py + 25], outline=(200, 170, 110, 160), width=4)
    anel = anel.rotate(-22, center=(px, py), resample=Image.BICUBIC)
    img = Image.alpha_composite(img, anel)
    draw = ImageDraw.Draw(img)

    # 4. Lua / Planeta Menor (canto inferior direito)
    mx, my, mr = 470, 440, 50
    draw.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(80, 170, 230, 255), outline=(130, 220, 255, 255), width=3)
    # Crateras
    for cx, cy, cr in [(450, 430, 12), (485, 455, 10), (465, 460, 7)]:
        draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(60, 130, 190, 255), outline=(40, 100, 150, 255), width=2)

    # 5. Foguete estilizado voando em diagonal no centro
    fx, fy = 320, 310
    # Chamas do motor
    chama_pts = [(fx - 15, fy + 45), (fx, fy + 85), (fx + 15, fy + 45), (fx + 5, fy + 65), (fx - 5, fy + 65)]
    draw.polygon(chama_pts, fill=(255, 90, 20, 255))
    draw.polygon([(fx - 8, fy + 45), (fx, fy + 70), (fx + 8, fy + 45)], fill=(255, 230, 50, 255))
    # Asas
    draw.polygon([(fx - 22, fy + 15), (fx - 48, fy + 42), (fx - 18, fy + 40)], fill=(220, 40, 50, 255), outline=(180, 20, 30, 255), width=2)
    draw.polygon([(fx + 22, fy + 15), (fx + 48, fy + 42), (fx + 18, fy + 40)], fill=(220, 40, 50, 255), outline=(180, 20, 30, 255), width=2)
    # Corpo do foguete
    corpo_pts = [(fx, fy - 65), (fx + 26, fy - 15), (fx + 22, fy + 42), (fx - 22, fy + 42), (fx - 26, fy - 15)]
    draw.polygon(corpo_pts, fill=(245, 245, 250, 255), outline=(180, 190, 205, 255), width=3)
    # Bico vermelho
    bico_pts = [(fx, fy - 65), (fx + 22, fy - 25), (fx - 22, fy - 25)]
    draw.polygon(bico_pts, fill=(230, 45, 55, 255))
    # Janela circular
    draw.ellipse([fx - 14, fy - 10, fx + 14, fy + 18], fill=(60, 160, 240, 255), outline=(200, 220, 240, 255), width=3)
    draw.ellipse([fx - 8, fy - 4, fx + 2, fy + 6], fill=(180, 230, 255, 220))

    # Moldura externa suave
    draw.rectangle([0, 0, 599, 599], outline=(80, 100, 180, 200), width=4)
    img.save(PASTA_ASSETS / "puzzle_espaco.png")
    print("Salvo: puzzle_espaco.png")


def gerar_fase2_floresta():
    """Gera ilustração do tema Floresta Encantada (600x600)."""
    img = Image.new("RGBA", TAMANHO, (250, 190, 100, 255))
    draw = ImageDraw.Draw(img)

    # 1. Céu com degradê do pôr do sol
    for y in range(350):
        prog = y / 350.0
        r = int(255 * (1 - prog) + 240 * prog)
        g = int(140 * (1 - prog) + 180 * prog)
        b = int(110 * (1 - prog) + 160 * prog)
        draw.line([(0, y), (600, y)], fill=(r, g, b, 255))

    # 2. Sol gigante nascendo/se pondo
    sx, sy, sr = 300, 210, 85
    draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 235, 140, 240), outline=(255, 215, 80, 255), width=3)

    # 3. Montanhas ao fundo (camada 1 - roxa distante)
    draw.polygon([(0, 360), (140, 170), (280, 360)], fill=(120, 85, 140, 255))
    draw.polygon([(180, 360), (330, 150), (480, 360)], fill=(95, 65, 120, 255))
    draw.polygon([(360, 360), (510, 190), (600, 360)], fill=(110, 75, 130, 255))

    # Neve no pico das montanhas
    draw.polygon([(140, 170), (115, 205), (135, 195), (145, 205), (165, 205)], fill=(245, 245, 255, 255))
    draw.polygon([(330, 150), (300, 195), (325, 180), (335, 195), (360, 195)], fill=(245, 245, 255, 255))

    # 4. Lago espelhado e colinas verdes (camada média)
    draw.rectangle([0, 360, 600, 600], fill=(45, 110, 70, 255))
    # Rio/Lago sinuoso azul esmeralda
    lago_pts = [(0, 480), (180, 450), (320, 470), (460, 440), (600, 490), (600, 600), (0, 600)]
    draw.polygon(lago_pts, fill=(50, 140, 170, 255), outline=(70, 180, 210, 255), width=3)

    # 5. Pinheiros em estilo low-poly/vetorial
    def desenhar_pinheiro(px, py, escala=1.0):
        # Tronco
        tw, th = int(12 * escala), int(30 * escala)
        draw.rectangle([px - tw // 2, py - th, px + tw // 2, py], fill=(90, 55, 35, 255))
        # 3 camadas de folhas
        camadas = [(40, 35, 25), (32, 28, 48), (22, 22, 68)]
        for larg, alt, sobe in camadas:
            w = int(larg * escala)
            h = int(alt * escala)
            top_y = py - int(sobe * escala)
            pts = [(px, top_y - h), (px - w, top_y), (px + w, top_y)]
            draw.polygon(pts, fill=(30, 95, 55, 255), outline=(20, 75, 40, 255), width=2)

    desenhar_pinheiro(90, 450, 1.3)
    desenhar_pinheiro(150, 440, 1.0)
    desenhar_pinheiro(480, 430, 1.2)
    desenhar_pinheiro(540, 450, 1.4)
    desenhar_pinheiro(40, 460, 0.9)

    # 6. Cogumelos mágicos vermelhos com bolinhas brancas no primeiro plano
    for cx, cy, cr in [(240, 540, 24), (275, 555, 16)]:
        # Haste
        draw.rectangle([cx - cr // 4, cy, cx + cr // 4, cy + int(cr * 1.1)], fill=(240, 235, 220, 255))
        # Chapéu
        draw.pieslice([cx - cr, cy - cr, cx + cr, cy + cr], 180, 360, fill=(230, 40, 40, 255), outline=(180, 20, 20, 255), width=2)
        # Bolinhas
        draw.ellipse([cx - cr // 2, cy - cr // 2, cx - cr // 4, cy - cr // 4], fill=(255, 255, 255, 255))
        draw.ellipse([cx + cr // 5, cy - cr // 1.6, cx + cr // 2.5, cy - cr // 2.5], fill=(255, 255, 255, 255))

    # Moldura
    draw.rectangle([0, 0, 599, 599], outline=(40, 90, 60, 220), width=4)
    img.save(PASTA_ASSETS / "puzzle_floresta.png")
    print("Salvo: puzzle_floresta.png")


def gerar_fase3_robot():
    """Gera ilustração do tema Robô Futurista / IA (600x600)."""
    img = Image.new("RGBA", TAMANHO, (18, 24, 38, 255))
    draw = ImageDraw.Draw(img)

    # 1. Trilha de circuitos eletrônicos luminosos ao fundo
    linhas = [
        [(40, 80), (120, 80), (160, 120), (160, 220)],
        [(560, 80), (480, 80), (440, 120), (440, 220)],
        [(80, 520), (160, 520), (200, 480)],
        [(520, 520), (440, 520), (400, 480)],
        [(300, 30), (300, 80)],
    ]
    for pts in linhas:
        draw.line(pts, fill=(0, 200, 255, 140), width=3)
        for px, py in pts:
            draw.ellipse([px - 5, py - 5, px + 5, py + 5], fill=(0, 240, 255, 200))

    # 2. Engrenagens mecânicas decorativas
    def desenhar_engrenagem(cx, cy, r_int, r_ext, dentes=8, cor=(60, 80, 110, 200)):
        temp = Image.new("RGBA", TAMANHO, (0, 0, 0, 0))
        d_temp = ImageDraw.Draw(temp)
        for i in range(dentes):
            ang = (2 * math.pi / dentes) * i
            dx, dy = math.cos(ang) * r_ext, math.sin(ang) * r_ext
            d_temp.rectangle([cx + dx - 7, cy + dy - 7, cx + dx + 7, cy + dy + 7], fill=cor)
        d_temp.ellipse([cx - r_int, cy - r_int, cx + r_int, cy + r_int], fill=cor)
        d_temp.ellipse([cx - r_int // 2, cy - r_int // 2, cx + r_int // 2, cy + r_int // 2], fill=(18, 24, 38, 255))
        return temp

    img = Image.alpha_composite(img, desenhar_engrenagem(100, 180, 40, 55, dentes=10))
    img = Image.alpha_composite(img, desenhar_engrenagem(500, 180, 40, 55, dentes=10))
    draw = ImageDraw.Draw(img)

    # 3. Cabeça do Robô (Centro)
    rx, ry = 300, 280
    # Antena
    draw.line([(rx, ry - 140), (rx, ry - 100)], fill=(180, 200, 220, 255), width=6)
    draw.ellipse([rx - 14, ry - 154, rx + 14, ry - 126], fill=(255, 60, 90, 255), outline=(255, 200, 200, 255), width=3)

    # Orelhas / Parafusos laterais
    draw.rectangle([rx - 150, ry - 40, rx - 125, ry + 20], fill=(120, 140, 160, 255), outline=(200, 220, 240, 255), width=2)
    draw.rectangle([rx + 125, ry - 40, rx + 150, ry + 20], fill=(120, 140, 160, 255), outline=(200, 220, 240, 255), width=2)

    # Rosto (Caixa chanfrada metálica)
    draw.rounded_rectangle([rx - 125, ry - 100, rx + 125, ry + 90], radius=28, fill=(215, 225, 240, 255), outline=(130, 155, 185, 255), width=5)

    # Visor de Vidro Escuro
    draw.rounded_rectangle([rx - 105, ry - 80, rx + 105, ry + 20], radius=18, fill=(15, 22, 35, 255), outline=(0, 220, 255, 255), width=4)

    # Olhos de LED Ciano Brilhantes (expressão alegre e amigável)
    # Olho esquerdo
    draw.ellipse([rx - 70, ry - 52, rx - 20, ry - 8], fill=(0, 245, 255, 255), outline=(200, 255, 255, 255), width=3)
    draw.ellipse([rx - 55, ry - 44, rx - 35, ry - 24], fill=(255, 255, 255, 255))
    # Olho direito
    draw.ellipse([rx + 20, ry - 52, rx + 70, ry - 8], fill=(0, 245, 255, 255), outline=(200, 255, 255, 255), width=3)
    draw.ellipse([rx + 35, ry - 44, rx + 55, ry - 24], fill=(255, 255, 255, 255))

    # Bochechas rosadas de LED
    draw.ellipse([rx - 90, ry - 10, rx - 75, ry + 5], fill=(255, 120, 160, 200))
    draw.ellipse([rx + 75, ry - 10, rx + 90, ry + 5], fill=(255, 120, 160, 200))

    # Sorriso digital (arco iluminado)
    draw.arc([rx - 45, ry + 30, rx + 45, ry + 70], 20, 160, fill=(40, 60, 90, 255), width=6)

    # 4. Pescoço e Corpo com Núcleo de Energia (Arc Reactor)
    draw.rectangle([rx - 30, ry + 90, rx + 30, ry + 120], fill=(100, 120, 140, 255))
    # Ombros
    draw.rounded_rectangle([rx - 160, ry + 120, rx + 160, ry + 260], radius=24, fill=(190, 205, 225, 255), outline=(120, 145, 175, 255), width=4)
    # Núcleo de energia no peito
    draw.ellipse([rx - 36, ry + 150, rx + 36, ry + 222], fill=(0, 220, 255, 255), outline=(255, 255, 255, 255), width=4)
    draw.ellipse([rx - 20, ry + 166, rx + 20, ry + 206], fill=(255, 255, 255, 255))

    # Moldura
    draw.rectangle([0, 0, 599, 599], outline=(0, 180, 240, 220), width=4)
    img.save(PASTA_ASSETS / "puzzle_robot.png")
    print("Salvo: puzzle_robot.png")


if __name__ == "__main__":
    gerar_fase1_espaco()
    gerar_fase2_floresta()
    gerar_fase3_robot()
    print("Todas as ilustrações foram geradas com sucesso em /assets!")

