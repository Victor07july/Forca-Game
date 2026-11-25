import math
import os
import random
import sys
import pygame
from pygame import mixer
import pygame_menu

# No WSLg (Windows + WSL), direciona o SDL para o servidor PulseAudio do Windows
if 'PULSE_SERVER' in os.environ and 'SDL_AUDIODRIVER' not in os.environ:
    os.environ['SDL_AUDIODRIVER'] = 'pulseaudio'

# Inicia o pygame
pygame.init()

# Diretório base para carregar arquivos de imagem e som com segurança
DIRETORIO_BASE = os.path.dirname(os.path.abspath(__file__))

# Inicializa o áudio do jogo (com fallback seguro caso falte biblioteca/placa de som)
AUDIO_DISPONIVEL = False
som_ativo = True
try:
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    AUDIO_DISPONIVEL = True
except pygame.error as erro_audio:
    AUDIO_DISPONIVEL = False
    som_ativo = False
    print(f'Aviso: não foi possível iniciar o áudio ({erro_audio}).')


def tocar_musica_fundo():
    if AUDIO_DISPONIVEL and som_ativo:
        mixer.music.load(os.path.join(DIRETORIO_BASE, 'background_song.mp3'))
        mixer.music.play(-1)


def alternar_som():
    global som_ativo
    if not AUDIO_DISPONIVEL:
        return
    som_ativo = not som_ativo
    botao_som.set_title('Som ON' if som_ativo else 'Som OFF')
    if som_ativo:
        tocar_musica_fundo()
    else:
        mixer.music.stop()


# Inicia a música de fundo com o jogo
tocar_musica_fundo()

# Resolução base de referência e janela redimensionável (suporta maximizar e F11)
LARGURA_BASE, ALTURA_BASE = (800, 600)
LARGURA, ALTURA = (LARGURA_BASE, ALTURA_BASE)
janela = pygame.display.set_mode((LARGURA, ALTURA), pygame.RESIZABLE)
pygame.display.set_caption('Forca Game')

# Carrega imagens originais uma única vez para reescalar com nitidez quando maximizar
CAMINHO_QUADRO = os.path.join(DIRETORIO_BASE, 'quadro.png')
background_original = pygame.image.load(CAMINHO_QUADRO)
imagens_originais = [
    pygame.image.load(os.path.join(DIRETORIO_BASE, f'hangman{i}.png'))
    for i in range(7)
]

# Cores
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
AMARELO_GIZ = (255, 235, 130)

# Variáveis dinâmicas dependentes da resolução atual
A = 65  # Código ASCII da letra 'A' maiúscula
RAIO = 20
VAO = 15
ESPESSURA_CIRCULO = 3
background = background_original
imagens = list(imagens_originais)
FONTE_LETRA = None
FONTE_PALAVRA = None
FONTE_TITULO = None
FONTE_DICA = None

# Palavras e dicas recuperadas do projeto original (commit afc5e50)
DICAS_PALAVRAS = {
    'BRASIL': 'País da América do Sul, conhecido por suas praias e clima tropical.',
    'NORUEGA': 'País localizado na Europa, famoso por possuir navios Vikings.',
    'CHINA': 'País origem do molho Shoyu.',
    'ITALIA': 'País onde foi inventada a Pizza.',
    'ALEMANHA': 'País que causou a Segunda Guerra Mundial.',
}
palavras = list(DICAS_PALAVRAS.keys())

situacao_forca = 0
palavra = ''
acertos = []
letras = []
menu = None


