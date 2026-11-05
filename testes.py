"""Testes automatizados da lógica pura do Quebra-Cabeça (sem necessidade de câmera física).

Execute no terminal: python testes.py
"""
import math
from logica import (
    BotaoVirtual,
    CursorMao,
    JogoQuebraCabeca,
    Peca,
    dist,
    razao_pinca,
)

W, H = 960, 540


def test_distancia_euclidiana():
    assert dist((0, 0), (3, 4)) == 5.0
    assert dist((10, 20), (10, 20)) == 0.0


def test_razao_pinca_normalizada():
    # Cria landmarks sintéticos de mão
    # Pulso em (0, 100), Base do médio em (0, 0) -> tamanho da mão = 100 px
    mao = [(0, 0)] * 21
    mao[0] = (0, 100)   # Pulso
    mao[9] = (0, 0)     # Base do dedo médio

    # Dedos bem próximos (pinça fechada)
    mao[4] = (50, 50)   # Ponta polegar
    mao[8] = (52, 50)   # Ponta indicador
    r_fechada = razao_pinca(mao)
    assert r_fechada < 0.15

    # Dedos bem afastados (mão aberta)
    mao[4] = (10, 50)
    mao[8] = (90, 50)
    r_aberta = razao_pinca(mao)
    assert r_aberta > 0.70


def test_cursor_suavizacao_e_tolerancia():
    cursor = CursorMao(alpha=0.5, tolerancia_perda_s=0.40)
    t = 0.0

    # Inicialização: primeiro ponto é adotado diretamente
    cursor.atualizar((100.0, 100.0), 0.8, t)
    assert cursor.ativa
    assert cursor.pos == (100.0, 100.0)

    # Segundo ponto: suavização exponencial (média ponderada)
    t += 0.033
    cursor.atualizar((200.0, 200.0), 0.8, t)
    assert cursor.pos == (150.0, 150.0)

    # Perda curta (< 0.40s): permanece ativa na posição anterior
    t += 0.10
    cursor.atualizar(None, None, t)
    assert cursor.ativa
    assert cursor.pos == (150.0, 150.0)

    # Perda longa (> 0.40s): desativa
    t += 0.50
    cursor.atualizar(None, None, t)
    assert not cursor.ativa
    assert cursor.pos is None


def test_pinça_histerese_e_debounce():
    cursor = CursorMao(limiar_fechar=0.32, limiar_abrir=0.52, debounce_quadros=2)
    t = 0.0

    # 1 quadro com dedos juntos (< 0.32): ainda não deve disparar (debounce = 2)
    fechou, abriu = cursor.atualizar((100, 100), 0.20, t)
    assert not cursor.pinçando and not fechou

    # 2º quadro consecutivo: ativa a pinça
    t += 0.033
    fechou, abriu = cursor.atualizar((100, 100), 0.20, t)
    assert cursor.pinçando and fechou

    # Valor dentro da faixa de histerese (0.40): deve manter-se pinçando!
    t += 0.033
    fechou, abriu = cursor.atualizar((100, 100), 0.40, t)
    assert cursor.pinçando and not abriu

    # Mão abrindo (> 0.52): precisa de 2 quadros de debounce para soltar
    t += 0.033
    fechou, abriu = cursor.atualizar((100, 100), 0.70, t)
    assert cursor.pinçando  # 1º quadro aberto

    t += 0.033
    fechou, abriu = cursor.atualizar((100, 100), 0.70, t)
    assert not cursor.pinçando and abriu  # 2º quadro: soltou


def test_pegar_e_arrastar_peca():
    jogo = JogoQuebraCabeca(W, H, seed=42)
    cursor = CursorMao(alpha=1.0, debounce_quadros=1)

    peca = jogo.pecas[0]
    px, py = peca.x, peca.y

    # Posiciona o cursor sobre a peça e fecha a pinça
    t = 0.0
    cursor.atualizar((px, py), 0.20, t)
    jogo.atualizar(cursor, t, 0.033)

    assert jogo.peca_ativa is peca
    assert peca.segurada

    # Arrasta a mão para outro ponto (300, 300)
    t += 0.033
    cursor.atualizar((300.0, 300.0), 0.20, t)
    jogo.atualizar(cursor, t, 0.033)

    assert peca.segurada
    assert math.isclose(peca.x, 300.0, abs_tol=1.0)
    assert math.isclose(peca.y, 300.0, abs_tol=1.0)


