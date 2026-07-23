from collections import deque
import math
import numpy as np
import urenderer
from OpenGL import GL

# Importações dos módulos internos do renderizador
from urenderer.node import Node, Light, LightType
from urenderer.renderer.opengl import Material, Texture
from urenderer.geometry.mesh.cube import get_mesh_cube
from urenderer.geometry.mesh.glb import load_glb  

# Nome da cena utilizado para salvar diretórios de trabalho e renderizar o vídeo
NOME_DA_CENA = "tatico_vitoria_433"


# =================================--------------------------------------------
# 1. FUNÇÕES DE ANIMAÇÃO (CALLBACKS DO GRAFO DE CENA)
# =================================--------------------------------------------

def animar_camera_estadio(node: Node, deltaTime: float, time_since_start: float) -> None:
    """
    Callback aplicado ao nó raiz da cena para animar a câmera.
    Cria um efeito de sobrevoo panorâmico contínuo ao redor do estádio.
    """
    # Rotação progressiva no eixo Y (azimute) para orbitar o estádio
    node.rotation[1] = -25.0 + (time_since_start * 3.0) 
    
    # Oscilação senoidal suave no eixo X (elevação/inclinação) para dar dinamismo
    node.rotation[0] = 15.0 + math.sin(time_since_start * 1.5) * 3.0


def animar_jogadores(node: Node, deltaTime: float, time_since_start: float) -> None:
    """
    Callback aplicado individualmente a cada jogador.
    Gerencia a alternância cíclica de jogadas táticas e adiciona movimentações
    procedurais de corrida (passadas e gingado).
    """
    # Recupera o identificador do atleta e sua posição tática original do nó
    idx = node.render_data.get("idx", -1)
    base_pos = node.render_data.get("base_pos", np.array([0.0, 0.0, 0.0], dtype=np.float32))

    # --- CONTROLE DO CICLO TEMPORAL DAS JOGADAS ---
    tempo_jogada = 4.0                       # Duração da fase de ataque + retorno (4s)
    tempo_total_ciclo = tempo_jogada * 2.0   # Duração total do ciclo (Jogada 1 + Jogada 2 = 8s)
    
    # Tempo relativo dentro do ciclo atual [0, 8s)
    t = time_since_start % tempo_total_ciclo
    
    # Cálculo da interpolação suave (curva cosseno) para ida (0 -> 1) e volta (1 -> 0)
    if t < tempo_jogada:
        jogada_ativa = 1
        fator = (1.0 - math.cos((t / tempo_jogada) * 2.0 * math.pi)) / 2.0
    else:
        jogada_ativa = 2
        t_fase2 = t - tempo_jogada
        fator = (1.0 - math.cos((t_fase2 / tempo_jogada) * 2.0 * math.pi)) / 2.0

    offset_tatico = np.array([0.0, 0.0, 0.0], dtype=np.float32)

    # --- CONFIGURAÇÃO DOS DESLOCAMENTOS DA JOGADA 1 (Ataque pela Direita) ---
    if jogada_ativa == 1:
        if idx == 4:    # Lateral Direito: Projeção até a linha de fundo
            offset_tatico = np.array([-0.5, 0.0, -22.0], dtype=np.float32)
        elif idx == 1:  # Lateral Esquerdo: Basculação interna (linha de 3)
            offset_tatico = np.array([2.5, 0.0, 0.5], dtype=np.float32)
        elif idx == 2:  # Zagueiro Esquerdo: Cobertura central
            offset_tatico = np.array([2.0, 0.0, 0.0], dtype=np.float32)
        elif idx == 3:  # Zagueiro Direito: Cobertura do setor do LD
            offset_tatico = np.array([2.0, 0.0, -1.0], dtype=np.float32)
        elif idx == 1:  # (Atribuição redundante mantida)
            offset_tatico = np.array([2.0, 0.0, 1.0], dtype=np.float32)
        elif idx == 6:  # Meia Esquerdo: Dá amplitude no lado oposto
            offset_tatico = np.array([-2.5, 0.0, -1.0], dtype=np.float32)
        elif idx == 7:  # Meia Direito: Apoio à subida do lateral
            offset_tatico = np.array([2.5, 0.0, -1.0], dtype=np.float32)
        elif idx == 8:  # Ponta Esquerdo: Diagonal em direção à área
            offset_tatico = np.array([4.5, 0.0, -6.0], dtype=np.float32)
        elif idx == 9:  # Ponta Direito: Movimento para o meio (libera corredor)
            offset_tatico = np.array([-4.5, 0.0, -2.0], dtype=np.float32)
        elif idx == 10: # Centroavante: Infiltração na grande área
            offset_tatico = np.array([2.0, 0.0, -5.0], dtype=np.float32)

    # --- CONFIGURAÇÃO DOS DESLOCAMENTOS DA JOGADA 2 (Ataque pela Esquerda) ---
    elif jogada_ativa == 2:
        if idx == 1:    # Lateral Esquerdo: Projeção até a linha de fundo
            offset_tatico = np.array([0.5, 0.0, -22.0], dtype=np.float32)
        elif idx == 4:  # Lateral Direito: Basculação interna (linha de 3)
            offset_tatico = np.array([-2.5, 0.0, 0.5], dtype=np.float32)
        elif idx == 3:  # Zagueiro Direito: Cobertura central
            offset_tatico = np.array([-1.5, 0.0, 0.0], dtype=np.float32)
        elif idx == 2:  # Zagueiro Esquerdo: Cobertura do setor do LE
            offset_tatico = np.array([-2.0, 0.0, -1.0], dtype=np.float32)
        elif idx == 8:  # Ponta Esquerdo: Infiltração em diagonal
            offset_tatico = np.array([4.5, 0.0, -2.0], dtype=np.float32)
        elif idx == 5:  # Volante: Aproximação à entrada da área
            offset_tatico = np.array([0.0, 0.0, -4.0], dtype=np.float32)
        elif idx == 10: # Centroavante: Movimentação no primeiro pau
            offset_tatico = np.array([-2.0, 0.0, -5.0], dtype=np.float32)

    # 1. Aplica o deslocamento tático interpolado sobre o plano do campo (XZ)
    pos_tatica = base_pos + (offset_tatico * fator)
    node.translation[0] = pos_tatica[0]
    node.translation[2] = pos_tatica[2]

    # 2. Animação de flutuação vertical no eixo Y (simulação do salto da passada)
    node.translation[1] = pos_tatica[1] + math.sin(4 * time_since_start) * 0.15

    # 3. Animação procedural do corpo durante a corrida (inclinação frontal e lateral)
    node.rotation[0] = math.sin(6 * time_since_start) * 12.0
    node.rotation[2] = math.cos(6 * time_since_start) * 2.0


