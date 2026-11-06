# /// script
# requires-python = ">=3.10"
# dependencies = ["mediapipe", "opencv-python", "numpy", "pillow"]
# ///
"""Quebra-Cabeça Interativo com Visão Computacional (MediaPipe Hand Landmarker).

Pegue e arraste as peças com o gesto de pinça entre o polegar e o indicador.
Encaixe cada peça no seu respectivo slot no tabuleiro à direita.

Controles e Teclas:
  q / ESC : Sair da aplicação
  e       : Exibir / ocultar esqueleto da mão
  d       : Exibir / ocultar informações de depuração
  r       : Reiniciar fase atual
  h       : Exibir / ocultar dica translúcida (gabarito)
  b       : Embaralhar peças soltas na bandeja
  n       : Avançar diretamente para a próxima fase
"""
import time
import cv2
import numpy as np

from logica import CursorMao, JogoQuebraCabeca, razao_pinca
from maos import (
    INDICADOR_PONTA,
    POLEGAR_PONTA,
    Rastreador,
    Saida,
    argumentos,
    desenhar_mao,
    fonte_de,
)
from visual import (
    GerenciadorPecasVisuais,
    TextoRender,
    desenhar_botoes,
    desenhar_cursor_mao,
    desenhar_hud_completo,
    desenhar_particulas,
    desenhar_pecas,
    desenhar_tabuleiro,
)


def main():
    args = argumentos(
        __doc__.splitlines()[0],
        extras=lambda ap: ap.add_argument(
            "--fase", type=int, default=1, help="Fase inicial (1, 2 ou 3)"
        ),
    )

    rastreador = Rastreador(num_maos=1, confianca=0.35)
    gerenciador_visuais = GerenciadorPecasVisuais()
    texto = TextoRender()
    cursor = CursorMao(alpha=0.5, limiar_fechar=0.32, limiar_abrir=0.52)
    saida = Saida(args, "Quebra-Cabeca Interativo com Visao Computacional")

    jogo = None
    esqueleto = True
    depurar = True
    t_ant = 0.0
    fps = 30.0
    taxa_deteccao = 1.0

    try:
        quadro_count = 0
        for quadro, t in fonte_de(args):
            quadro_count += 1
            if args.max_quadros and quadro_count > args.max_quadros:
                break

            h, w = quadro.shape[:2]
            if jogo is None:
                jogo = JogoQuebraCabeca(largura_tela=w, altura_tela=h)
                if args.fase in (1, 2, 3):
                    jogo.iniciar_fase(args.fase - 1)

            dt = min(max(t - t_ant, 1e-3), 0.1)
            fps = 0.90 * fps + 0.10 / dt
            t_ant = t

            # -----------------------------------------------------------------
            # 1. PERCEPÇÃO: MediaPipe detecta os 21 pontos da mão no quadro
            # -----------------------------------------------------------------
            maos = rastreador.processar(quadro, t)
            mao = maos[0] if maos else None
            taxa_deteccao = 0.96 * taxa_deteccao + 0.04 * (mao is not None)

            # -----------------------------------------------------------------
            # 2. INTERPRETAÇÃO: Ponto médio dos dedos vira cursor; pinça vira clique
            # -----------------------------------------------------------------
            if mao is not None:
                ponto_pinça = (
                    (mao[POLEGAR_PONTA][0] + mao[INDICADOR_PONTA][0]) / 2.0,
                    (mao[POLEGAR_PONTA][1] + mao[INDICADOR_PONTA][1]) / 2.0,
                )
                razao = razao_pinca(mao)
            else:
                ponto_pinça = None
                razao = None

            cursor.atualizar(ponto_pinça, razao, t)

            # -----------------------------------------------------------------
            # 3. JOGO: Regras do quebra-cabeça, arrasto, snap magnético e botões
            # -----------------------------------------------------------------
            jogo.atualizar(cursor, t, dt)

            # -----------------------------------------------------------------
            # 4. SAÍDA VISUAL: Renderização em camadas com acabamento profissional
            # -----------------------------------------------------------------
            # Escurece levemente o fundo da câmera para dar destaque às peças e tabuleiro
            quadro[:] = (quadro * 0.58).astype(np.uint8)

            # Esqueleto da mão
            if esqueleto and mao is not None:
                desenhar_mao(quadro, mao)

            # Tabuleiro alvo e grade
            desenhar_tabuleiro(quadro, jogo, gerenciador_visuais)

            # Peças com sombras projetadas e relevo
            desenhar_pecas(quadro, jogo, gerenciador_visuais, cursor.pos)

            # Partículas de comemoração ao encaixar
            desenhar_particulas(quadro, jogo.particulas, t)

            # Botões virtuais na tela
            botoes_visiveis = [
                btn for btn in jogo.botoes
                if btn.id != "proxima" or jogo.estado == "fase_concluida"
            ]
            desenhar_botoes(quadro, botoes_visiveis, texto)

            # Cursor da mão no ponto de pinça
            desenhar_cursor_mao(
                quadro,
                cursor.pos,
                cursor.pinçando,
                jogo.peca_ativa is not None,
                cursor.razao_atual,
            )

            # HUD superior e depuração
            desenhar_hud_completo(
                quadro,
                jogo,
                texto,
                mao is not None,
                cursor.pos,
                fps,
                depurar,
                taxa_deteccao,
            )

            # Renderiza os textos tipográficos com Pillow
            texto.desenhar(quadro)

            # Atualiza a janela ou salva no vídeo
            if not saida.mostrar(quadro):
                break

            # Tratamento de teclas de atalho
            tecla = saida.tecla
            if tecla == ord("e"):
                esqueleto = not esqueleto
            elif tecla == ord("d"):
                depurar = not depurar
            elif tecla == ord("r"):
                jogo.iniciar_fase(jogo.fase_idx)
            elif tecla == ord("h"):
                jogo.mostrar_dica = not jogo.mostrar_dica
            elif tecla == ord("b"):
                jogo.embaralhar_pecas_soltas()
            elif tecla == ord("n"):
                if jogo.fase_idx + 1 < len(jogo.fases):
                    jogo.iniciar_fase(jogo.fase_idx + 1)
    finally:
        saida.fechar()


if __name__ == "__main__":
    main()

