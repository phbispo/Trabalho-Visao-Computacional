# Quebra-Cabeça Interativo com Visão Computacional (MediaPipe Hand Landmarker)

Trabalho prático da disciplina de **Visão Computacional** — Conceito 2 (C2)  
Prof. Gabriel Soares Baptista — Computação — FAESA

---

## 🎯 Visão Geral do Projeto

O **Quebra-Cabeça Interativo** é um jogo em tempo real controlado inteiramente por gestos da mão capturados por câmera ou vídeo. Utilizando o **MediaPipe Hand Landmarker (API Tasks)**, a aplicação interpreta as articulações dos dedos para permitir que o usuário:

1. **Pegue as peças** da bandeja à esquerda unindo a ponta do polegar à ponta do indicador (gesto de pinça);
2. **Arraste as peças** pelo ar com movimento natural e suavizado;
3. **Encaixe as peças** no tabuleiro à direita via **Snap Magnético**, travando-as na posição correta com efeitos comemorativos de partículas;
4. **Avance por fases progressivas** com diferentes temas e níveis de dificuldade:
   - **Fase 1:** Espaço Cósmico (Grade 2x2 — 4 peças grandes)
   - **Fase 2:** Floresta Mágica (Grade 3x2 — 6 peças médias)
   - **Fase 3:** Robô Futurista (Grade 3x3 — 9 peças)

---

## 📋 Atendimento aos Requisitos da Avaliação (C2)

| Requisito do Edital | Como foi implementado no projeto |
|---|---|
| **Regra de interação definida pela equipe** | Medição da **razão da pinça** entre o polegar (landmark 4) e indicador (landmark 8) normalizada pela palma (landmarks 0 e 9). Implementação de **máquina de estados com histerese** (liga em `< 0.32` e desliga em `> 0.52`) e **debounce de 2 quadros**, além de **Snap Magnético** por distância euclidiana ao slot correspondente. |
| **Estado que evolui ao longo do tempo** | Máquina de estados (`jogando` → `fase_concluida` → `vitoria`), cronômetro de fase e total, pontuação progressiva com bônus por velocidade, contagem de peças encaixadas/restantes e progressão entre 3 fases distintas. |
| **Resposta visual que expressa entendimento** | Cursor interativo com mudança de cor e forma (verde quando livre, anel contraído dourado quando em pinça), efeito de **hover** iluminado nas peças, efeito de **elevação 3D com sombra projetada** ao segurar peças, explosão de partículas douradas/esmeralda no encaixe correto, gabarito translúcido na função "Dica", botões com indicador circular de *dwell click* e HUD completo. |
| **Comportamento para perda de detecção** | **Tolerância a oclusões curtas** (< 0.40s) mantendo a peça estável; **liberação segura sem teletransporte** em perdas longas (> 0.40s); aviso em tela *"Mostre a mão para a câmera"* quando nenhuma mão estiver presente. |
| **Separação em camadas recomendada** | Código desacoplado em `maos.py` (visão/câmera), `logica.py` (regras puras sem OpenCV/MediaPipe), `visual.py` (renderização e tipografia com Pillow) e `quebra_cabeca.py` (game loop principal). |

---

## 🚀 Como Executar

### 1. Instalação das Dependências

Certifique-se de ter o Python 3.10 ou superior instalado:

```bash
pip install -r requirements.txt
```

*(Dependências: `mediapipe`, `opencv-python`, `numpy`, `pillow`)*

O modelo `hand_landmarker.task` já se encontra na raiz do projeto (ou será baixado automaticamente se ausente).

### 2. Executando o Jogo

**Com Webcam (modo padrão interativo):**
```bash
python quebra_cabeca.py
```

**Com um arquivo de vídeo (para testes ou apresentação pré-gravada):**
```bash
python quebra_cabeca.py --video seu_video.mp4
```

**Gravar a partida diretamente em arquivo MP4 (modo headless para entrega/vídeo):**
```bash
python quebra_cabeca.py --saida demonstracao.mp4
```

**Selecionar fase inicial ou câmera específica:**
```bash
python quebra_cabeca.py --fase 2 --camera 1 --largura 960 --fps 60
```

---

## 🎮 Controles e Interação

### Gestos com a Mão:
- **Pinça (Polegar + Indicador juntos):** Pega a peça que estiver sob o cursor ou aciona botões da interface.
- **Mão Aberta (Dedos afastados):** Solta a peça que está sendo segurada.
- **Permanência (Dwell Click):** Manter a mão parada sobre um botão por 1.0s o ativa automaticamente.

### Teclas de Atalho:
- `q` ou `ESC`: Encerra o jogo.
- `e`: Mostra / oculta o esqueleto da mão e articulações do MediaPipe.
- `d`: Mostra / oculta os dados de depuração em tempo real (FPS, status e taxa de detecção).
- `h`: Liga / desliga a **Dica translúcida (Gabarito)** no tabuleiro.
- `b`: **Embaralha** as peças soltas na bandeja lateral.
- `r`: Reinicia a fase atual.
- `n`: Avança diretamente para a próxima fase.

