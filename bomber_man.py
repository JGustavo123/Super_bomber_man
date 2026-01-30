import pygame
import random
import math

# Inicialização
pygame.init()
largura, altura = 1280, 768 
tela = pygame.display.set_mode((largura, altura))
relogio = pygame.time.Clock()

# Objetos de texto
fonte_txt = pygame.font.Font(None, 36)
fonte_item = pygame.font.Font(None, 24)
fonte_titulo = pygame.font.Font(None, 90)

# Cores
GRAMA, PEDRA, MADEIRA, FOGO = (34, 139, 34), (80, 80, 80), (139, 69, 19), (255, 69, 0)
P1_COR, BOT_COR = (30, 30, 155), (200, 0, 200)
BRANCO, PRETO, VERDE_ITEM = (255, 255, 255), (0, 0, 0), (50, 200, 50)
VERDE_BTN, VERMELHO_BTN = (40, 180, 40), (180, 40, 40)

# Configurações do Mapa
tile_size = 64
mapa_l, mapa_a = 15, 11
off_x = (largura - (mapa_l * tile_size)) // 2
off_y = 80 

def resetar_jogo():
    global p1_pos, bombas, explosoes, bots, mapa_jogo, itens, p1_status, tempo_mov_p1
    p1_pos = [1, 1]
    bombas, explosoes, itens = [], [], []
    tempo_mov_p1 = 0
    
    # Status iniciais equilibrados
    p1_status = {"bombas_max": 1, "alcance": 2, "velocidade": 180, "itens_v": 0} 
    
    zonas_seguras = [(1,1), (1,2), (2,1), (1,13), (1,12), (2,13), (9,1), (8,1), (9,2), (9,13), (9,12), (8,13)]
    
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
    
    bots = [
        {"pos": [1, 13], "dir": [0, -1], "last": 0, "alcance": 2},
        {"pos": [9, 1], "dir": [0, 1], "last": 0, "alcance": 2},
        {"pos": [9, 13], "dir": [-1, 0], "last": 0, "alcance": 2}
    ]

def esta_livre(l, c):
    if not (0 <= l < mapa_a and 0 <= c < mapa_l) or mapa_jogo[l][c] != 0: 
        return False
    for b in bombas:
        if b[0] == l and b[1] == c: return False
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

# O jogo começa na tela de Menu (0)
sala = 0 
resetar_jogo()
rodando = True

