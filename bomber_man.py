import pygame
import random
import math
import os

# inicialização
pygame.init()
pygame.mixer.init()
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
LARANJA, AMARELO = (255, 140, 0), (255, 255, 0)
P1_COR, P2_COR, BOT_COR = (30, 30, 155), (200, 30, 30), (200, 0, 200)
BRANCO, PRETO, VERDE_ITEM = (255, 255, 255), (0, 0, 0), (50, 200, 50)
AZUL_BOTAO, AZUL_TEXTO = (20, 40, 80), (150, 200, 255)

# Audio (eu mudei o volume global para 0.5 pra ouvir melhor)
volume_global = 0.5
musica_atual = ""

try:
    def carregar_som(nome):
        caminho = os.path.join("sons", nome)
        if os.path.exists(caminho):
            s = pygame.mixer.Sound(caminho)
            s.set_volume(volume_global)
            return s
        return None

    som_explosao = carregar_som("explosao.wav")
    som_item = carregar_som("pegar_item.mp3")
    som_creeper = carregar_som("creeper_chiado.mp3")
    
    musica_menu = os.path.join("sons", "musica_menu.wav")
    musica_jogo = os.path.join("sons", "musica_tema.mp3")
    musica_vitoria = os.path.join("sons", "musica_vitoria.mp3")
    musica_derrota = os.path.join("sons", "musica_derrota.mp3")
    
    def tocar_musica(caminho, loop=-1):
        global musica_atual
        if musica_atual != caminho and os.path.exists(caminho):
            pygame.mixer.music.stop()
            pygame.mixer.music.load(caminho)
            pygame.mixer.music.set_volume(volume_global)
            pygame.mixer.music.play(loop)
            musica_atual = caminho

    def atualizar_volumes():
        pygame.mixer.music.set_volume(volume_global)
        for s in [som_explosao, som_item, som_creeper]:
            if s: s.set_volume(volume_global)
except Exception as e:
    print(f"Erro no áudio: {e}")

# Carregamento das sprites
try:
    def carregar(nome, tamanho=(56, 56)):
        caminho = os.path.join("sprites", nome)
        if os.path.exists(caminho):
            img = pygame.image.load(caminho).convert_alpha()
            return pygame.transform.scale(img, tamanho)
        return None

    capa_img = carregar("Tela_de_inicio.png", (largura, altura))
    p1_anim = {
        "cima": carregar("Gabimaru_costa.png"), "baixo": carregar("Gabimaru_frente.png"),
        "esquerda": carregar("Gabimaru_esquerda.png"), "direita": carregar("Gabimaru_direita.png")
    }
    spr_itens = {
        "V": carregar("item_velocidade.png", (54, 54)),
        "B": carregar("item_bomba.png", (54, 54)),
        "A": carregar("item_alcance.png", (54, 54))
    }
    sprite_pedra = carregar("bloco_indestrutivel.png", (64, 64))
    sprite_madeira = carregar("caixa_madeira.png", (64, 64))
    sprite_grama = carregar("grama.png", (64, 64))
    tem_sprites = True
except Exception as e:
    print(f"Erro sprites: {e}")
    tem_sprites = False

# Configurações do mapa
tile_size = 64
mapa_l, mapa_a = 15, 11
off_x = (largura - (mapa_l * tile_size)) // 2
off_y = 80 

