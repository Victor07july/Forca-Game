import pygame
import math

pygame.init()

#Define a resolução. largura x altura
LARGURA, ALTURA = (800,600) #WIDTH, HEIGHT
janela = pygame.display.set_mode((LARGURA, ALTURA))

#Plano de fundo/background (precisa ser colocado no loop)
background = pygame.image.load('quadro.png')

#Título do jogo
pygame.display.set_caption('Forca Game')

#Imagens do jogo
imagens = []
for i in range(7):
    addimg = pygame.image.load('hangman' + str(i) + '.png') #Variável para adicionar imagens na list imagens através do append (Linha 17 e 14)
    imagens.append(addimg)

#Variáveis dos botões, que serão desenhados começando de seu centro
#O jogo terá 26 botoes, com 13 em duas filas
#A distância entre 2 botões é seu raio * 2 + vão
#Para determinar o começo e fim da fila, é calculada a largura da janela (800) -  onde quermos que a fila comece na reta x
RAIO = 20
VAO = 15
letras = []
começox = round((LARGURA - (RAIO * 2 + VAO) * 13) / 2)
começoy = 400
A = 65 #Na programação, cada letra no teclado é definido por um número, e o A maiusculo é definido pelo 65

for i in range(26): #Determinar a posição x, y e letras (começando do A = 65 +1, +2...) para cada botão
    x = começox + VAO * 2 + (RAIO * 2 + VAO) * (i % 13)
    y = começoy + ((i // 13) * (VAO + RAIO *2))
    letras.append([x, y, chr(A + i), True])

#Fontes
FONTE_LETRA = pygame.font.SysFont('comicsans', 40) #fonte e tamanho
FONTE_PALAVRA = pygame.font.SysFont('comicsans', 30)

#cores 
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)

#Variáveis do jogo
situacao_forca = 0
palavra = 'DESENVOLVEDOR'
acertos = [] #letras que letras foram acertadas

#Loop do jogo
FPS = 60 #FPS máximo (vai na linha 20)
clock = pygame.time.Clock() #Variável com a função de travar o clock

jogorodando = True

#Função para desenhar itnes no jogo, deve ficar dentro do loop  (Linha 67)
def desenhar():
    janela.fill((0, 0, 0))

    janela.blit(background, (0,0)) #Desenha o quadro verde na tela (Linha 11)

    #Desenhar palavras
    mostrar_palavra = ''
    for letra in palavra:
        if letra in acertos:
            mostrar_palavra += letra + ' '
        else: 
            mostrar_palavra += '_ '
    texto = FONTE_PALAVRA.render(mostrar_palavra, 1, (255, 255, 255)) 
    janela.blit(texto, (400, 200))

    #Desenhar letras
    for letra in letras: #Para cada letra dentro da lista letra...
         x, y, ltr, visivel = letra
         if visivel:
            pygame.draw.circle(janela, (255, 255, 255), (x, y), RAIO, 3) #3 = grossura da linha, cor da borda
            texto = FONTE_LETRA.render(ltr, 1, (255, 255, 255))#o que imprimir, anti-alising, cor
            janela.blit(texto, (x - texto.get_width()/2, y - texto.get_height()/2)) #ao dividir a largura do texto por 2, nós saberemos onde ficara o meio do texto, cor da linha

    janela.blit(imagens[situacao_forca], (150,100))
    pygame.display.update()


while jogorodando:
    clock.tick(FPS)

    desenhar()


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            jogorodando = False
        
        #Checar se o mouse clicou em algum botão através da distancia mouse-botao
        if event.type == pygame.MOUSEBUTTONDOWN:
            m_x, m_y = pygame.mouse.get_pos()
            for letra in letras:
                x, y, ltr, visivel = letra
                if visivel:
                    dist = math.sqrt((x - m_x) ** 2 + (y - m_y) ** 2) #Teorema de pitagoras para calcular a distancia entre mouse-botao
                    if dist < RAIO:
                        print(ltr)
                        letra[3] = False #3 é a posição de True na lista "letras" (linha 24 e linha 33)
                        acertos.append(ltr)
                        if ltr not in palavra:
                            situacao_forca += 1

    #Ver se você ganhou o perdeu.
    ganhou = True
    for letra in palavra:
        if letra not in acertos:
            ganhou = False
            break

    if ganhou:
        janela.blit(background, (0, 0))
        texto = FONTE_PALAVRA.render('Você GANHOU!', 1, BRANCO)
        janela.blit(texto, (LARGURA/2 - texto.get_width()/2, ALTURA/2 - texto.get_height()/2))
        pygame.display.update()
        pygame.time.delay(3000)
        break

    if situacao_forca == 6:
        print('Você perdeu')
        break

pygame.quit()