def calcular_posicoes_letras(visibilidades=None):
    sy = ALTURA / ALTURA_BASE
    largura_fila = 12 * (RAIO * 2 + VAO)
    primeiro_x = round((LARGURA - largura_fila) / 2)
    começoy = round(400 * sy)

    botoes = []
    for i in range(26):
        x = primeiro_x + (RAIO * 2 + VAO) * (i % 13)
        y = começoy + ((i // 13) * (VAO + RAIO * 2))
        visivel = True if visibilidades is None else visibilidades[i]
        botoes.append([x, y, chr(A + i), visivel])
    return botoes


def criar_botoes_letras():
    return calcular_posicoes_letras()


def atualizar_resolucao(nova_largura, nova_altura):
    global LARGURA, ALTURA, RAIO, VAO, ESPESSURA_CIRCULO
    global background, imagens, letras
    global FONTE_LETRA, FONTE_PALAVRA, FONTE_TITULO, FONTE_DICA

    LARGURA = max(480, nova_largura)
    ALTURA = max(360, nova_altura)
    sx = LARGURA / LARGURA_BASE
    sy = ALTURA / ALTURA_BASE
    escala = min(sx, sy)

    # Redimensiona o quadro-negro para preencher toda a janela
    background = pygame.transform.smoothscale(background_original, (LARGURA, ALTURA))

    # Redimensiona as imagens da forca mantendo a proporção original
    imagens = [
        pygame.transform.smoothscale(
            img,
            (max(1, round(img.get_width() * escala)), max(1, round(img.get_height() * escala))),
        )
        for img in imagens_originais
    ]

    # Escala botões e fontes proporcionalmente
    RAIO = max(12, round(20 * escala))
    VAO = max(6, round(15 * escala))
    ESPESSURA_CIRCULO = max(2, round(3 * escala))

    FONTE_LETRA = pygame.font.SysFont('comicsans', max(18, round(40 * escala)))
    FONTE_PALAVRA = pygame.font.SysFont('comicsans', max(16, round(30 * escala)))
    FONTE_TITULO = pygame.font.SysFont('comicsans', max(16, round(28 * escala)))
    FONTE_DICA = pygame.font.SysFont('lucidahandwriting,comicsans,dejavusans', max(12, round(18 * escala)))

    # Reposiciona os 26 botões preservando quais letras já foram clicadas
    visibilidades = [b[3] for b in letras] if len(letras) == 26 else None
    letras = calcular_posicoes_letras(visibilidades)

    # Atualiza tamanho, fontes e centralização do menu se já estiver criado
    if menu is not None:
        menubar = menu.get_menubar()
        menubar.update_font({'size': max(20, round(40 * escala))})
        for widget in menu.get_widgets():
            widget.update_font({'size': max(16, round(28 * escala))})
            widget.set_margin(0, round(22 * escala))
        menu.resize(LARGURA, ALTURA)
        menubar._offsetx = max(0, (LARGURA - menubar.get_width()) // 2)
        menubar._offsety = round(70 * sy)


def sincronizar_janela():
    global janela
    sup_atual = pygame.display.get_surface()
    if sup_atual is not None:
        janela = sup_atual
    larg_atual, alt_atual = janela.get_size()
    if (larg_atual, alt_atual) != (LARGURA, ALTURA):
        atualizar_resolucao(larg_atual, alt_atual)


def reiniciar_jogo():
    global situacao_forca, palavra, acertos, letras
    situacao_forca = 0
    palavra = random.choice(palavras)
    acertos = []
    letras = criar_botoes_letras()


atualizar_resolucao(LARGURA_BASE, ALTURA_BASE)
reiniciar_jogo()


# Função para desenhar itens no jogo adaptados ao tamanho atual da janela
def desenhar():
    sincronizar_janela()
    sx = LARGURA / LARGURA_BASE
    sy = ALTURA / ALTURA_BASE

    janela.fill(PRETO)
    janela.blit(background, (0, 0))

    # Desenhar título
    texto = FONTE_TITULO.render('FORCA GAME', True, BRANCO)
    janela.blit(texto, (LARGURA / 2 - texto.get_width() / 2, round(30 * sy)))

    # Desenhar dica correspondente à palavra sorteada
    texto_dica = DICAS_PALAVRAS.get(palavra, '')
    if texto_dica:
        dica = FONTE_DICA.render(f'Dica: {texto_dica}', True, AMARELO_GIZ)
        janela.blit(dica, (LARGURA / 2 - dica.get_width() / 2, round(72 * sy)))

    # Desenhar palavra oculta/revelada
    mostrar_palavra = ''
    for letra in palavra:
        if letra == ' ':
            mostrar_palavra += '  '
        elif letra in acertos:
            mostrar_palavra += letra + ' '
        else:
            mostrar_palavra += '_ '
    texto = FONTE_PALAVRA.render(mostrar_palavra, True, BRANCO)
    janela.blit(texto, (round(400 * sx), round(220 * sy)))

    # Desenhar botões das letras
    for letra in letras:
        x, y, ltr, visivel = letra
        if visivel:
            pygame.draw.circle(janela, BRANCO, (x, y), RAIO, ESPESSURA_CIRCULO)
            texto = FONTE_LETRA.render(ltr, True, BRANCO)
            janela.blit(texto, (x - texto.get_width() / 2, y - texto.get_height() / 2))

    janela.blit(imagens[situacao_forca], (round(150 * sx), round(115 * sy)))
    pygame.display.update()


def aguardar_responsivo(duracao_ms, callback_desenho=None):
    inicio = pygame.time.get_ticks()
    relogio = pygame.time.Clock()
    while pygame.time.get_ticks() - inicio < duracao_ms:
        relogio.tick(60)
        redimensionou = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
                redimensionou = True
            if event.type == pygame.VIDEORESIZE:
                atualizar_resolucao(event.w, event.h)
                redimensionou = True

        larg_atual, alt_atual = janela.get_size()
        if (larg_atual, alt_atual) != (LARGURA, ALTURA):
            atualizar_resolucao(larg_atual, alt_atual)
            redimensionou = True

        if redimensionou and callback_desenho is not None:
            callback_desenho()


# Mostra mensagem de fim de jogo, toca o efeito correspondente e retoma a música de fundo
def mostrar_mensagem(mensagem, subtitulo=None, arquivo_som=None):
    aguardar_responsivo(800, desenhar)

    if AUDIO_DISPONIVEL and som_ativo and arquivo_som:
        mixer.music.load(os.path.join(DIRETORIO_BASE, arquivo_som))
        mixer.music.play()

    def desenhar_tela_mensagem():
        janela.blit(background, (0, 0))
        texto = FONTE_PALAVRA.render(mensagem, True, BRANCO)
        if subtitulo:
            texto_sub = FONTE_PALAVRA.render(subtitulo, True, AMARELO_GIZ)
            janela.blit(texto, (LARGURA / 2 - texto.get_width() / 2, ALTURA / 2 - texto.get_height()))
            janela.blit(texto_sub, (LARGURA / 2 - texto_sub.get_width() / 2, ALTURA / 2 + round(10 * (ALTURA / ALTURA_BASE))))
        else:
            janela.blit(texto, (LARGURA / 2 - texto.get_width() / 2, ALTURA / 2 - texto.get_height() / 2))
        pygame.display.update()

    desenhar_tela_mensagem()
    aguardar_responsivo(4000, desenhar_tela_mensagem)

    if AUDIO_DISPONIVEL and som_ativo and arquivo_som:
        tocar_musica_fundo()

    pygame.event.clear()


def main():
    global situacao_forca
    sincronizar_janela()
    reiniciar_jogo()

    FPS = 60
    clock = pygame.time.Clock()
    jogorodando = True

    while jogorodando:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    jogorodando = False
                elif event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()

            if event.type == pygame.VIDEORESIZE:
                atualizar_resolucao(event.w, event.h)

            # Checar se o mouse clicou em algum botão através da distância mouse-botão
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                m_x, m_y = pygame.mouse.get_pos()
                for letra in letras:
                    x, y, ltr, visivel = letra
                    if visivel:
                        dist = math.sqrt((x - m_x) ** 2 + (y - m_y) ** 2)
                        if dist < RAIO:
                            letra[3] = False
                            acertos.append(ltr)
                            if ltr not in palavra:
                                situacao_forca += 1

        desenhar()

        # Verificar se ganhou ou perdeu
        ganhou = all(letra in acertos or letra == ' ' for letra in palavra)

        if ganhou:
            mostrar_mensagem('Parabéns, você ganhou!', arquivo_som='win_song.mp3')
            break

        if situacao_forca == 6:
            mostrar_mensagem(
                'Poxa, não foi dessa vez...',
                subtitulo=f'A palavra era: {palavra}',
                arquivo_som='fail_song.mp3',
            )
            break


def sair_jogo():
    pygame.quit()
    sys.exit(0)


# DEFININDO BACKGROUND DO MENU
imagem_fundo_menu = pygame_menu.baseimage.BaseImage(
    image_path=CAMINHO_QUADRO,
    drawing_mode=pygame_menu.baseimage.IMAGE_MODE_FILL,
)

# CONFIGURANDO O TEMA DO MENU (pygame-menu 4.x)
tema = pygame_menu.themes.Theme(
    background_color=imagem_fundo_menu,
    title_bar_style=pygame_menu.widgets.MENUBAR_STYLE_NONE,
    title_close_button=False,
    title_font_shadow=True,
    title_font=pygame_menu.font.FONT_8BIT,
    title_font_size=40,
    title_font_color=BRANCO,
    title_offset=(200, 70),
    widget_font=pygame_menu.font.FONT_8BIT,
    widget_font_size=28,
    widget_font_color=BRANCO,
    selection_color=AMARELO_GIZ,
    widget_margin=(0, 22),
)

# SETANDO O MENU INICIAL
menu = pygame_menu.Menu(
    'Forca Game',
    LARGURA,
    ALTURA,
    theme=tema,
    mouse_motion_selection=True,
)
menu.add.button('Jogar', main)
botao_som = menu.add.button('Som ON' if som_ativo else 'Som OFF', alternar_som)
menu.add.button('Sair', sair_jogo)
atualizar_resolucao(LARGURA, ALTURA)


def executar_menu():
    clock = pygame.time.Clock()
    while True:
        clock.tick(60)
        eventos = pygame.event.get()
        for event in eventos:
            if event.type == pygame.QUIT:
                sair_jogo()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
            if event.type == pygame.VIDEORESIZE:
                atualizar_resolucao(event.w, event.h)

        sincronizar_janela()

        if menu.is_enabled():
            menu.update(eventos)
            menu.draw(janela)
            pygame.display.update()


if __name__ == '__main__':
    executar_menu()
