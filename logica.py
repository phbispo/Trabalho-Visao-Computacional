"""Lógica pura do Quebra-Cabeça Interativo, sem dependência de OpenCV ou MediaPipe.

Trabalha apenas com estruturas de dados, geometria 2D, coordenadas em pixels e
tempo contínuo em segundos. Isso torna as regras 100% testáveis com entradas sintéticas.
"""
import math
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


def dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Calcula a distância euclidiana entre dois pontos 2D."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def razao_pinca(mao) -> float:
    """Calcula a razão da distância ponta do polegar (4) ao indicador (8)

    dividida pelo comprimento da palma (pulso 0 à base do dedo médio 9).
    A normalização torna o gesto invariante à distância da mão em relação à câmera.
    """
    if mao is None or len(mao) < 10:
        return 1.0
    dist_pinca = dist(mao[4], mao[8])
    tam_mao = max(dist(mao[0], mao[9]), 1e-5)
    return dist_pinca / tam_mao


@dataclass
class Peca:
    """Representa uma peça do quebra-cabeça."""
    id: int
    linha: int
    coluna: int
    x: float
    y: float
    largura: float
    altura: float
    slot_x: float
    slot_y: float
    origem_x: float
    origem_y: float
    encaixada: bool = False
    segurada: bool = False
    offset_x: float = 0.0
    offset_y: float = 0.0
    animando: bool = False
    alvo_anim_x: float = 0.0
    alvo_anim_y: float = 0.0

    def contem_ponto(self, px: float, py: float) -> bool:
        """Verifica se o ponto (px, py) está dentro dos limites da peça."""
        meia_largura = self.largura / 2.0
        meia_altura = self.altura / 2.0
        return (self.x - meia_largura <= px <= self.x + meia_largura and
                self.y - meia_altura <= py <= self.y + meia_altura)

    def distancia_ao_slot(self) -> float:
        """Distância euclidiana atual entre a peça e a sua posição correta no tabuleiro."""
        return dist((self.x, self.y), (self.slot_x, self.slot_y))


@dataclass
class Slot:
    """Representa uma posição correta de encaixe no tabuleiro."""
    linha: int
    coluna: int
    x: float
    y: float
    largura: float
    altura: float
    ocupado: bool = False


@dataclass
class Particula:
    """Partícula brilhante emitida ao encaixar uma peça."""
    x: float
    y: float
    vx: float
    vy: float
    cor: Tuple[int, int, int]
    raio: float
    t0: float
    duracao: float = 0.7


class CursorMao:
    """Interpreta as posições brutas da mão, aplicando suavização e máquina de estados da pinça.

    Utiliza histerese e contagem consecutiva (debounce) para garantir que
    ações de pegar e soltar peças sejam firmes, estáveis e livres de jitter.
    """

    def __init__(self, alpha: float = 0.5, limiar_fechar: float = 0.32,
                 limiar_abrir: float = 0.52, debounce_quadros: int = 2,
                 tolerancia_perda_s: float = 0.40):
        self.alpha = alpha
        self.limiar_fechar = limiar_fechar
        self.limiar_abrir = limiar_abrir
        self.debounce_quadros = debounce_quadros
        self.tolerancia_perda_s = tolerancia_perda_s

        self.pos: Optional[Tuple[float, float]] = None
        self.pinçando: bool = False
        self._quadros_fechados: int = 0
        self._quadros_abertos: int = 0
        self._ultimo_t_visto: float = -math.inf
        self.razao_atual: float = 1.0
        self.ativa: bool = False
        self.detectada: bool = False

    def atualizar(self, ponto_bruto: Optional[Tuple[float, float]],
                  razao: Optional[float], t: float) -> Tuple[bool, bool]:
        """Atualiza a posição suavizada e o estado da pinça.

        Retorna:
            (acabou_de_fechar, acabou_de_abrir)
        """
        acabou_de_fechar = False
        acabou_de_abrir = False
        self.detectada = ponto_bruto is not None and razao is not None

        if ponto_bruto is None or razao is None:
            if t - self._ultimo_t_visto > self.tolerancia_perda_s:
                self.ativa = False
                self.pos = None
                self._quadros_fechados = 0
                self._quadros_abertos = 0
                if self.pinçando:
                    self.pinçando = False
                    acabou_de_abrir = True
            return acabou_de_fechar, acabou_de_abrir

        # Mão detectada
        self._ultimo_t_visto = t
        self.razao_atual = razao

        # Suavização exponencial do cursor para eliminar tremulação
        if self.pos is None or not self.ativa:
            self.pos = ponto_bruto
        else:
            self.pos = (
                self.alpha * ponto_bruto[0] + (1.0 - self.alpha) * self.pos[0],
                self.alpha * ponto_bruto[1] + (1.0 - self.alpha) * self.pos[1],
            )
        self.ativa = True

        # Máquina de estados da pinça com histerese e debounce
        if razao < self.limiar_fechar:
            self._quadros_abertos = 0
            self._quadros_fechados += 1
            if not self.pinçando and self._quadros_fechados >= self.debounce_quadros:
                self.pinçando = True
                acabou_de_fechar = True
        elif razao > self.limiar_abrir:
            self._quadros_fechados = 0
            self._quadros_abertos += 1
            if self.pinçando and self._quadros_abertos >= self.debounce_quadros:
                self.pinçando = False
                acabou_de_abrir = True
        else:
            # Região da histerese: preserva o estado atual sem oscilar
            self._quadros_fechados = 0
            self._quadros_abertos = 0

        return acabou_de_fechar, acabou_de_abrir