# Retângulos de interface
rect_btn_start = pygame.Rect(largura//2 - 150, 600, 300, 80)
rect_btn_ajustes = pygame.Rect(largura - 200, 20, 180, 50)
rect_btn_voltar_ajuste = pygame.Rect(largura//2 - 100, 550, 200, 60)
rect_slider_fundo = pygame.Rect(largura//2 - 200, altura//2, 400, 20)

def resetar_jogo():
    global p1_pos, p2_pos, bombas, explosoes, bots, mapa_jogo, itens, p1_status, p2_status, tempo_mov_p1, tempo_mov_p2, vencedor, ultima_dir_p1, ultima_dir_p2
    p1_pos, p2_pos = [1, 1], [9, 13]
    bombas, explosoes, itens = [], [], []
    tempo_mov_p1 = tempo_mov_p2 = 0
    vencedor, ultima_dir_p1, ultima_dir_p2 = "", "baixo", "baixo"
    p1_status = {"bombas_max": 1, "alcance": 2, "velocidade": 180, "vivo": True}
    p2_status = {"bombas_max": 1, "alcance": 2, "velocidade": 180, "vivo": True}
    zonas_seguras = [(1,1), (1,2), (2,1), (9,13), (9,12), (8,13)]
    mapa_jogo = []
    for l in range(mapa_a):
        linha = []
        for c in range(mapa_l):
            if l == 0 or l == mapa_a-1 or c == 0 or c == mapa_l-1 or (l % 2 == 0 and c % 2 == 0): linha.append(1)
            elif (l, c) in zonas_seguras: linha.append(0)
            elif random.random() < 0.6: linha.append(2)
            else: linha.append(0)
        mapa_jogo.append(linha)
    bots = []
    if modo_jogo == "single":
        bots = [{"pos": [1, 13], "dir": [0, -1], "last": 0, "alcance": 2},
                {"pos": [9, 1], "dir": [0, 1], "last": 0, "alcance": 2},
                {"pos": [9, 13], "dir": [-1, 0], "last": 0, "alcance": 2}]

def esta_livre(l, c):
    if not (0 <= l < mapa_a and 0 <= c < mapa_l) or mapa_jogo[l][c] != 0: return False
    for b in bombas:
        if b[0] == l and b[1] == c: return False
    return True

def eh_perigoso(l, c):
    for b in bombas:
        alc = b[4]
        if (b[0] == l and abs(b[1] - c) <= alc) or (b[1] == c and abs(b[0] - l) <= alc): return True
    for e in explosoes:
        if e[0] == l and e[1] == c: return True
    return False

def disparar_explosao(lin, col, alcance):
    agora_ms = pygame.time.get_ticks()
    explosoes.append([lin, col, agora_ms + 500, 500])
    if som_explosao: som_explosao.play()
    direcoes = [(0,1), (0,-1), (1,0), (-1,0)]
    for dl, dc in direcoes:
        for i in range(1, alcance + 1): 
            nl, nc = lin + dl*i, col + dc*i
            if 0 <= nl < mapa_a and 0 <= nc < mapa_l:
                if mapa_jogo[nl][nc] == 1: break 
                explosoes.append([nl, nc, agora_ms + 500, 500])
                if mapa_jogo[nl][nc] == 2:
                    mapa_jogo[nl][nc] = 0 
                    if random.random() < 0.3:
                        itens.append({"pos": [nl, nc], "tipo": random.choice(["A", "V", "B"])})
                    break

sala = 0  
modo_jogo = ""
rodando = True
ultima_dir_p1 = "baixo"
ultima_dir_p2 = "baixo"

while rodando:
    agora = pygame.time.get_ticks()
    pos_mouse = pygame.mouse.get_pos()
    eventos = pygame.event.get()
    
    for evento in eventos:
        if evento.type == pygame.QUIT: 
            rodando = False
        
        if evento.type == pygame.MOUSEBUTTONDOWN:
            if sala == 0:
                if rect_btn_start.collidepoint(evento.pos): sala = 1
                if rect_btn_ajustes.collidepoint(evento.pos): sala = 7
            elif sala == 1:
                rect_s = pygame.Rect(largura//2-200, 300, 400, 80)
                rect_m = pygame.Rect(largura//2-200, 450, 400, 80)
                if rect_s.collidepoint(evento.pos): 
                    modo_jogo = "single"
                    resetar_jogo()
                    sala = 2
                elif rect_m.collidepoint(evento.pos): 
                    modo_jogo = "multi"
                    resetar_jogo()
                    sala = 2
            elif sala == 7:
                if rect_btn_voltar_ajuste.collidepoint(evento.pos): sala = 0
            elif sala in [3, 4, 5, 6]:
                rect_v = pygame.Rect(largura//2 - 200, 450, 400, 80)
                if rect_v.collidepoint(evento.pos): sala = 0

        if evento.type == pygame.KEYDOWN:
            # Tecla ESC para voltar ao menu principal
            if sala == 1 and evento.key == pygame.K_ESCAPE:
                sala = 0
            
            if sala == 2:
                # Bomba P1 (Espaço)
                if evento.key == pygame.K_SPACE and p1_status["vivo"]:
                    if len([b for b in bombas if b[3] == "p1"]) < p1_status["bombas_max"]:
                        if not any(b[0] == p1_pos[0] and b[1] == p1_pos[1] for b in bombas):
                            bombas.append([p1_pos[0], p1_pos[1], agora, "p1", p1_status["alcance"]])
                            if som_creeper: som_creeper.play()
                
                # Bomba P2 (Shift Esquerdo)
                if evento.key == pygame.K_LSHIFT and modo_jogo == "multi" and p2_status["vivo"]:
                    if len([b for b in bombas if b[3] == "p2"]) < p2_status["bombas_max"]:
                        if not any(b[0] == p2_pos[0] and b[1] == p2_pos[1] for b in bombas):
                            bombas.append([p2_pos[0], p2_pos[1], agora, "p2", p2_status["alcance"]])
                            if som_creeper: som_creeper.play()

    if sala == 7 and pygame.mouse.get_pressed()[0]:
        if rect_slider_fundo.inflate(0, 20).collidepoint(pos_mouse):
            volume_global = max(0, min(1, (pos_mouse[0] - rect_slider_fundo.x) / rect_slider_fundo.width))
            atualizar_volumes()
        
    # Separação da musica por sala
    if sala in [0, 1, 7]: 
        tocar_musica(musica_menu)
    elif sala == 2: 
        tocar_musica(musica_jogo)
    elif sala in [3, 6]: 
        tocar_musica(musica_derrota, loop=0)
    elif sala in [4, 5]: 
        tocar_musica(musica_vitoria, loop=0)

    if sala == 2:
        teclas = pygame.key.get_pressed()
        
        # Movimento P1 (Setas)
        if p1_status["vivo"] and agora - tempo_mov_p1 > p1_status["velocidade"]:
            nl, nc = p1_pos[0], p1_pos[1]
            if teclas[pygame.K_UP]: nl -= 1; ultima_dir_p1 = "cima"
            elif teclas[pygame.K_DOWN]: nl += 1; ultima_dir_p1 = "baixo"
            elif teclas[pygame.K_LEFT]: nc -= 1; ultima_dir_p1 = "esquerda"
            elif teclas[pygame.K_RIGHT]: nc += 1; ultima_dir_p1 = "direita"
            
            if [nl, nc] != p1_pos and esta_livre(nl, nc): 
                p1_pos = [nl, nc]
                tempo_mov_p1 = agora
                for it in itens[:]:
                    if it["pos"] == p1_pos:
                        if it["tipo"] == "V": p1_status["velocidade"] = max(80, p1_status["velocidade"] - 20)
                        elif it["tipo"] == "B": p1_status["bombas_max"] += 1
                        elif it["tipo"] == "A": p1_status["alcance"] += 1
                        itens.remove(it)
                        if som_item: som_item.play()

        # Movimento P2 (WASD)
        if modo_jogo == "multi" and p2_status["vivo"] and agora - tempo_mov_p2 > p2_status["velocidade"]:
            nl, nc = p2_pos[0], p2_pos[1]
            if teclas[pygame.K_w]: nl -= 1; ultima_dir_p2 = "cima"
            elif teclas[pygame.K_s]: nl += 1; ultima_dir_p2 = "baixo"
            elif teclas[pygame.K_a]: nc -= 1; ultima_dir_p2 = "esquerda"
            elif teclas[pygame.K_d]: nc += 1; ultima_dir_p2 = "direita"
            
            if [nl, nc] != p2_pos and esta_livre(nl, nc): 
                p2_pos = [nl, nc]
                tempo_mov_p2 = agora
                for it in itens[:]:
                    if it["pos"] == p2_pos:
                        if it["tipo"] == "V": p2_status["velocidade"] = max(80, p2_status["velocidade"] - 20)
                        elif it["tipo"] == "B": p2_status["bombas_max"] += 1
                        elif it["tipo"] == "A": p2_status["alcance"] += 1
                        itens.remove(it)
                        if som_item: som_item.play()

        # Bombas e IA
        for b in bombas[:]:
            if agora - b[2] > 2000: disparar_explosao(b[0], b[1], b[4]); bombas.remove(b)
        explosoes = [e for e in explosoes if agora < e[2]]
        
        if modo_jogo == "single":
            for bot in bots:
                if agora - bot["last"] > 550:
                    l, c = bot["pos"]; dircs = [(0,1), (0,-1), (1,0), (-1,0)]
                    poss = [d for d in dircs if esta_livre(l + d[0], c + d[1])]
                    segs = [d for d in poss if not eh_perigoso(l + d[0], c + d[1])]
                    escolha = random.choice(segs if segs else (poss if poss else [(0,0)]))
                    bot["pos"] = [l + escolha[0], c + escolha[1]]; bot["last"] = agora
                    if not eh_perigoso(l, c) and random.random() < 0.08:
                        bombas.append([l, c, agora, "bot", bot["alcance"]])
                        if som_creeper: som_creeper.play()

        # Mortes e Fim de Jogo
        for f in explosoes:
            if f[0] == p1_pos[0] and f[1] == p1_pos[1]: p1_status["vivo"] = False
            if modo_jogo == "multi" and f[0] == p2_pos[0] and f[1] == p2_pos[1]: p2_status["vivo"] = False
            for bot in bots[:]:
                if f[0] == bot["pos"][0] and f[1] == bot["pos"][1]: bots.remove(bot)
        
        if modo_jogo == "single":
            if not p1_status["vivo"]: sala = 3
            elif not bots: sala = 4
        else:
            if not p1_status["vivo"] and not p2_status["vivo"]: sala = 3
            elif not p1_status["vivo"]: sala = 6
            elif not p2_status["vivo"]: sala = 5

    tela.fill((30, 30, 30))
    
    if sala == 0:
        if tem_sprites: tela.blit(capa_img, (0, 0))
        pygame.draw.rect(tela, AZUL_BOTAO, rect_btn_start, border_radius=15)
        txt = fonte_txt.render("START GAME", True, AZUL_TEXTO)
        tela.blit(txt, txt.get_rect(center=rect_btn_start.center))
        pygame.draw.rect(tela, (50, 50, 50), rect_btn_ajustes, border_radius=10)
        tela.blit(fonte_txt.render("AJUSTES", True, BRANCO), fonte_txt.render("AJUSTES", True, BRANCO).get_rect(center=rect_btn_ajustes.center))

    elif sala == 7:
        tela.fill((20, 20, 20))
        pygame.draw.rect(tela, (60, 60, 60), rect_slider_fundo, border_radius=10)
        pygame.draw.rect(tela, AZUL_TEXTO, (rect_slider_fundo.x, rect_slider_fundo.y, int(rect_slider_fundo.width * volume_global), 20), border_radius=10)
        t_vol = fonte_txt.render(f"VOLUME: {int(volume_global*100)}%", True, BRANCO)
        tela.blit(t_vol, (largura//2-70, altura//2-50))
        pygame.draw.rect(tela, AZUL_BOTAO, rect_btn_voltar_ajuste, border_radius=10)
        tela.blit(fonte_txt.render("VOLTAR", True, BRANCO), fonte_txt.render("VOLTAR", True, BRANCO).get_rect(center=rect_btn_voltar_ajuste.center))

    elif sala == 1:
        if tem_sprites: tela.blit(capa_img, (0, 0))
        overlay = pygame.Surface((largura, altura)); overlay.set_alpha(180); overlay.fill((0,0,0)); tela.blit(overlay, (0,0))
        rect_s = pygame.Rect(largura//2-200, 300, 400, 80); rect_m = pygame.Rect(largura//2-200, 450, 400, 80)
        pygame.draw.rect(tela, AZUL_BOTAO, rect_s, border_radius=15)
        tela.blit(fonte_txt.render("SINGLE PLAYER", True, AZUL_TEXTO), fonte_txt.render("SINGLE PLAYER", True, AZUL_TEXTO).get_rect(center=rect_s.center))
        pygame.draw.rect(tela, AZUL_BOTAO, rect_m, border_radius=15)
        tela.blit(fonte_txt.render("MULTIPLAYER", True, AZUL_TEXTO), fonte_txt.render("MULTIPLAYER", True, AZUL_TEXTO).get_rect(center=rect_m.center))
        tela.blit(fonte_txt.render("ESC para voltar", True, BRANCO), (largura//2-80, 580))

    elif sala == 2:
        for l in range(mapa_a):
            for c in range(mapa_l):
                px, py = off_x + c * tile_size, off_y + l * tile_size
                if tem_sprites: tela.blit(sprite_grama, (px, py))
                if mapa_jogo[l][c] == 1: tela.blit(sprite_pedra, (px, py))
                elif mapa_jogo[l][c] == 2: tela.blit(sprite_madeira, (px, py))
        
        for it in itens:
            spr = spr_itens.get(it["tipo"])
            if spr: tela.blit(spr, (off_x + it["pos"][1]*tile_size+5, off_y + it["pos"][0]*tile_size+5))

        for b in bombas:
            rd = 22 + int(math.sin(agora * 0.01) * 5)
            pygame.draw.circle(tela, PRETO, (off_x + b[1]*tile_size + 32, off_y + b[0]*tile_size + 32), rd)
            pygame.draw.circle(tela, (60, 60, 60), (off_x + b[1]*tile_size + 28, off_y + b[0]*tile_size + 28), rd // 3)

        for e in explosoes:
            tm = int(tile_size * ((e[2] - agora) / e[3]))
            if tm > 0:
                m = (tile_size - tm) // 2
                xb, yb = off_x + e[1]*tile_size + m, off_y + e[0]*tile_size + m
                pygame.draw.rect(tela, FOGO, (xb, yb, tm, tm))
                pygame.draw.rect(tela, LARANJA, (xb+tm//4, yb+tm//4, tm//2, tm//2))
                pygame.draw.rect(tela, AMARELO, (xb+tm//3, yb+tm//3, tm//3, tm//3))

        if p1_status["vivo"]:
            tela.blit(p1_anim.get(ultima_dir_p1), (off_x + p1_pos[1]*tile_size+4, off_y + p1_pos[0]*tile_size+4))
        
        if modo_jogo == "multi" and p2_status["vivo"]:
            pygame.draw.rect(tela, P2_COR, (off_x + p2_pos[1]*tile_size+12, off_y + p2_pos[0]*tile_size+12, 40, 40))
        
        if modo_jogo == "single":
            for bot in bots: pygame.draw.rect(tela, BOT_COR, (off_x + bot["pos"][1]*tile_size+12, off_y + bot["pos"][0]*tile_size+12, 40, 40))

    elif sala in [3, 4, 5, 6]:
        cores = {3: (50,0,0), 4: (0,50,0), 5: (0,50,100), 6: (100,0,0)}
        msgs = {3: "DERROTA!", 4: "VITÓRIA!", 5: "P1 VENCEU!", 6: "P2 VENCEU!"}
        tela.fill(cores[sala])
        t_msg = fonte_titulo.render(msgs[sala], True, BRANCO)
        tela.blit(t_msg, t_msg.get_rect(center=(largura//2, 250)))
        rv = pygame.Rect(largura//2-200, 450, 400, 80)
        pygame.draw.rect(tela, BRANCO, rv, 2, border_radius=10)
        tela.blit(fonte_txt.render("VOLTAR AO MENU", True, BRANCO), fonte_txt.render("VOLTAR AO MENU", True, BRANCO).get_rect(center=rv.center))

    pygame.display.flip()
    relogio.tick(60)

pygame.quit()