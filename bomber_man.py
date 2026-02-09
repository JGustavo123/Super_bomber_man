import pygame
import random
import math
import os

# inicialização
pygame.init()
largura, altura = 1280, 768 
tela = pygame.display.set_mode((largura, altura))
pygame.display.set_caption("Super Bomberman - Gabimaru Edition")
relogio = pygame.time.Clock()

# objetos de texto
fonte_txt = pygame.font.Font(None, 36)
fonte_item = pygame.font.Font(None, 24)
fonte_titulo = pygame.font.Font(None, 90)

# cores
GRAMA, PEDRA, MADEIRA, FOGO = (34, 139, 34), (80, 80, 80), (139, 69, 19), (255, 69, 0)
P1_COR, P2_COR, BOT_COR = (30, 30, 155), (200, 30, 30), (200, 0, 200)
BRANCO, PRETO, VERDE_ITEM = (255, 255, 255), (0, 0, 0), (50, 200, 50)
VERDE_BTN, AZUL_BOTAO = (40, 180, 40), (20, 40, 80)
AZUL_TEXTO = (150, 200, 255)

# carregamento das sprites 
try:
    def carregar(nome, tamanho=(56, 56)):
        img = pygame.image.load(os.path.join("sprites", nome)).convert_alpha()
        return pygame.transform.scale(img, tamanho)

    # imagens da interface
    capa_img = pygame.image.load(os.path.join("sprites", "Tela_de_inicio.png")).convert()
    capa_img = pygame.transform.scale(capa_img, (largura, altura))
    
    # sprites do jogador 1
    p1_frente = carregar("Gabimaru_frente.png")
    p1_costas = carregar("Gabimaru_costa.png") 
    p1_direita = carregar("Gabimaru_direita.png")
    p1_esquerda = carregar("Gabimaru_esquerda.png")
    
    # texturas do mapa
    sprite_pedra = carregar("bloco_indestrutivel.png", (64, 64))
    sprite_madeira = carregar("caixa_madeira.png", (64, 64))
    sprite_grama = carregar("grama.png", (64, 64))
    
    tem_sprites = True
    sprite_atual_p1 = p1_frente
except Exception as e:
    print(f"erro ao carregar arquivos: {e}")
    tem_sprites = False
    sprite_atual_p1 = None

# configurações do mapa
tile_size = 64
mapa_l, mapa_a = 15, 11
off_x = (largura - (mapa_l * tile_size)) // 2
off_y = 80 

