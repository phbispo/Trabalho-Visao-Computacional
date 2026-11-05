"""Entrada de vídeo e rastreamento de mãos com MediaPipe (API Tasks).

Este módulo isola a captura de vídeo (webcam/arquivo) e a inferência do
MediaPipe Hand Landmarker. O restante do jogo recebe apenas coordenadas em pixels.
"""
import argparse
import time
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

URL_MODELO = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)
CAMINHO_MODELO = Path(__file__).with_name("hand_landmarker.task")

# Landmarks principais da mão segundo a topologia do MediaPipe
PULSO = 0
POLEGAR_BASE = 2
POLEGAR_PONTA = 4
INDICADOR_BASE = 5
INDICADOR_PONTA = 8
MEDIO_BASE = 9
MEDIO_PONTA = 12
MINIMO_BASE = 17

# Esqueleto da mão conectando os 21 pontos
CONEXOES = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # polegar
    (0, 5), (5, 6), (6, 7), (7, 8),          # indicador
    (5, 9), (9, 10), (10, 11), (11, 12),     # médio
    (9, 13), (13, 14), (14, 15), (15, 16),   # anelar
    (13, 17), (17, 18), (18, 19), (19, 20),  # mínimo
    (0, 17),                                 # base da palma
]


def baixar_modelo(destino=CAMINHO_MODELO):
    """Garante a presença do arquivo do modelo .task (8 MB)."""
    if not destino.exists():
        print(f"Baixando modelo {destino.name}...")
        urllib.request.urlretrieve(URL_MODELO, destino)
    return destino


class Rastreador:
    """Envolve o HandLandmarker da API Tasks e retorna landmarks em pixels."""

    def __init__(self, num_maos=1, confianca=0.35):
        modelo_path = str(baixar_modelo())
        opcoes = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=modelo_path),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=num_maos,
            min_hand_detection_confidence=confianca,
            min_hand_presence_confidence=confianca,
            min_tracking_confidence=confianca,
        )
        self.detector = vision.HandLandmarker.create_from_options(opcoes)
        self._ultimo_ms = -1

    def processar(self, quadro_bgr, t):
        """Processa o quadro atual no tempo `t` (em segundos).

        Retorna lista de arrays numpy de formato (21, 2) com posições em pixels.
        """
        ms = max(int(t * 1000), self._ultimo_ms + 1)
        self._ultimo_ms = ms

        rgb = cv2.cvtColor(quadro_bgr, cv2.COLOR_BGR2RGB)
        imagem = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        resultado = self.detector.detect_for_video(imagem, ms)

        h, w = quadro_bgr.shape[:2]
        escala = np.array([w, h], dtype=float)

        return [
            np.array([[p.x, p.y] for p in mao], dtype=float) * escala
            for mao in resultado.hand_landmarks
        ]


def desenhar_mao(quadro, mao, cor_ossos=(80, 220, 120), cor_pontos=(0, 255, 255)):
    """Desenha as conexões e articulações da mão com suavização visual."""
    for a, b in CONEXOES:
        pt_a = tuple(mao[a].astype(int))
        pt_b = tuple(mao[b].astype(int))
        cv2.line(quadro, pt_a, pt_b, (20, 20, 20), 4, cv2.LINE_AA)
        cv2.line(quadro, pt_a, pt_b, cor_ossos, 2, cv2.LINE_AA)

    for i, ponto in enumerate(mao):
        pt = tuple(ponto.astype(int))
        raio = 5 if i in (POLEGAR_PONTA, INDICADOR_PONTA) else 3
        cv2.circle(quadro, pt, raio + 1, (20, 20, 20), -1, cv2.LINE_AA)
        cv2.circle(quadro, pt, raio, cor_pontos, -1, cv2.LINE_AA)


def abrir_fonte(camera=0, video=None, largura=960, espelhar=True, fps_pedido=60):
    """Gerador que fornece pares (quadro_bgr, tempo_t).

    Configura webcam em MJPG com buffer mínimo para baixa latência.
    """
    cap = cv2.VideoCapture(video) if video else cv2.VideoCapture(camera)
    if not cap.isOpened():
        origem = f"o arquivo de vídeo '{video}'" if video else f"a webcam de índice {camera}"
        raise SystemExit(f"Erro: Não foi possível abrir {origem}.")

    if not video:
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, largura)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, round(largura * 9 / 16))
        cap.set(cv2.CAP_PROP_FPS, fps_pedido)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    inicio = time.perf_counter()
    i = 0

    try:
        while True:
            ok, quadro = cap.read()
            if not ok:
                return

            h, w = quadro.shape[:2]
            if w != largura:
                altura_nova = round(h * largura / w)
                quadro = cv2.resize(quadro, (largura, altura_nova), interpolation=cv2.INTER_LINEAR)

            if espelhar:
                quadro = cv2.flip(quadro, 1)

            t = i / fps if video else (time.perf_counter() - inicio)
            i += 1
            yield quadro, t
    finally:
        cap.release()


def argumentos(descricao, extras=None):
    """Configuração padrão da CLI do projeto."""
    ap = argparse.ArgumentParser(description=descricao)
    ap.add_argument("--camera", type=int, default=0, help="Índice da webcam (padrão: 0)")
    ap.add_argument("--video", help="Caminho de um arquivo de vídeo para teste")
    ap.add_argument("--largura", type=int, default=960, help="Largura do quadro em pixels (padrão: 960)")
    ap.add_argument("--fps", type=int, default=60, help="Taxa pedida à webcam (padrão: 60)")
    ap.add_argument("--espelhar", action=argparse.BooleanOptionalAction, default=None,
                    help="Espelhar imagem horizontalmente (padrão: sim na webcam)")
    ap.add_argument("--saida", help="Gravar resultado em vídeo MP4 sem abrir janela")
    ap.add_argument("--max-quadros", type=int, help="Encerrar após N quadros")
    if extras:
        extras(ap)
    return ap.parse_args()


def fonte_de(args):
    """Abre a fonte apropriada conforme os argumentos CLI."""
    espelhar = (args.video is None) if (args.espelhar is None) else args.espelhar
    return abrir_fonte(args.camera, args.video, args.largura, espelhar, args.fps)


class Saida:
    """Gerencia a exibição na janela OpenCV ou gravação de saída em MP4."""

    def __init__(self, args, nome="Quebra-Cabeca Interativo", fps=30):
        self.nome = nome
        self.fps = fps
        self.caminho = args.saida
        self.gravador = None
        self.tecla = -1

    def mostrar(self, quadro):
        """Mostra o quadro na janela e/ou grava no arquivo MP4. Retorna False se o usuário fechou."""
        if self.caminho:
            if self.gravador is None:
                h, w = quadro.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                self.gravador = cv2.VideoWriter(self.caminho, fourcc, self.fps, (w, h))
            self.gravador.write(quadro)
            return True

        cv2.imshow(self.nome, quadro)
        self.tecla = cv2.waitKey(1) & 0xFF
        if self.tecla in (ord("q"), 27):  # q ou ESC
            return False
        return True

    def fechar(self):
        """Fecha os recursos da janela e do gravador."""
        if self.gravador:
            self.gravador.release()
            print(f"Vídeo gravado salvo em: {self.caminho}")
        cv2.destroyAllWindows()