@dataclass
class BotaoVirtual:
    """Botão interativo acionável tanto por pinça quanto por tempo de repouso (dwell click)."""
    id: str
    texto: str
    x: float
    y: float
    w: float
    h: float
    tempo_dwell_necessario: float = 1.0
    dwell_atual: float = 0.0
    hover: bool = False
    _dwell_disparado: bool = False

    def contem_ponto(self, px: float, py: float) -> bool:
        return (self.x <= px <= self.x + self.w and
                self.y <= py <= self.y + self.h)

    def atualizar(self, cursor_pos: Optional[Tuple[float, float]],
                  acabou_de_fechar: bool, dt: float) -> bool:
        """Retorna True se o botão foi acionado por pinça ou por dwell."""
        if cursor_pos is None:
            self.hover = False
            self._dwell_disparado = False
            self.dwell_atual = 0.0
            return False

        self.hover = self.contem_ponto(*cursor_pos)
        if not self.hover:
            self._dwell_disparado = False
            self.dwell_atual = 0.0
            return False

        # Acionamento imediato por gesto de pinça
        if acabou_de_fechar:
            self.dwell_atual = 0.0
            return True

        if self._dwell_disparado:
            return False

        # Acionamento gradual por permanência (dwell)
        self.dwell_atual += dt
        if self.dwell_atual >= self.tempo_dwell_necessario:
            self._dwell_disparado = True
            self.dwell_atual = 0.0
            return True

        return False


@dataclass
class DefinicaoFase:
    """Configurações de cada nível do jogo."""
    numero: int
    titulo: str
    imagem_nome: str
    linhas: int
    colunas: int


FASES_PADRAO = [
    DefinicaoFase(1, "Fase 1: Espaço Cósmico (2x2)", "puzzle_espaco.png", 2, 2),
    DefinicaoFase(2, "Fase 2: Floresta Mágica (3x2)", "puzzle_floresta.png", 2, 3),
    DefinicaoFase(3, "Fase 3: Robô do Futuro (3x3)", "puzzle_robot.png", 3, 3),
]