# =================================--------------------------------------------
# 2. CONFIGURAÇÃO E EXECUÇÃO DA CENA PRINCIPAL
# =================================--------------------------------------------

if __name__ == "__main__":
    # Limpa o diretório de arquivos temporários do projeto
    urenderer.utils.clear_workdir(NOME_DA_CENA)
    
    # -------------------------------------------------------------------------
    # SETUP DO RENDERIZADOR E CÂMERA OPENGL
    # -------------------------------------------------------------------------
    width, height = 1920, 1080
    renderer = urenderer.renderer.OpenGLRenderer(width, height)
    
    # Cor do céu/fundo (estilo ambiente noturno) e iluminação ambiente PBR
    renderer.background_color = np.array([0.05, 0.05, 0.05, 1.0], np.float32)
    renderer.ambient_color = np.array([0.25, 0.25, 0.25], dtype=np.float32)
    
    # Instancia o Runtime com configuração de perspectiva da câmera
    runtime = urenderer.application.Runtime(renderer, name=NOME_DA_CENA)
    runtime.camera.vertical_fov = 60.0
    runtime.camera.far_plane = 100.0
    
    # -------------------------------------------------------------------------
    # SHADERS E CARREGAMENTO DE TEXTURAS
    # -------------------------------------------------------------------------
    shader = urenderer.renderer.Shader("assets/vertex.vs", "assets/05-fragment.fs")
    
    # Texturas monocromáticas auxiliares de 1x1 pixel (para canais PBR padrão)
    blackTextureR = Texture(np.zeros((1, 1), np.uint8), GL.GL_RED, GL.GL_R8)
    whiteTextureR = Texture(255 * np.ones((1, 1), np.uint8), GL.GL_RED, GL.GL_R8)
    
    # Texturas PBR do gramado
    textura_gramado = Texture.load_file("assets/grass/Grass001_1K-PNG_Color.png", srgb=True, drop_alpha=True)
    textura_gramado_rough = Texture.load_file("assets/grass/Grass001_1K-PNG_Roughness.png", drop_alpha=True)
    textura_gramado_normal = Texture.load_file("assets/grass/Grass001_1K-PNG_NormalGL.png", drop_alpha=True)
    
    # Texturas do escudo/placar e uniformes
    logo_vitoria = Texture.load_file("assets/vitoria_bandeira.jpg", srgb=True, drop_alpha=False)
    textura_uniforme = Texture.load_file("assets/camisa_vitoria.png", srgb=True, drop_alpha=True)

    # -------------------------------------------------------------------------
    # MATERIAIS PBR DOS OBJETOS
    # -------------------------------------------------------------------------
    textura_atlas = Texture.load_file("assets/textura_base.png", srgb=True, drop_alpha=True)

    # Material das arquibancadas
    material_arquibancada = Material(shader)
    material_arquibancada.set_texture(0, "baseColorTexture", textura_uniforme)
    material_arquibancada.set_texture(1, "metallicTexture", blackTextureR)    
    material_arquibancada.set_texture(2, "roughnessTexture", whiteTextureR)  
    material_arquibancada.set_uniform("tiling", 1.0)

    # Material dos jogadores com rugosidade média para simular tecido/pele
    roughness_media = Texture(np.full((1, 1), 100, dtype=np.uint8), GL.GL_RED, GL.GL_R8)
    material_jogador = Material(shader)
    material_jogador.set_texture(0, "baseColorTexture", textura_atlas)
    material_jogador.set_texture(1, "metallicTexture", blackTextureR)   
    material_jogador.set_texture(2, "roughnessTexture", roughness_media)  
    material_jogador.set_uniform("tiling", 1.0) 

    # Material PBR do gramado
    material_campo = Material(shader)
    material_campo.set_texture(0, "baseColorTexture", textura_gramado)
    material_campo.set_texture(1, "metallicTexture", blackTextureR)
    material_campo.set_texture(2, "roughnessTexture", textura_gramado_rough)
    material_campo.set_texture(3, "normalTexture", textura_gramado_normal) 
    material_campo.set_uniform("tiling", 12.0)
    
    # Material do placar/bandeira do Vitória
    material_logo = Material(shader)
    material_logo.set_texture(0, "baseColorTexture", logo_vitoria)
    material_logo.set_texture(1, "metallicTexture", blackTextureR)
    material_logo.set_texture(2, "roughnessTexture", whiteTextureR)
    material_logo.set_uniform("tiling", 1.0)
    
    # -------------------------------------------------------------------------
    # MONTAGEM DO GRAFO DE CENA
    # -------------------------------------------------------------------------
    cena_root = Node(name="Cena_Principal")

    # Gramado (Cubo achatado e dimensionado)
    no_campo = Node(name="Gramado")
    no_campo.render_data["mesh"] = get_mesh_cube()
    no_campo.render_data["material"] = material_campo
    no_campo.scale = np.array([30.0, 0.05, 35.0], dtype=np.float32)
    no_campo.translation = np.array([-4.5, -8.0, -3.0], dtype=np.float32)
    no_campo.rotation = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    cena_root.add_child(no_campo)

    # --- ARQUIBANCADA 1 (Lado Direito) ---
    no_arquibancada = load_glb("assets/estrutura_arquibancada_02.glb")
    no_arquibancada.name = "Arquibancada1"
    no_arquibancada.scale = np.array([0.01, 0.01, 0.01], dtype=np.float32)
    no_arquibancada.translation = np.array([11.0, -8.0, 16.0], dtype=np.float32)
    no_arquibancada.rotation = np.array([-90.0, 0.0, 0.0], dtype=np.float32)
    
    # Percurso em largura (BFS) para atrelar o material a todas as submalhas da Arquibancada 1
    fila_arq1 = deque([no_arquibancada])
    while len(fila_arq1) > 0:
        atual = fila_arq1.popleft()
        if "mesh" in atual.render_data:
            atual.render_data["material"] = material_arquibancada
        for child in atual.children:
            fila_arq1.append(child)
    cena_root.add_child(no_arquibancada)

    # --- ARQUIBANCADA 2 (Lado Esquerdo Invertido) ---
    no_arquibancada2 = load_glb("assets/estrutura_arquibancada_02.glb")
    no_arquibancada2.name = "Arquibancada2"
    no_arquibancada2.scale = np.array([0.01, 0.01, 0.01], dtype=np.float32)
    no_arquibancada2.translation = np.array([-20.0, -8.0, -35.0], dtype=np.float32) 
    no_arquibancada2.rotation = np.array([-90.0, 0.0, 180.0], dtype=np.float32) 
    
    # Percurso BFS para atrelar o material a todas as submalhas da Arquibancada 2
    fila_arq2 = deque([no_arquibancada2])
    while len(fila_arq2) > 0:
        atual = fila_arq2.popleft()
        if "mesh" in atual.render_data:
            atual.render_data["material"] = material_arquibancada
        for child in atual.children:
            fila_arq2.append(child)
    cena_root.add_child(no_arquibancada2)

    # (Bloco de código comentado mantido conforme original)
    # no_arquibancada_frontal = load_glb("assets/estrutura_arquibancada_02.glb")
    # no_arquibancada_frontal.name = "ArquibancadaFrontal"
    # no_arquibancada_frontal.scale = np.array([0.005, 0.01, 0.005], dtype=np.float32)
    # no_arquibancada_frontal.translation = np.array([0.0, -10.0, 15.0], dtype=np.float32)
    # no_arquibancada_frontal.rotation = np.array([-90.0, 0.0, 90.0], dtype=np.float32)
    # fila_arq_frontal = deque([no_arquibancada_frontal])
    # while len(fila_arq_frontal) > 0:
    #     atual = fila_arq_frontal.popleft()
    #     if "mesh" in atual.render_data:
    #         atual.render_data["material"] = material_jogador
    #     for child in atual.children:
    #         fila_arq_frontal.append(child)
    # cena_root.add_child(no_arquibancada_frontal)
    # no_campo = load_glb("assets/low_poly_football_pitch.glb")
    # no_campo.name = "Estadio_Campo"
    # no_campo.scale = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    # no_campo.translation = np.array([0.0, -0.025, 0.0], dtype=np.float32)
    # cena_root.add_child(no_campo)

    # Validação defensiva de materiais não atribuídos
    from collections import deque
    fila_campo = deque([no_arquibancada])
    while len(fila_campo) > 0:
        atual = fila_campo.popleft()
        if "mesh" in atual.render_data and "material" not in atual.render_data:
            atual.render_data["material"] = material_campo 
        for filho in atual.children:
            fila_campo.append(filho)

    # O Placar / Escudo do Vitória ao fundo
    no_logo = Node(name="Placar")
    no_logo.render_data["mesh"] = get_mesh_cube()
    no_logo.render_data["material"] = material_logo
    no_logo.scale = np.array([36.0, 22.0, 0.2], dtype=np.float32)
    no_logo.translation = np.array([-5.0, 2.0, -35.0], dtype=np.float32)
    no_logo.rotation = np.array([0.0, 0.0, 0.0], dtype=np.float32) 
    cena_root.add_child(no_logo)
    
    # Coordenadas iniciais no esquema tático 4-3-3
    posicoes_433 = [
        (-5.0, -7.5, 10.0),     # Goleiro 
        (-12.5, -7.5, 5.0),    # Lateral Esq
        (-8.0, -7.5, 6.0),     # Zag Esq
        (-2.0, -7.5, 6.0),     # Zag Dir
        (2.5, -7.5, 5.0),      # Lateral Dir
        (-5.0, -7.5, 3.0),      # Volante
        (-10.0, -7.5, -1.5),   # Meia Esq
        (0.0, -7.5, -1.5),      # Meia Dir
        (-12.0, -7.5, -5.0),   # Ponta Esq
        (2.0, -7.5, -5.0),      # Ponta Dir
        (-5.0, -7.5, -10.0)    # Centroavante 
    ]
    
    time_node = Node(name="Time_Vitoria")
    cena_root.add_child(time_node)
    
    # Instanciação e posicionamento dos 11 jogadores
    for idx, pos in enumerate(posicoes_433):
        jogador_root = load_glb("assets/low_poly_soccer_player.glb")
        jogador_root.name = f"Jogador_{idx}"
        jogador_root.translation = np.array(pos, dtype=np.float32)
        
        # Guarda índice e posição de origem para uso dentro do callback de animação
        jogador_root.render_data["idx"] = idx
        jogador_root.render_data["base_pos"] = np.array(pos, dtype=np.float32)
        
        jogador_root.scale = np.array([0.015, 0.015, 0.015], dtype=np.float32)
        jogador_root.rotation = np.array([0.0, 0.0, 0.0], dtype=np.float32) 
        jogador_root.callbacks = [animar_jogadores]
        
        # Percurso BFS para aplicar o material dos atletas em suas submalhas
        fila_de_nos = deque([jogador_root])
        while len(fila_de_nos) > 0:
            no_atual = fila_de_nos.popleft()
            if "mesh" in no_atual.render_data:
                no_atual.render_data["material"] = material_jogador 
            for child in no_atual.children:
                fila_de_nos.append(child)
                
        time_node.add_child(jogador_root)
        
    # Posição inicial do nó pai da cena (controla a perspectiva da câmera em visão TV)
    cena_root.translation = np.array([0.0, -8.0, -45.0], dtype=np.float32)
    cena_root.rotation = np.array([15.0, -25.0, 0.0], dtype=np.float32) 
    cena_root.callbacks = [animar_camera_estadio]
    runtime.scene.add_child(cena_root)
    
    # -------------------------------------------------------------------------
    # ILUMINAÇÃO DO ESTÁDIO
    # -------------------------------------------------------------------------
    # Luz Direcional global (Luar/Sol)
    luz_global = Light(LightType.DIRECTIONAL)
    luz_global.rotation = np.array([45.0, 30.0, 0.0], np.float64)
    luz_global.light_intensity = 1.0
    runtime.scene.add_child(luz_global)
   
    # Refletor Pontual Esquerdo (Luz tom frio)
    refletor_esq = Light(LightType.POINT)
    refletor_esq.translation = np.array([-12.0, 10.0, 5.0], np.float64)
    refletor_esq.light_color = np.array([0.9, 0.9, 1.0], np.float32)
    refletor_esq.light_intensity = 80.0
    cena_root.add_child(refletor_esq)
    
    # Refletor Pontual Direito (Luz tom quente)
    refletor_dir = Light(LightType.POINT)
    refletor_dir.translation = np.array([12.0, 10.0, 5.0], np.float64)
    refletor_dir.light_color = np.array([1.0, 0.9, 0.9], np.float32)
    refletor_dir.light_intensity = 80.0
    cena_root.add_child(refletor_dir)

    # -------------------------------------------------------------------------
    # LOOP DE RENDERIZAÇÃO E CONVERSÃO PARA VÍDEO
    # -------------------------------------------------------------------------
    # Executa o loop por 500 frames capturando a 60 FPS (~8.3 segundos)
    runtime.loop(n=500, capture=np.arange(0, 500, 1, dtype=np.int32))
    urenderer.utils.image_to_video(NOME_DA_CENA, fps=60)
    urenderer.utils.clear_workdir(NOME_DA_CENA, image_only=True)