---

## 🧪 Testes Automatizados (Sem Câmera)

Toda a lógica pura do jogo foi estruturada em `logica.py` sem chamadas de câmera ou OpenCV, permitindo testes sintéticos determinísticos rápidos:

```bash
python testes.py
```

Bateria de 10 testes cobrindo:
1. Cálculo de distância euclidiana 2D;
2. Razão normalizada da pinça invariante à profundidade;
3. Suavização exponencial do cursor da mão;
4. Histerese e debounce contra falsos disparos da pinça;
5. Mecânica de pegar, arrastar e seguir o cursor com offset relativo;
6. Snap magnético e emissão de partículas ao soltar próximo do slot;
7. Rejeição de encaixe e preservação de estado ao soltar longe;
8. Tolerância a perdas breves de visão (< 0.40s);
9. Soltura segura e prevenção de teletransporte em perdas longas (> 0.40s);
10. Transição de estados entre fases e acionamento de botões virtuais por pinça e dwell.

---

## 🏗️ Arquitetura do Software

```
TrabalhoDeepLearning/
├── hand_landmarker.task     # Modelo pré-treinado MediaPipe Tasks (8 MB)
├── requirements.txt         # mediapipe, opencv-python, numpy, pillow
├── maos.py                  # Camada 1: Câmera, MediaPipe Tasks, rastreamento e esqueleto
├── logica.py                # Camada 2 e 3: Regras puras, geometria, snap magnético e estados
├── visual.py                # Camada 4: Fatiamento de peças, sombras, partículas, botões e HUD
├── quebra_cabeca.py         # Laço principal (Game Loop) integrando as 4 camadas
├── testes.py                # Testes unitários automatizados da lógica pura
├── gerar_assets.py          # Script gerador das artes originais em alta resolução
└── assets/                  # Ilustrações temáticas completas das fases
    ├── puzzle_espaco.png    # Fase 1: Espaço Cósmico (2x2)
    ├── puzzle_floresta.png  # Fase 2: Floresta Mágica (3x2)
    └── puzzle_robot.png     # Fase 3: Robô Futurista (3x3)
```

---

## 🔮 Continuidade na C3 (Evolução Futura)

Conforme orientação do edital, a aplicação foi projetada de forma modular para permitir evolução direta na avaliação do Conceito 3 (C3):
- **Rotação de Peças com Dois Dedos:** Permitir que as peças comecem rotacionadas em 90°, 180° ou 270°, exigindo que o jogador gire a mão ou use o dedo médio para orientar a peça antes de encaixar.
- **Modo Cooperativo (2 Mãos / 2 Jogadores):** Configurar `num_maos=2` para permitir que duas pessoas montem um quebra-cabeça de 16 ou 25 peças juntas na mesma câmera.
- **Importação de Fotos Personalizadas:** Botão para capturar uma foto pela webcam ou carregar qualquer imagem do computador para gerar um quebra-cabeça na hora.
- **Efeitos Sonoros Sintetizados:** Áudio espacial ao pegar, arrastar e encaixar peças com sucesso.

---

## 🎥 Roteiro Sugerido para o Vídeo de Demonstração (Até 3 Minutos)

1. **Abertura (0:00 - 0:25):**
   - Apresentação dos integrantes e objetivo do projeto (Quebra-Cabeça com pegada e encaixe por pinça da mão usando MediaPipe Tasks).
2. **Demonstração da Interação Básica (0:25 - 1:15):**
   - Mostrar a mão aberta diante da câmera (cursor verde).
   - Fazer o gesto de pinça sobre uma peça: destacar a borda dourada e a sombra projetada (elevação 3D).
   - Arrastar a peça até o tabuleiro e soltar perto do slot correto, demonstrando o **Snap Magnético** e a explosão de partículas coloridas.
3. **Comportamento em Falha / Perda de Detecção (1:15 - 1:45):**
   - Segurar uma peça e retirar propositalmente a mão do campo de visão da câmera: demonstrar que a peça é solta suavemente no local, o aviso *"Mostre a mão para a câmera"* aparece e não há pulo/teletransporte quando a mão retorna.
4. **Botões Virtuais e Gabarito (1:45 - 2:20):**
   - Acionar o botão *"Dica [H]"* (por pinça ou tempo parado sobre ele) mostrando o gabarito translúcido.
   - Encaixar as peças restantes da Fase 1 e mostrar a transição para a Fase 2 (Floresta Mágica).
5. **Encerramento e Código (2:20 - 3:00):**
   - Mostrar rapidamente a organização dos arquivos (`maos.py`, `logica.py`, `visual.py`, `testes.py`) e a execução dos 10 testes com `python testes.py`.