while rodando:
    agora = pygame.time.get_ticks()
    eventos = pygame.event.get()
    
    for evento in eventos:
        if evento.type == pygame.QUIT: 
            rodando = False
        
        if evento.type == pygame.MOUSEBUTTONDOWN:
            if sala == 0:
                if pygame.Rect(440, 350, 400, 100).collidepoint(evento.pos):
                    resetar_jogo()
                    sala = 2
            elif sala in [3, 4]:
                if pygame.Rect(440, 450, 400, 80).collidepoint(evento.pos):
                    sala = 0

        if sala == 2 and evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE:
            if len([b for b in bombas if b[3] == "p1"]) < p1_status["bombas_max"]:
                if not any(b[0] == p1_pos[0] and b[1] == p1_pos[1] for b in bombas):
                    bombas.append([p1_pos[0], p1_pos[1], agora, "p1", p1_status["alcance"]])

    if sala == 2:
        teclas = pygame.key.get_pressed()
        if agora - tempo_mov_p1 > p1_status["velocidade"]:
            nl, nc = p1_pos[0], p1_pos[1]
            if teclas[pygame.K_UP]: nl -= 1
            elif teclas[pygame.K_DOWN]: nl += 1
            elif teclas[pygame.K_LEFT]: nc -= 1
            elif teclas[pygame.K_RIGHT]: nc += 1
            if [nl, nc] != p1_pos and esta_livre(nl, nc):
                p1_pos = [nl, nc]; tempo_mov_p1 = agora

        for item in itens[:]:
            if item["pos"] == p1_pos:
                if item["tipo"] == "A": p1_status["alcance"] += 1 
                elif item["tipo"] == "V": p1_status["itens_v"] += 1; p1_status["velocidade"] = max(50, p1_status["velocidade"] - 15) 
                elif item["tipo"] == "B": p1_status["bombas_max"] += 1 
                itens.remove(item)

        # IA de Sobrevivência Real
        for bot in bots:
            if agora - bot["last"] > 550:
                l, c = bot["pos"]
                direcoes = [(0,1), (0,-1), (1,0), (-1,0)]
                possiveis = [d for d in direcoes if esta_livre(l + d[0], c + d[1])]
                seguras = [d for d in possiveis if not eh_perigoso(l + d[0], c + d[1])]

                if eh_perigoso(l, c):
                    escolha = random.choice(seguras) if seguras else (random.choice(possiveis) if possiveis else (0,0))
                else:
                    if seguras:
                        if bot["dir"] in seguras and random.random() < 0.8:
                            escolha = bot["dir"]
                        else:
                            escolha = seguras[0]
                            d_min = 1000
                            for d in seguras:
                                dist = math.sqrt((l+d[0]-p1_pos[0])**2 + (c+d[1]-p1_pos[1])**2)
                                if dist < d_min: d_min = dist; escolha = d
                    else: escolha = (0,0)

                bot["dir"] = escolha
                bot["pos"] = [l + escolha[0], c + escolha[1]]; bot["last"] = agora

                if not eh_perigoso(l, c) and seguras and random.random() < 0.08:
                    bombas.append([l, c, agora, "bot", bot["alcance"]])

        for b in bombas[:]:
            if agora - b[2] > 2000: disparar_explosao(b[0], b[1], b[4]); bombas.remove(b)
        explosoes = [e for e in explosoes if agora < e[2]]
        for f in explosoes:
            if f[0] == p1_pos[0] and f[1] == p1_pos[1]: sala = 3
            for bot in bots[:]:
                if f[0] == bot["pos"][0] and f[1] == bot["pos"][1]: bots.remove(bot)
        if len(bots) == 0: sala = 4

    # --- DESENHO ---
    tela.fill((30, 30, 30))
    if sala == 0:
        tela.blit(fonte_titulo.render("SUPER BOMBERMAN", True, BRANCO), (largura//2-350, 200))
        pygame.draw.rect(tela, VERDE_BTN, (440, 350, 400, 100), border_radius=15)
        tela.blit(fonte_txt.render("JOGAR", True, BRANCO), (largura//2-40, 388))
    elif sala == 2:
        status = f"Bombas: {p1_status['bombas_max']}  Alcance: {p1_status['alcance']}  Velocidade: {p1_status['itens_v']}"
        tela.blit(fonte_txt.render(status, True, BRANCO), (off_x, 25))
        tela.blit(fonte_txt.render(f"Vivos: {len(bots)+1}", True, BRANCO), (off_x + 700, 25))
        pygame.draw.rect(tela, GRAMA, (off_x, off_y, mapa_l*tile_size, mapa_a*tile_size))
        for l in range(mapa_a):
            for c in range(mapa_l):
                px, py = off_x + c * tile_size, off_y + l * tile_size
                if mapa_jogo[l][c] == 1: pygame.draw.rect(tela, PEDRA, (px, py, tile_size-2, tile_size-2))
                elif mapa_jogo[l][c] == 2: pygame.draw.rect(tela, MADEIRA, (px, py, tile_size-2, tile_size-2))
        for it in itens:
            ix, iy = off_x + it["pos"][1]*tile_size + 12, off_y + it["pos"][0]*tile_size + 12
            pygame.draw.rect(tela, VERDE_ITEM, (ix, iy, 40, 40), border_radius=5)
            tela.blit(fonte_item.render(it["tipo"], True, PRETO), (ix + 15, iy + 10))
        for b in bombas: pygame.draw.circle(tela, PRETO, (off_x + b[1]*tile_size + 32, off_y + b[0]*tile_size + 32), 20)
        for e in explosoes: pygame.draw.rect(tela, FOGO, (off_x + e[1]*tile_size, off_y + e[0]*tile_size, tile_size, tile_size))
        pygame.draw.rect(tela, P1_COR, (off_x + p1_pos[1]*tile_size+12, off_y + p1_pos[0]*tile_size+12, 40, 40))
        for bot in bots: pygame.draw.rect(tela, BOT_COR, (off_x + bot["pos"][1]*tile_size+12, off_y + bot["pos"][0]*tile_size+12, 40, 40))
    elif sala in [3, 4]:
        msg = "DERROTA!" if sala == 3 else "VITÓRIA!"
        tela.fill((50, 0, 0) if sala == 3 else (0, 50, 0))
        tela.blit(fonte_titulo.render(msg, True, BRANCO), (largura//2-180, 200))
        pygame.draw.rect(tela, BRANCO, (440, 450, 400, 80), 2, border_radius=10)
        tela.blit(fonte_txt.render("VOLTAR AO MENU", True, BRANCO), (largura//2-100, 478))
    pygame.display.flip()
    relogio.tick(60)
pygame.quit()