class JogoQuebraCabeca:
    """Gerenciador de regras, peças, tabuleiro, fases e máquina de estados do jogo."""

    def __init__(self, largura_tela: int = 960, altura_tela: int = 540,
                 fases: Optional[List[DefinicaoFase]] = None, seed: Optional[int] = None):
        self.w = largura_tela
        self.h = altura_tela
        self.fases = fases or FASES_PADRAO
        self.rng = random.Random(seed)

        self.fase_idx: int = 0
        self.estado: str = "jogando"  # jogando -> fase_concluida -> vitoria
        self.pontos: int = 0
        self.pecas_encaixadas: int = 0
        self.tempo_fase: float = 0.0
        self.tempo_total: float = 0.0
        self.mostrar_dica: bool = False
        self.raio_snap: float = 55.0  # tolerância em pixels para encaixar

        self.pecas: List[Peca] = []
        self.slots: List[Slot] = []
        self.particulas: List[Particula] = []
        self.peca_ativa: Optional[Peca] = None

        # Geometria do tabuleiro e bandeja
        self._definir_geometria()
        self._criar_botoes()
        self.iniciar_fase(0)

    def _definir_geometria(self):
        """Define as áreas do tabuleiro alvo e da bandeja de peças."""
        # Tabuleiro alvo fica à direita
        self.tabuleiro_tamanho = min(self.h * 0.72, self.w * 0.42)
        self.tabuleiro_cx = self.w * 0.72
        self.tabuleiro_cy = self.h * 0.52
        self.tabuleiro_x0 = self.tabuleiro_cx - self.tabuleiro_tamanho / 2.0
        self.tabuleiro_y0 = self.tabuleiro_cy - self.tabuleiro_tamanho / 2.0

        # Área de dispersão da bandeja (à esquerda)
        self.bandeja_x_min = self.w * 0.06
        self.bandeja_x_max = self.w * 0.46
        self.bandeja_y_min = self.h * 0.20
        self.bandeja_y_max = self.h * 0.86

    def _criar_botoes(self):
        """Inicializa os botões virtuais interativos no topo e rodapé."""
        bw, bh = 130, 42
        y_topo = 18
        self.botoes = [
            BotaoVirtual("dica", "Dica [H]", self.w * 0.50 - bw / 2, y_topo, bw, bh),
            BotaoVirtual("embaralhar", "Embaralhar", self.w * 0.06, y_topo, bw, bh),
            BotaoVirtual("reiniciar", "Reiniciar", self.w * 0.06 + bw + 15, y_topo, bw, bh),
            BotaoVirtual("proxima", "Próxima Fase >>", self.w - 195, y_topo, 180, bh),
        ]

    @property
    def fase_atual(self) -> DefinicaoFase:
        return self.fases[self.fase_idx]

    def iniciar_fase(self, fase_idx: int):
        """Prepara o tabuleiro, slots e peças para a fase indicada."""
        self.fase_idx = max(0, min(fase_idx, len(self.fases) - 1))
        fase = self.fase_atual
        self.estado = "jogando"
        self.pecas_encaixadas = 0
        self.tempo_fase = 0.0
        self.mostrar_dica = False
        self.peca_ativa = None
        self.particulas.clear()

        linhas, colunas = fase.linhas, fase.colunas
        largura_peca = self.tabuleiro_tamanho / colunas
        altura_peca = self.tabuleiro_tamanho / linhas

        # Cria os slots de encaixe no tabuleiro
        self.slots = []
        for l in range(linhas):
            for c in range(colunas):
                cx = self.tabuleiro_x0 + (c + 0.5) * largura_peca
                cy = self.tabuleiro_y0 + (l + 0.5) * altura_peca
                self.slots.append(Slot(l, c, cx, cy, largura_peca, altura_peca))

        # Cria as peças e espalha na bandeja
        self.pecas = []
        posicoes_bandeja = self._gerar_posicoes_bandeja(linhas * colunas, largura_peca, altura_peca)

        peca_id = 0
        for l in range(linhas):
            for c in range(colunas):
                slot = self.slots[peca_id]
                bx, by = posicoes_bandeja[peca_id]
                self.pecas.append(Peca(
                    id=peca_id,
                    linha=l,
                    coluna=c,
                    x=bx,
                    y=by,
                    largura=largura_peca,
                    altura=altura_peca,
                    slot_x=slot.x,
                    slot_y=slot.y,
                    origem_x=bx,
                    origem_y=by,
                    encaixada=False,
                    segurada=False,
                ))
                peca_id += 1

    def _gerar_posicoes_bandeja(self, total_pecas: int, largura_p: float, altura_p: float) -> List[Tuple[float, float]]:
        """Distribui as peças na bandeja esquerda de forma organizada e com leve jitter estético."""
        posicoes = []
        # Organiza em uma grade de bandeja de 2 ou 3 colunas
        cols_bandeja = 2 if total_pecas <= 6 else 3
        linhas_bandeja = math.ceil(total_pecas / cols_bandeja)

        passo_x = (self.bandeja_x_max - self.bandeja_x_min) / cols_bandeja
        passo_y = (self.bandeja_y_max - self.bandeja_y_min) / linhas_bandeja

        indices = list(range(total_pecas))
        self.rng.shuffle(indices)

        for idx in range(total_pecas):
            lb = idx // cols_bandeja
            cb = idx % cols_bandeja
            cx = self.bandeja_x_min + (cb + 0.5) * passo_x + self.rng.uniform(-10, 10)
            cy = self.bandeja_y_min + (lb + 0.5) * passo_y + self.rng.uniform(-10, 10)
            posicoes.append((cx, cy))

        # Reordena conforme shuffle
        return [posicoes[i] for i in indices]

    def embaralhar_pecas_soltas(self):
        """Retorna todas as peças ainda não encaixadas para novas posições na bandeja."""
        soltas = [p for p in self.pecas if not p.encaixada and not p.segurada]
        if not soltas:
            return
        largura_p = soltas[0].largura
        altura_p = soltas[0].altura
        novas_pos = self._gerar_posicoes_bandeja(len(soltas), largura_p, altura_p)
        for p, (nx, ny) in zip(soltas, novas_pos):
            p.origem_x = nx
            p.origem_y = ny
            p.animando = True
            p.alvo_anim_x = nx
            p.alvo_anim_y = ny

    def atualizar(self, cursor: CursorMao, t: float, dt: float):
        """Avança o ciclo principal de lógica: pinça, arrasto, encaixe, animações e botões."""
        if self.estado == "jogando":
            self.tempo_fase += dt
            self.tempo_total += dt

        # 1. Animações de peças voltando suavemente à bandeja
        for p in self.pecas:
            if p.animando:
                fator = min(1.0, 14.0 * dt)
                p.x += (p.alvo_anim_x - p.x) * fator
                p.y += (p.alvo_anim_y - p.y) * fator
                if dist((p.x, p.y), (p.alvo_anim_x, p.alvo_anim_y)) < 2.0:
                    p.x, p.y = p.alvo_anim_x, p.alvo_anim_y
                    p.animando = False

        # 2. Atualização e expiração de partículas
        for part in list(self.particulas):
            part.x += part.vx * dt
            part.y += part.vy * dt
            part.vy += 80.0 * dt  # leve gravidade para efeito cascata
            if t - part.t0 > part.duracao:
                self.particulas.remove(part)

        # 3. Interação com Botões Virtuais
        pos_botao = cursor.pos if cursor.detectada and self.peca_ativa is None else None
        if pos_botao is None:
            for btn in self.botoes:
                btn.atualizar(None, False, dt)
        else:
            acabou_de_fechar = (cursor.pinçando and self.peca_ativa is None and
                                getattr(cursor, "_quadros_fechados", 0) == cursor.debounce_quadros)
            for btn in self.botoes:
                # O botão de próxima fase só funciona se a fase foi concluída
                if btn.id == "proxima" and self.estado != "fase_concluida":
                    continue
                if btn.atualizar(pos_botao, acabou_de_fechar, dt):
                    self._executar_acao_botao(btn.id)
                    return

        # 4. Comportamento se a mão for perdida durante o arrasto
        if not cursor.ativa:
            if self.peca_ativa is not None:
                self.peca_ativa.segurada = False
                self._tentar_encaixar(self.peca_ativa, t)
                self.peca_ativa = None
            return

        # 5. Lógica de Pegar e Arrastar com a Pinça
        px, py = cursor.pos

        # Se já está segurando uma peça
        if self.peca_ativa is not None:
            if cursor.pinçando:
                # Segue o movimento da mão suavemente
                self.peca_ativa.x = px + self.peca_ativa.offset_x
                self.peca_ativa.y = py + self.peca_ativa.offset_y
            else:
                # Mão abriu: SOLTA a peça!
                self.peca_ativa.segurada = False
                self._tentar_encaixar(self.peca_ativa, t)
                self.peca_ativa = None

        # Se NÃO está segurando peça e acabou de fechar a pinça
        elif cursor.pinçando:
            # Procura por peças livres sob o cursor (da última renderizada para a primeira)
            for p in reversed(self.pecas):
                if not p.encaixada and p.contem_ponto(px, py):
                    self.peca_ativa = p
                    p.segurada = True
                    p.animando = False
                    p.offset_x = p.x - px
                    p.offset_y = p.y - py
                    # Coloca a peça no final da lista para desenhá-la no topo (Z-order)
                    self.pecas.remove(p)
                    self.pecas.append(p)
                    break

    def _tentar_encaixar(self, peca: Peca, t: float):
        """Verifica se a peça solta está suficientemente perto do slot correto (Snap Magnético)."""
        d = peca.distancia_ao_slot()
        if d <= self.raio_snap:
            # ENCAIXE PERFEITO!
            peca.x = peca.slot_x
            peca.y = peca.slot_y
            peca.encaixada = True
            self.pecas_encaixadas += 1

            # Pontuação: 100 pontos base + bônus de agilidade
            bonus = max(0, int(150 - self.tempo_fase * 3))
            self.pontos += (100 + bonus)

            # Emite explosão de partículas comemorativas no centro do slot
            self._emitir_particulas_snap(peca.slot_x, peca.slot_y, t)

            # Verifica vitória da fase
            if self.pecas_encaixadas >= len(self.pecas):
                if self.fase_idx + 1 < len(self.fases):
                    self.estado = "fase_concluida"
                else:
                    self.estado = "vitoria"
                self._emitir_particulas_vitoria(t)
        else:
            # Não encaixou: se estiver fora dos limites da tela, retorna para a bandeja
            if (peca.x < 20 or peca.x > self.w - 20 or
                    peca.y < 20 or peca.y > self.h - 20):
                peca.animando = True
                peca.alvo_anim_x = peca.origem_x
                peca.alvo_anim_y = peca.origem_y

    def _emitir_particulas_snap(self, cx: float, cy: float, t: float, num_particulas: int = 30):
        """Gera partículas douradas e esmeralda ao redor do slot de encaixe."""
        cores = [
            (255, 215, 0),   # Ouro
            (80, 255, 120),  # Verde esmeralda
            (0, 240, 255),   # Ciano
            (255, 255, 255), # Branco
        ]
        for _ in range(num_particulas):
            ang = self.rng.uniform(0, 2 * math.pi)
            vel = self.rng.uniform(60, 260)
            vx = math.cos(ang) * vel
            vy = math.sin(ang) * vel
            self.particulas.append(Particula(
                x=cx,
                y=cy,
                vx=vx,
                vy=vy,
                cor=self.rng.choice(cores),
                raio=self.rng.uniform(2.5, 5.5),
                t0=t,
                duracao=self.rng.uniform(0.4, 0.7),
            ))

    def _emitir_particulas_vitoria(self, t: float):
        """Celebração ao completar o puzzle inteiro com confetes coloridos."""
        for _ in range(70):
            cx = self.tabuleiro_cx + self.rng.uniform(-self.tabuleiro_tamanho / 2, self.tabuleiro_tamanho / 2)
            cy = self.tabuleiro_cy + self.rng.uniform(-self.tabuleiro_tamanho / 2, self.tabuleiro_tamanho / 2)
            self._emitir_particulas_snap(cx, cy, t, num_particulas=1)

    def _executar_acao_botao(self, botao_id: str):
        """Executa a ação correspondente ao botão acionado."""
        if botao_id == "dica":
            self.mostrar_dica = not self.mostrar_dica
        elif botao_id == "embaralhar":
            self.embaralhar_pecas_soltas()
        elif botao_id == "reiniciar":
            self.iniciar_fase(self.fase_idx)
        elif botao_id == "proxima":
            if self.fase_idx + 1 < len(self.fases):
                self.iniciar_fase(self.fase_idx + 1)