def test_snap_magnetico_ao_soltar_proximo():
    jogo = JogoQuebraCabeca(W, H, seed=42)
    cursor = CursorMao(alpha=1.0, debounce_quadros=1)
    peca = jogo.pecas[0]

    # Pega a peça
    t = 0.0
    cursor.atualizar((peca.x, peca.y), 0.20, t)
    jogo.atualizar(cursor, t, 0.033)
    assert jogo.peca_ativa is peca

    # Move a peça para bem próximo do seu slot correto (dentro do raio_snap de 55 px)
    t += 0.033
    pos_quase_certa = (peca.slot_x + 15.0, peca.slot_y - 10.0)
    cursor.atualizar(pos_quase_certa, 0.20, t)
    jogo.atualizar(cursor, t, 0.033)

    # Abre a pinça (solta)
    t += 0.033
    cursor.atualizar(pos_quase_certa, 0.80, t)
    jogo.atualizar(cursor, t, 0.033)

    # A peça deve ter encaixado com snap magnético exato!
    assert jogo.peca_ativa is None
    assert peca.encaixada
    assert peca.x == peca.slot_x and peca.y == peca.slot_y
    assert jogo.pecas_encaixadas == 1
    assert jogo.pontos >= 100
    assert len(jogo.particulas) > 0  # partículas emitidas


def test_soltar_longe_nao_encaixa():
    jogo = JogoQuebraCabeca(W, H, seed=42)
    cursor = CursorMao(debounce_quadros=1)
    peca = jogo.pecas[0]

    # Pega e move para uma posição bem longe do slot correto
    t = 0.0
    cursor.atualizar((peca.x, peca.y), 0.20, t)
    jogo.atualizar(cursor, t, 0.033)

    t += 0.033
    pos_longe = (150.0, 250.0)
    cursor.atualizar(pos_longe, 0.20, t)
    jogo.atualizar(cursor, t, 0.033)

    # Solta longe
    t += 0.033
    cursor.atualizar(pos_longe, 0.80, t)
    jogo.atualizar(cursor, t, 0.033)

    # Não deve ter encaixado
    assert not peca.encaixada
    assert jogo.pecas_encaixadas == 0
    assert jogo.pontos == 0


def test_perda_longa_solta_peca_com_segurança():
    jogo = JogoQuebraCabeca(W, H, seed=42)
    cursor = CursorMao(debounce_quadros=1, tolerancia_perda_s=0.30)
    peca = jogo.pecas[0]

    # Segura a peça
    t = 0.0
    cursor.atualizar((peca.x, peca.y), 0.20, t)
    jogo.atualizar(cursor, t, 0.033)
    assert jogo.peca_ativa is peca

    # Mão é perdida temporariamente (0.1s): mantém a peça
    t += 0.10
    cursor.atualizar(None, None, t)
    jogo.atualizar(cursor, t, 0.10)
    assert jogo.peca_ativa is peca

    # Mão é perdida por tempo longo (> 0.30s): solta a peça suavemente
    t += 0.40
    cursor.atualizar(None, None, t)
    jogo.atualizar(cursor, t, 0.40)
    assert jogo.peca_ativa is None
    assert not peca.segurada


def test_conclusao_de_fase_e_avanco():
    jogo = JogoQuebraCabeca(W, H, seed=42)
    assert jogo.fase_idx == 0
    assert jogo.estado == "jogando"

    # Encaixa todas as peças diretamente
    for p in jogo.pecas:
        p.x = p.slot_x
        p.y = p.slot_y
        jogo._tentar_encaixar(p, 1.0)

    assert jogo.pecas_encaixadas == len(jogo.pecas)
    assert jogo.estado == "fase_concluida"

    # Avança para a próxima fase
    jogo._executar_acao_botao("proxima")
    assert jogo.fase_idx == 1
    assert jogo.estado == "jogando"
    assert jogo.pecas_encaixadas == 0


def test_botoes_virtuais_clique_e_dwell():
    btn = BotaoVirtual("teste", "Teste", 100, 100, 80, 40, tempo_dwell_necessario=0.5)

    # Fora do botão: sem ação
    assert not btn.atualizar((50, 50), acabou_de_fechar=False, dt=0.1)
    assert not btn.hover

    # Sobre o botão com pinça fechada: acionamento imediato
    assert btn.atualizar((120, 120), acabou_de_fechar=True, dt=0.1)

    # Sobre o botão sem pinça, mas esperando tempo dwell (0.5s)
    assert not btn.atualizar((120, 120), acabou_de_fechar=False, dt=0.3)
    assert btn.atualizar((120, 120), acabou_de_fechar=False, dt=0.3)  # ultrapassa 0.5s -> dispara


if __name__ == "__main__":
    funcoes_teste = [f for n, f in sorted(globals().items()) if n.startswith("test_")]
    passaram = 0
    for teste in funcoes_teste:
        teste()
        print(f"ok  {teste.__name__}")
        passaram += 1
    print(f"\n{passaram} testes passaram com sucesso.")