# retângulos dos botões
rect_btn_start = pygame.Rect(largura//2 - 150, 600, 300, 80)
rect_btn_single = pygame.Rect(largura//2 - 200, 300, 400, 80)
rect_btn_multi = pygame.Rect(largura//2 - 200, 450, 400, 80)

def resetar_jogo():
    global p1_pos, p2_pos, bombas, explosoes, bots, mapa_jogo, itens, p1_status, p2_status, tempo_mov_p1, tempo_mov_p2, vencedor
    p1_pos = [1, 1]
    p2_pos = [9, 13] 
    bombas, explosoes, itens = [], [], []
    tempo_mov_p1 = tempo_mov_p2 = 0
    vencedor = ""
    
    # status iniciais
    p1_status = {"bombas_max": 1, "alcance": 2, "velocidade": 180, "vivo": True} 
    p2_status = {"bombas_max": 1, "alcance": 2, "velocidade": 180, "vivo": True}
    
    # zonas seguras para p1 e p2
    zonas_seguras = [(1,1), (1,2), (2,1), (9,13), (9,12), (8,13)]
    
    mapa_jogo = []
    for l in range(mapa_a):
        linha = []
        for c in range(mapa_l):
            if l == 0 or l == mapa_a-1 or c == 0 or c == mapa_l-1 or (l % 2 == 0 and c % 2 == 0):
                linha.append(1)
            elif (l, c) in zonas_seguras:
                linha.append(0)
            elif random.random() < 0.6:
                linha.append(2)
            else:
                linha.append(0)
        mapa_jogo.append(linha)
    
    bots = []
    if modo_jogo == "single":
        bots = [
            {"pos": [1, 13], "dir": [0, -1], "last": 0, "alcance": 2},
            {"pos": [9, 1], "dir": [0, 1], "last": 0, "alcance": 2},
            {"pos": [9, 13], "dir": [-1, 0], "last": 0, "alcance": 2}
        ]

def esta_livre(l, c):
    if not (0 <= l < mapa_a and 0 <= c < mapa_l) or mapa_jogo[l][c] != 0: return False
    for b in bombas:
        if b[0] == l and b[1] == c: return False
    if [l, c] == p1_pos and p1_status["vivo"]: return False
    if [l, c] == p2_pos and modo_jogo == "multi" and p2_status["vivo"]: return False
    return True

def eh_perigoso(l, c):
    for b in bombas:
        alc = b[4]
        if b[0] == l and abs(b[1] - c) <= alc: return True
        if b[1] == c and abs(b[0] - l) <= alc: return True
    for e in explosoes:
        if e[0] == l and e[1] == c: return True
    return False

def disparar_explosao(lin, col, alcance):
    tempo_fim = pygame.time.get_ticks() + 500
    explosoes.append([lin, col, tempo_fim])
    direcoes = [(0,1), (0,-1), (1,0), (-1,0)]
    for dl, dc in direcoes:
        for i in range(1, alcance + 1): 
            nl, nc = lin + dl*i, col + dc*i
            if 0 <= nl < mapa_a and 0 <= nc < mapa_l:
                if mapa_jogo[nl][nc] == 1: break 
                explosoes.append([nl, nc, tempo_fim])
                if mapa_jogo[nl][nc] == 2:
                    mapa_jogo[nl][nc] = 0 
                    if random.random() < 0.3:
                        tipo = random.choice(["A", "V", "B"])
                        itens.append({"pos": [nl, nc], "tipo": tipo})
                    break

# início das variáveis de controle
sala = 0 
modo_jogo = ""
vencedor = ""
rodando = True
ultima_dir_p1 = "baixo"
ultima_dir_p2 = "baixo"

while rodando:
    agora = pygame.time.get_ticks()
    eventos = pygame.event.get()
    
    for evento in eventos:
        if evento.type == pygame.QUIT: rodando = False
        
        if evento.type == pygame.MOUSEBUTTONDOWN:
            if sala == 0 and rect_btn_start.collidepoint(evento.pos): sala = 1
            elif sala == 1:
                if rect_btn_single.collidepoint(evento.pos): modo_jogo = "single"; resetar_jogo(); sala = 2
                elif rect_btn_multi.collidepoint(evento.pos): modo_jogo = "multi"; resetar_jogo(); sala = 2
            elif sala in [3, 4, 5, 6] and pygame.Rect(440, 450, 400, 80).collidepoint(evento.pos): sala = 0

        if sala == 2 and evento.type == pygame.KEYDOWN:
            # bomba p1 (espaço)
            if evento.key == pygame.K_SPACE and p1_status["vivo"]:
                if len([b for b in bombas if b[3] == "p1"]) < p1_status["bombas_max"]:
                    if not any(b[0] == p1_pos[0] and b[1] == p1_pos[1] for b in bombas):
                        bombas.append([p1_pos[0], p1_pos[1], agora, "p1", p1_status["alcance"]])
            # bomba p2 (shift esquerdo)
            if evento.key == pygame.K_LSHIFT and modo_jogo == "multi" and p2_status["vivo"]:
                if len([b for b in bombas if b[3] == "p2"]) < p2_status["bombas_max"]:
                    if not any(b[0] == p2_pos[0] and b[1] == p2_pos[1] for b in bombas):
                        bombas.append([p2_pos[0], p2_pos[1], agora, "p2", p2_status["alcance"]])

    if sala == 2:
        teclas = pygame.key.get_pressed()
        
        # movimento p1 (setas)
        if p1_status["vivo"] and agora - tempo_mov_p1 > p1_status["velocidade"]:
            nl, nc = p1_pos[0], p1_pos[1]
            if teclas[pygame.K_UP]: nl -= 1; ultima_dir_p1 = "cima"
            elif teclas[pygame.K_DOWN]: nl += 1; ultima_dir_p1 = "baixo"
            elif teclas[pygame.K_LEFT]: nc -= 1; ultima_dir_p1 = "esquerda"
            elif teclas[pygame.K_RIGHT]: nc += 1; ultima_dir_p1 = "direita"
            if [nl, nc] != p1_pos and esta_livre(nl, nc): p1_pos = [nl, nc]; tempo_mov_p1 = agora

        # movimento p2 (wasd)
        if modo_jogo == "multi" and p2_status["vivo"] and agora - tempo_mov_p2 > p2_status["velocidade"]:
            nl, nc = p2_pos[0], p2_pos[1]
            if teclas[pygame.K_w]: nl -= 1; ultima_dir_p2 = "cima"
            elif teclas[pygame.K_s]: nl += 1; ultima_dir_p2 = "baixo"
            elif teclas[pygame.K_a]: nc -= 1; ultima_dir_p2 = "esquerda"
            elif teclas[pygame.K_d]: nc += 1; ultima_dir_p2 = "direita"
            if [nl, nc] != p2_pos and esta_livre(nl, nc): p2_pos = [nl, nc]; tempo_mov_p2 = agora

        # lógica das bombas
        for b in bombas[:]:
            if agora - b[2] > 2000: disparar_explosao(b[0], b[1], b[4]); bombas.remove(b)
        explosoes = [e for e in explosoes if agora < e[2]]
        
        # ia dos bots
        if modo_jogo == "single":
            for bot in bots:
                if agora - bot["last"] > 550:
                    l, c = bot["pos"]; direcoes = [(0,1), (0,-1), (1,0), (-1,0)]
                    possiveis = [d for d in direcoes if esta_livre(l + d[0], c + d[1])]
                    seguras = [d for d in possiveis if not eh_perigoso(l + d[0], c + d[1])]
                    if eh_perigoso(l, c): escolha = random.choice(seguras) if seguras else (random.choice(possiveis) if possiveis else (0,0))
                    else:
                        if seguras:
                            if bot["dir"] in seguras and random.random() < 0.8: escolha = bot["dir"]
                            else:
                                escolha = seguras[0]; d_min = 1000
                                for d in seguras:
                                    dist = math.sqrt((l+d[0]-p1_pos[0])**2 + (c+d[1]-p1_pos[1])**2)
                                    if dist < d_min: d_min = dist; escolha = d
                        else: escolha = (0,0)
                    bot["dir"] = escolha; bot["pos"] = [l + escolha[0], c + escolha[1]]; bot["last"] = agora
                    if not eh_perigoso(l, c) and seguras and random.random() < 0.08:
                        bombas.append([l, c, agora, "bot", bot["alcance"]])

        # checar morte
        for f in explosoes:
            if f[0] == p1_pos[0] and f[1] == p1_pos[1]: p1_status["vivo"] = False
            if modo_jogo == "multi" and f[0] == p2_pos[0] and f[1] == p2_pos[1]: p2_status["vivo"] = False
            for bot in bots[:]:
                if f[0] == bot["pos"][0] and f[1] == bot["pos"][1]: bots.remove(bot)
        
        # condições de fim de jogo
        if modo_jogo == "single":
            if not p1_status["vivo"]: sala = 3 # derrota single
            elif len(bots) == 0: sala = 4 # vitória single
        else: # multiplayer
            if not p1_status["vivo"] and not p2_status["vivo"]: sala = 3 # empate
            elif not p1_status["vivo"]: sala = 6 # p2 venceu
            elif not p2_status["vivo"]: sala = 5 # p1 venceu

    # desenho 
    tela.fill((30, 30, 30))
    
    # tela de inicio
    if sala == 0: 
        if tem_sprites: tela.blit(capa_img, (0, 0))
        pygame.draw.rect(tela, AZUL_BOTAO, rect_btn_start, border_radius=15)
        txt = fonte_txt.render("START GAME", True, AZUL_TEXTO)
        tela.blit(txt, txt.get_rect(center=rect_btn_start.center))

    # seleção de modo
    elif sala == 1: 
        if tem_sprites: tela.blit(capa_img, (0, 0))
        overlay = pygame.Surface((largura, altura)); overlay.set_alpha(180); overlay.fill((0,0,0)); tela.blit(overlay, (0,0))
        pygame.draw.rect(tela, AZUL_BOTAO, rect_btn_single, border_radius=15)
        t_single = fonte_txt.render("SINGLE PLAYER", True, AZUL_TEXTO)
        tela.blit(t_single, t_single.get_rect(center=rect_btn_single.center))
        pygame.draw.rect(tela, AZUL_BOTAO, rect_btn_multi, border_radius=15)
        t_multi = fonte_txt.render("MULTIPLAYER", True, AZUL_TEXTO)
        tela.blit(t_multi, t_multi.get_rect(center=rect_btn_multi.center))

    elif sala == 2:
        for l in range(mapa_a):
            for c in range(mapa_l):
                px, py = off_x + c * tile_size, off_y + l * tile_size
                if tem_sprites: tela.blit(sprite_grama, (px, py))
                if mapa_jogo[l][c] == 1: tela.blit(sprite_pedra, (px, py))
                elif mapa_jogo[l][c] == 2: tela.blit(sprite_madeira, (px, py))
        
        # efeito da bomba
        for b in bombas:
            rd = 22 + int(math.sin(agora * 0.01) * 5)
            pygame.draw.circle(tela, PRETO, (off_x + b[1]*tile_size + 32, off_y + b[0]*tile_size + 32), rd)
            pygame.draw.circle(tela, (60, 60, 60), (off_x + b[1]*tile_size + 28, off_y + b[0]*tile_size + 28), rd // 3)

        for e in explosoes: pygame.draw.rect(tela, FOGO, (off_x + e[1]*tile_size, off_y + e[0]*tile_size, tile_size, tile_size))
        
        if p1_status["vivo"]:
            if tem_sprites: tela.blit(sprite_atual_p1, (off_x + p1_pos[1]*tile_size+4, off_y + p1_pos[0]*tile_size+4))
            else: pygame.draw.rect(tela, P1_COR, (off_x + p1_pos[1]*tile_size+12, off_y + p1_pos[0]*tile_size+12, 40, 40))
        
        if modo_jogo == "multi" and p2_status["vivo"]:
            pygame.draw.rect(tela, P2_COR, (off_x + p2_pos[1]*tile_size+12, off_y + p2_pos[0]*tile_size+12, 40, 40))
        
        if modo_jogo == "single":
            for bot in bots: pygame.draw.rect(tela, BOT_COR, (off_x + bot["pos"][1]*tile_size+12, off_y + bot["pos"][0]*tile_size+12, 40, 40))

    elif sala in [3, 4, 5, 6]:
        if sala == 3: msg, cor = "derrota!", (50, 0, 0)
        elif sala == 4: msg, cor = "vitória!", (0, 50, 0)
        elif sala == 5: msg, cor = "player 1 venceu!", (0, 50, 100)
        elif sala == 6: msg, cor = "player 2 venceu!", (100, 0, 0)
        
        tela.fill(cor)
        t_msg = fonte_titulo.render(msg, True, BRANCO)
        tela.blit(t_msg, t_msg.get_rect(center=(largura//2, 250)))
        
        rect_voltar = pygame.Rect(largura//2 - 200, 450, 400, 80)
        pygame.draw.rect(tela, BRANCO, rect_voltar, 2, border_radius=10)
        t_voltar = fonte_txt.render("voltar ao menu", True, BRANCO)
        tela.blit(t_voltar, t_voltar.get_rect(center=rect_voltar.center))

    pygame.display.flip()
    relogio.tick(60)
pygame.quit()