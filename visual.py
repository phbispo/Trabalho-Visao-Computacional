"""Renderização visual: tabuleiro, fatiamento de peças, sombras, partículas e HUD.

Utiliza OpenCV para operações geométricas e Pillow para renderização tipográfica
com suporte completo a acentos do idioma português.
"""
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from logica import BotaoVirtual, JogoQuebraCabeca, Particula, Peca

PASTA_ASSETS = Path(__file__).parent / "assets"


def _obter_fonte(tamanho: int, negrito: bool = True):
    """Carrega fonte TrueType do sistema ou padrão do Pillow."""
    nomes = (["DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf", "segoeui.ttf"] if negrito
             else ["DejaVuSans.ttf", "arial.ttf", "Arial.ttf", "segoeuisl.ttf"])
    for nome in nomes:
        try:
            return ImageFont.truetype(nome, tamanho)
        except OSError:
            continue
    return ImageFont.load_default(tamanho)


class TextoRender:
    """Acumula textos para desenho otimizado em lote usando Pillow."""

    def __init__(self):
        self.itens: List[Tuple[str, Tuple[int, int], int, Tuple[int, int, int], str, bool]] = []

    def add(self, texto: str, xy: Tuple[int, int], tamanho: int = 24,
            cor: Tuple[int, int, int] = (255, 255, 255), ancora: str = "la", negrito: bool = True):
        self.itens.append((texto, xy, tamanho, cor, ancora, negrito))

    def desenhar(self, quadro_bgr: np.ndarray):
        if not self.itens:
            return
        img_pil = Image.fromarray(cv2.cvtColor(quadro_bgr, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        for texto, xy, tamanho, cor, ancora, negrito in self.itens:
            fonte = _obter_fonte(tamanho, negrito)
            # Sombra de contorno escura para legibilidade máxima sobre qualquer fundo
            draw.text(xy, texto, font=fonte, fill=cor, anchor=ancora,
                      stroke_width=max(1, tamanho // 12), stroke_fill=(15, 15, 20))
        quadro_bgr[:] = cv2.cvtColor(np.asarray(img_pil), cv2.COLOR_RGB2BGR)
        self.itens.clear()


class GerenciadorPecasVisuais:
    """Carrega as imagens originais das fases e recorta os sprites das peças."""

    def __init__(self, pasta_assets: Path = PASTA_ASSETS):
        self.pasta = pasta_assets
        self.imagens_base: Dict[str, np.ndarray] = {}
        self.recortes_pecas: Dict[Tuple[str, int, int, int, int], np.ndarray] = {}

    def _carregar_imagem(self, nome: str) -> np.ndarray:
        if nome not in self.imagens_base:
            caminho = self.pasta / nome
            if not caminho.exists():
                # Cria uma imagem de fallback gradiente caso o arquivo ainda não exista
                img = np.zeros((600, 600, 3), dtype=np.uint8)
                for y in range(600):
                    img[y, :] = (int(255 * y / 600), 120, int(255 * (1 - y / 600)))
                self.imagens_base[nome] = img
            else:
                self.imagens_base[nome] = cv2.imread(str(caminho), cv2.IMREAD_COLOR)
        return self.imagens_base[nome]

    def obter_recorte_peca(self, img_nome: str, l: int, c: int,
                           total_l: int, total_c: int,
                           largura_saida: int, altura_saida: int) -> np.ndarray:
        """Retorna o recorte exato da peça com acabamento biselado nas bordas."""
        chave = (img_nome, l, c, largura_saida, altura_saida)
        if chave in self.recortes_pecas:
            return self.recortes_pecas[chave]

        base = self._carregar_imagem(img_nome)
        h_orig, w_orig = base.shape[:2]

        # Coordenadas do corte na imagem original
        y0 = int(round(l * (h_orig / total_l)))
        y1 = int(round((l + 1) * (h_orig / total_l)))
        x0 = int(round(c * (w_orig / total_c)))
        x1 = int(round((c + 1) * (w_orig / total_c)))

        fatia = base[y0:y1, x0:x1]
        redimensionada = cv2.resize(fatia, (largura_saida, altura_saida), interpolation=cv2.INTER_LINEAR)

        # Adiciona canal alfa (BGRA) para transparência e bordas chanfradas
        bgra = cv2.cvtColor(redimensionada, cv2.COLOR_BGR2BGRA)
        self.recortes_pecas[chave] = bgra
        return bgra

    def obter_imagem_redimensionada(self, img_nome: str, largura: int, altura: int) -> np.ndarray:
        """Retorna a imagem completa do puzzle redimensionada para a dica/gabarito."""
        base = self._carregar_imagem(img_nome)
        return cv2.resize(base, (largura, altura), interpolation=cv2.INTER_LINEAR)


def desenhar_retangulo_arredondado(quadro, pt1, pt2, cor, raio=12, espessura=-1):
    """Desenha retângulo com cantos arredondados usando OpenCV."""
    x1, y1 = pt1
    x2, y2 = pt2
    w = x2 - x1
    h = y2 - y1
    raio = min(raio, w // 2, h // 2)

    if espessura == -1:
        # Preenchimento
        cv2.rectangle(quadro, (x1 + raio, y1), (x2 - raio, y2), cor, -1)
        cv2.rectangle(quadro, (x1, y1 + raio), (x2, y2 - raio), cor, -1)
        cv2.circle(quadro, (x1 + raio, y1 + raio), raio, cor, -1, cv2.LINE_AA)
        cv2.circle(quadro, (x2 - raio, y1 + raio), raio, cor, -1, cv2.LINE_AA)
        cv2.circle(quadro, (x1 + raio, y2 - raio), raio, cor, -1, cv2.LINE_AA)
        cv2.circle(quadro, (x2 - raio, y2 - raio), raio, cor, -1, cv2.LINE_AA)
    else:
        # Contorno
        cv2.line(quadro, (x1 + raio, y1), (x2 - raio, y1), cor, espessura, cv2.LINE_AA)
        cv2.line(quadro, (x1 + raio, y2), (x2 - raio, y2), cor, espessura, cv2.LINE_AA)
        cv2.line(quadro, (x1, y1 + raio), (x1, y2 - raio), cor, espessura, cv2.LINE_AA)
        cv2.line(quadro, (x2, y1 + raio), (x2, y2 - raio), cor, espessura, cv2.LINE_AA)
        cv2.ellipse(quadro, (x1 + raio, y1 + raio), (raio, raio), 180, 0, 90, cor, espessura, cv2.LINE_AA)
        cv2.ellipse(quadro, (x2 - raio, y1 + raio), (raio, raio), 270, 0, 90, cor, espessura, cv2.LINE_AA)
        cv2.ellipse(quadro, (x2 - raio, y2 - raio), (raio, raio), 0, 0, 90, cor, espessura, cv2.LINE_AA)
        cv2.ellipse(quadro, (x1 + raio, y2 - raio), (raio, raio), 90, 0, 90, cor, espessura, cv2.LINE_AA)


def desenhar_tabuleiro(quadro: np.ndarray, jogo: JogoQuebraCabeca, gerenciador: GerenciadorPecasVisuais):
    """Desenha a moldura do tabuleiro, slots de encaixe e dica translúcida."""
    x0 = int(jogo.tabuleiro_x0)
    y0 = int(jogo.tabuleiro_y0)
    tam = int(jogo.tabuleiro_tamanho)

    # 1. Fundo escurecido translúcido do tabuleiro
    overlay = quadro.copy()
    desenhar_retangulo_arredondado(overlay, (x0 - 8, y0 - 8), (x0 + tam + 8, y0 + tam + 8),
                                  (25, 30, 42), raio=14, espessura=-1)
    cv2.addWeighted(overlay, 0.70, quadro, 0.30, 0, quadro)

    # 2. Imagem de Dica (Gabarito) se ativada
    if jogo.mostrar_dica:
        dica_img = gerenciador.obter_imagem_redimensionada(jogo.fase_atual.imagem_nome, tam, tam)
        alvo_roi = quadro[y0:y0 + tam, x0:x0 + tam]
        cv2.addWeighted(dica_img, 0.35, alvo_roi, 0.65, 0, alvo_roi)

    # 3. Linhas da grade e slots
    linhas, colunas = jogo.fase_atual.linhas, jogo.fase_atual.colunas
    w_slot = tam / colunas
    h_slot = tam / linhas

    for s in jogo.slots:
        sx0 = int(round(s.x - s.largura / 2.0))
        sy0 = int(round(s.y - s.altura / 2.0))
        sx1 = int(round(s.x + s.largura / 2.0))
        sy1 = int(round(s.y + s.altura / 2.0))
        cv2.rectangle(quadro, (sx0, sy0), (sx1, sy1), (80, 100, 120), 1, cv2.LINE_AA)
        peca = jogo.peca_ativa
        if (peca is not None and peca.linha == s.linha and peca.coluna == s.coluna
                and peca.distancia_ao_slot() <= jogo.raio_snap):
            cv2.rectangle(quadro, (sx0 + 3, sy0 + 3), (sx1 - 3, sy1 - 3),
                          (80, 255, 120), 4, cv2.LINE_AA)


    # Moldura exterior com brilho
    desenhar_retangulo_arredondado(quadro, (x0 - 8, y0 - 8), (x0 + tam + 8, y0 + tam + 8),
                                  (140, 180, 220), raio=14, espessura=2)


def desenhar_pecas(quadro: np.ndarray, jogo: JogoQuebraCabeca,
                   gerenciador: GerenciadorPecasVisuais, cursor_pos: Optional[Tuple[float, float]]):
    """Renderiza todas as peças com sombras, destaques de hover e relevo."""
    fase = jogo.fase_atual
    w_quadro, h_quadro = quadro.shape[1], quadro.shape[0]

    for p in jogo.pecas:
        pw = int(round(p.largura))
        ph = int(round(p.altura))
        recorte = gerenciador.obter_recorte_peca(fase.imagem_nome, p.linha, p.coluna,
                                                fase.linhas, fase.colunas, pw, ph)

        # Se a peça estiver sendo segurada, aplica leve zoom e sombra projetada
        escala = 1.06 if p.segurada else 1.0
        desenho_w = int(round(pw * escala))
        desenho_h = int(round(ph * escala))

        if escala != 1.0:
            sprite = cv2.resize(recorte, (desenho_w, desenho_h), interpolation=cv2.INTER_LINEAR)
        else:
            sprite = recorte

        cx, cy = int(round(p.x)), int(round(p.y))
        x0 = cx - desenho_w // 2
        y0 = cy - desenho_h // 2

        # 1. Sombra projetada para efeito tridimensional de elevação
        if p.segurada:
            sombra_ox = 14
            sombra_oy = 16
            sx0 = max(0, x0 + sombra_ox)
            sy0 = max(0, y0 + sombra_oy)
            sx1 = min(w_quadro, x0 + desenho_w + sombra_ox)
            sy1 = min(h_quadro, y0 + desenho_h + sombra_oy)
            if sx1 > sx0 and sy1 > sy0:
                sombra_roi = quadro[sy0:sy1, sx0:sx1]
                sombra_cinza = (sombra_roi.astype(np.float32) * 0.45).astype(np.uint8)
                quadro[sy0:sy1, sx0:sx1] = sombra_cinza

        # 2. Renderização da peça sobreposta com recorte seguro nas bordas da tela
        rx0 = max(0, x0)
        ry0 = max(0, y0)
        rx1 = min(w_quadro, x0 + desenho_w)
        ry1 = min(h_quadro, y0 + desenho_h)

        if rx1 > rx0 and ry1 > ry0:
            sp_x0 = rx0 - x0
            sp_y0 = ry0 - y0
            sp_x1 = sp_x0 + (rx1 - rx0)
            sp_y1 = sp_y0 + (ry1 - ry0)

            recorte_rgb = sprite[sp_y0:sp_y1, sp_x0:sp_x1, :3]
            alfa = (sprite[sp_y0:sp_y1, sp_x0:sp_x1, 3:4].astype(np.float32) / 255.0)

            pedaco_fundo = quadro[ry0:ry1, rx0:rx1].astype(np.float32)
            mistura = recorte_rgb * alfa + pedaco_fundo * (1.0 - alfa)
            quadro[ry0:ry1, rx0:rx1] = mistura.astype(np.uint8)

            # 3. Contornos visuais de status
            is_hover = (cursor_pos is not None and not p.encaixada and not p.segurada and
                        p.contem_ponto(*cursor_pos))

            if p.encaixada:
                # Contorno verde sutil indicando peça travada no lugar certo
                cv2.rectangle(quadro, (rx0, ry0), (rx1, ry1), (40, 200, 80), 1, cv2.LINE_AA)
            elif p.segurada:
                # Borda brilhante dourada quando a mão está segurando
                cv2.rectangle(quadro, (rx0, ry0), (rx1, ry1), (0, 220, 255), 3, cv2.LINE_AA)
            elif is_hover:
                # Destaque ciano neon quando a mão passa por cima (hover)
                cv2.rectangle(quadro, (rx0, ry0), (rx1, ry1), (255, 230, 0), 2, cv2.LINE_AA)
            else:
                # Borda suave padrão
                cv2.rectangle(quadro, (rx0, ry0), (rx1, ry1), (80, 90, 110), 1, cv2.LINE_AA)


def desenhar_particulas(quadro: np.ndarray, particulas: List[Particula], t: float):
    """Desenha as partículas comemorativas de encaixe com brilho fading."""
    for p in particulas:
        idade = t - p.t0
        fator = max(0.0, 1.0 - idade / p.duracao)
        raio = max(1, int(round(p.raio * fator)))
        cor = tuple(int(c * fator) for c in p.cor)
        cx, cy = int(round(p.x)), int(round(p.y))
        if 0 <= cx < quadro.shape[1] and 0 <= cy < quadro.shape[0]:
            cv2.circle(quadro, (cx, cy), raio, cor, -1, cv2.LINE_AA)


def desenhar_botoes(quadro: np.ndarray, botoes: List[BotaoVirtual], texto: TextoRender):
    """Desenha botões interativos com efeito hover e barra circular de dwell click."""
    for btn in botoes:
        x, y, w, h = int(btn.x), int(btn.y), int(btn.w), int(btn.h)
        cor_fundo = (50, 70, 95) if btn.hover else (30, 40, 55)
        cor_borda = (0, 230, 255) if btn.hover else (100, 130, 160)

        desenhar_retangulo_arredondado(quadro, (x, y), (x + w, y + h), cor_fundo, raio=10, espessura=-1)
        desenhar_retangulo_arredondado(quadro, (x, y), (x + w, y + h), cor_borda, raio=10, espessura=2)

        # Se houver progresso de dwell, desenha barra de carga no rodapé do botão
        if btn.dwell_atual > 0:
            progresso = min(1.0, btn.dwell_atual / btn.tempo_dwell_necessario)
            prog_w = int((w - 8) * progresso)
            cv2.rectangle(quadro, (x + 4, y + h - 6), (x + 4 + prog_w, y + h - 3), (0, 255, 200), -1)

        cor_texto = (255, 255, 255) if btn.hover else (210, 220, 230)
        texto.add(btn.texto, (x + w // 2, y + h // 2), tamanho=18, cor=cor_texto, ancora="mm", negrito=True)


def desenhar_cursor_mao(quadro: np.ndarray, cursor_pos: Optional[Tuple[float, float]],
                        pinçando: bool, segurando_peca: bool, razao: float):
    """Desenha o cursor estilizado no ponto de pega entre os dedos."""
    if cursor_pos is None:
        return

    cx, cy = int(round(cursor_pos[0])), int(round(cursor_pos[1]))
    w_quadro, h_quadro = quadro.shape[1], quadro.shape[0]
    if not (0 <= cx < w_quadro and 0 <= cy < h_quadro):
        return

    if pinçando:
        cor_cursor = (0, 215, 255) if segurando_peca else (0, 240, 200)
        raio = 14
        cv2.circle(quadro, (cx, cy), raio, (20, 20, 20), 4, cv2.LINE_AA)
        cv2.circle(quadro, (cx, cy), raio, cor_cursor, 2, cv2.LINE_AA)
        cv2.circle(quadro, (cx, cy), 6, cor_cursor, -1, cv2.LINE_AA)
        cv2.line(quadro, (cx - 18, cy), (cx + 18, cy), cor_cursor, 2, cv2.LINE_AA)
        cv2.line(quadro, (cx, cy - 18), (cx, cy + 18), cor_cursor, 2, cv2.LINE_AA)
    else:
        cor_cursor = (80, 240, 100)
        raio = 18
        cv2.circle(quadro, (cx, cy), raio, (20, 20, 20), 4, cv2.LINE_AA)
        cv2.circle(quadro, (cx, cy), raio, cor_cursor, 2, cv2.LINE_AA)
        cv2.circle(quadro, (cx, cy), 4, cor_cursor, -1, cv2.LINE_AA)


def desenhar_hud_completo(quadro: np.ndarray, jogo: JogoQuebraCabeca, texto: TextoRender,
                          mao_detectada: bool, cursor_pos: Optional[Tuple[float, float]],
                          fps: float, depurar: bool, taxa_deteccao: float):
    """Renderiza todas as informações do jogo, status da mão, cronômetro e mensagens."""
    h, w = quadro.shape[:2]
    fase = jogo.fase_atual

    # Painel superior com título, tempo e pontuação
    texto.add(fase.titulo, (w // 2, 28), tamanho=24, cor=(255, 255, 255), ancora="mm", negrito=True)

    # Status de Peças Encaixadas
    total_p = len(jogo.pecas)
    texto.add(f"Encaixadas: {jogo.pecas_encaixadas}/{total_p}", (w * 0.72, jogo.tabuleiro_y0 - 24),
              tamanho=20, cor=(100, 230, 255), ancora="mm", negrito=True)

    # Cronômetro e Pontos
    minutos = int(jogo.tempo_fase // 60)
    segundos = int(jogo.tempo_fase % 60)
    tempo_fmt = f"{minutos:02d}:{segundos:02d}"
    texto.add(f"Tempo: {tempo_fmt}", (w - 18, 22), tamanho=22, cor=(240, 240, 180), ancora="ra", negrito=True)
    texto.add(f"Pontos: {jogo.pontos}", (w - 18, 52), tamanho=22, cor=(120, 255, 160), ancora="ra", negrito=True)

    # Mensagem de alerta se a mão não for detectada
    if not mao_detectada:
        overlay = quadro.copy()
        cv2.rectangle(overlay, (w // 2 - 220, h - 80), (w // 2 + 220, h - 30), (20, 25, 45), -1)
        cv2.addWeighted(overlay, 0.75, quadro, 0.25, 0, quadro)
        desenhar_retangulo_arredondado(quadro, (w // 2 - 220, h - 80), (w // 2 + 220, h - 30),
                                      (80, 160, 255), raio=8, espessura=2)
        texto.add("Mostre a mão para a câmera", (w // 2, h - 55), tamanho=20,
                  cor=(255, 220, 120), ancora="mm", negrito=True)

    # Banner comemorativo de Fase Concluída ou Vitória Final
    if jogo.estado in ("fase_concluida", "vitoria"):
        overlay = quadro.copy()
        cx, cy = int(jogo.tabuleiro_cx), int(jogo.tabuleiro_cy)
        cv2.rectangle(overlay, (cx - 160, cy - 70), (cx + 160, cy + 70), (15, 25, 35), -1)
        cv2.addWeighted(overlay, 0.85, quadro, 0.15, 0, quadro)
        desenhar_retangulo_arredondado(quadro, (cx - 160, cy - 70), (cx + 160, cy + 70),
                                      (0, 240, 180), raio=14, espessura=3)

        titulo_vit = "Fase Concluída!" if jogo.estado == "fase_concluida" else "Parabéns, Você Venceu!"
        texto.add(titulo_vit, (cx, cy - 25), tamanho=26, cor=(255, 240, 100), ancora="mm", negrito=True)
        sub_msg = "Clique em Próxima Fase" if jogo.estado == "fase_concluida" else f"Pontuação Final: {jogo.pontos}"
        texto.add(sub_msg, (cx, cy + 20), tamanho=19, cor=(200, 255, 220), ancora="mm", negrito=False)

    # Painel de depuração no rodapé (tecla 'd')
    if depurar:
        status_mao = "Mão OK" if mao_detectada else "Sem Mão"
        segurando = "Segurando Peça" if jogo.peca_ativa else "Livre"
        msg_dep = (f"{status_mao} | {segurando} | FPS: {fps:.0f} | "
                   f"Detecção: {100 * taxa_deteccao:.0f}%")
        texto.add(msg_dep, (20, h - 16), tamanho=16, cor=(220, 220, 220), ancora="la", negrito=False)

