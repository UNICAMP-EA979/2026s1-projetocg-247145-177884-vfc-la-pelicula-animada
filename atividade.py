from collections import deque
import math
import numpy as np
import urenderer
from OpenGL import GL

# Importações do seu projeto
from urenderer.node import Node, Light, LightType
from urenderer.renderer.opengl import Material, Texture
from urenderer.geometry.mesh.cube import get_mesh_cube
from urenderer.geometry.mesh.glb import load_glb  

NOME_DA_CENA = "tatico_vitoria_433"

def animar_camera_estadio(node: Node, deltaTime: float, time_since_start: float) -> None:
    """Faz a cena inteira rotacionar lentamente, criando um efeito de sobrevoo/panorâmica."""
    # O valor 2.0 controla a velocidade do movimento (quanto menor, mais lento e suave)
    # A rotação no eixo Y (índice 1) faz a câmera "rodar" ao redor do campo
    node.rotation[1] = -25.0 + (time_since_start * 3.0) 
    
    # Opcional: leve balanço sutil na altura (eixo Y) ou inclinação para dar dinamismo de câmera real
    node.rotation[0] = 15.0 + math.sin(time_since_start * 1.5) * 3.0

def animar_jogadores(node: Node, deltaTime: float, time_since_start: float) -> None:
    """Anima os jogadores com alternância entre Jogada 1 (Direita) e Jogada 2 (Esquerda)."""
    idx = node.render_data.get("idx", -1)
    base_pos = node.render_data.get("base_pos", np.array([0.0, 0.0, 0.0], dtype=np.float32))

    # --- CONTROLE DO CICLO DAS JOGADAS ---
    tempo_jogada = 4.0  # Cada jogada completa (ida e volta) dura 4 segundos
    tempo_total_ciclo = tempo_jogada * 2.0  # 8 segundos para o ciclo completo (Jogada 1 + Jogada 2)
    
    t = time_since_start % tempo_total_ciclo
    
    # Determina qual jogada está ativa e calcula o fator suave (0.0 -> 1.0 -> 0.0)
    if t < tempo_jogada:
        jogada_ativa = 1
        # Curva suave Cossoidal: inicia em 0, atinge 1.0 no meio da jogada e volta a 0 no fim
        fator = (1.0 - math.cos((t / tempo_jogada) * 2.0 * math.pi)) / 2.0
    else:
        jogada_ativa = 2
        t_fase2 = t - tempo_jogada
        fator = (1.0 - math.cos((t_fase2 / tempo_jogada) * 2.0 * math.pi)) / 2.0

    offset_tatico = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    if jogada_ativa == 1:
        if idx == 4:  # Lateral Direito: Dispara até a linha de fundo
            offset_tatico = np.array([-0.5, 0.0, -22.0], dtype=np.float32)

        elif idx == 1:  # Lateral Esquerdo: Fecha por dentro formando a ponta esquerda da linha de 3
            offset_tatico = np.array([2.5, 0.0, 0.5], dtype=np.float32)  # Desliza para X: -5.0

        elif idx == 2:  # Zagueiro Esquerdo: Bascula para a direita ocupando o centro da linha de 3
            offset_tatico = np.array([2.0, 0.0, 0.0], dtype=np.float32)  # Desliza para X: -1.5

        elif idx == 3:  # Zagueiro Direito: Cobre diretamente a vaga do Lateral Direito
            offset_tatico = np.array([2.0, 0.0, -1.0], dtype=np.float32) # Desliza para X: 5.0

        elif idx == 1:  # Lateral Esquerdo: Fecha por dentro e compõe linha de 3 zagueiros
            offset_tatico = np.array([2.0, 0.0, 1.0], dtype=np.float32)

        elif idx == 6:  # Meia Esquerdo: Abre a amplitude na esquerda
            offset_tatico = np.array([-2.5, 0.0, -1.0], dtype=np.float32)

        elif idx == 7:  # Meia Direito: Abre a amplitude na direita
            offset_tatico = np.array([2.5, 0.0, -1.0], dtype=np.float32)

        elif idx == 8:  # Ponta Esquerdo: Corta da ponta para o meio (abrir corredor pro lateral)
            offset_tatico = np.array([4.5, 0.0, -6.0], dtype=np.float32)

        elif idx == 9:  # Ponta Direito: Corta da ponta para o meio (abrir corredor pro lateral)
            offset_tatico = np.array([-4.5, 0.0, -2.0], dtype=np.float32)

        elif idx == 10: # Centroavante: Infiltra fundo na grande área
            offset_tatico = np.array([2.0, 0.0, -5.0], dtype=np.float32)

    elif jogada_ativa == 2:
        if idx == 1:    # Lateral Esquerdo: Dispara até a linha de fundo na esquerda
            offset_tatico = np.array([0.5, 0.0, -22.0], dtype=np.float32)
        elif idx == 4:  # Lateral Direito: Fecha a ponta direita da linha de 3
            offset_tatico = np.array([-2.5, 0.0, 0.5], dtype=np.float32)
        elif idx == 3:  # Zagueiro Direito: Bascula para o centro da zaga
            offset_tatico = np.array([-1.5, 0.0, 0.0], dtype=np.float32)
        elif idx == 2:  # Zagueiro Esquerdo: Cobre a vaga do LE
            offset_tatico = np.array([-2.0, 0.0, -1.0], dtype=np.float32)
        elif idx == 8:  # Ponta Esquerdo: Corta para dentro em direção à área
            offset_tatico = np.array([4.5, 0.0, -2.0], dtype=np.float32)
        elif idx == 5:  # Volante: Infiltra na entrada da grande área
            offset_tatico = np.array([0.0, 0.0, -4.0], dtype=np.float32)
        elif idx == 10: # Centroavante: Puxa a marcação para o primeiro pau
            offset_tatico = np.array([-2.0, 0.0, -5.0], dtype=np.float32)

    # 1. Posição Tática com deslocamento suave
    pos_tatica = base_pos + (offset_tatico * fator)
    node.translation[0] = pos_tatica[0]
    node.translation[2] = pos_tatica[2]

    # 2. Passada/Flutuação procedural no eixo Y
    node.translation[1] = pos_tatica[1] + math.sin(4 * time_since_start) * 0.15

    # 3. Gingado da corrida (eixos X e Z)
    node.rotation[0] = math.sin(6 * time_since_start) * 12.0
    node.rotation[2] = math.cos(6 * time_since_start) * 2.0

if __name__ == "__main__":
    urenderer.utils.clear_workdir(NOME_DA_CENA)
    
    # -------------------------------------------------------------------------
    # 1. SETUP DO RENDERIZADOR OPENGL
    # -------------------------------------------------------------------------
    width, height = 1920, 1080
    renderer = urenderer.renderer.OpenGLRenderer(width, height)
    
    # Fundo de "noite de jogo"
    renderer.background_color = np.array([0.05, 0.05, 0.05, 1.0], np.float32)
    # Luz ambiente para não deixar sombras totalmente pretas
    renderer.ambient_color = np.array([0.25, 0.25, 0.25], dtype=np.float32)
    
    runtime = urenderer.application.Runtime(renderer, name=NOME_DA_CENA)
    runtime.camera.vertical_fov = 60.0
    runtime.camera.far_plane = 100.0
    
    # -------------------------------------------------------------------------
    # 2. SHADERS E TEXTURAS
    # -------------------------------------------------------------------------
    shader = urenderer.renderer.Shader("assets/vertex.vs", "assets/05-fragment.fs")
    
    blackTextureR = Texture(np.zeros((1, 1), np.uint8), GL.GL_RED, GL.GL_R8)
    whiteTextureR = Texture(255 * np.ones((1, 1), np.uint8), GL.GL_RED, GL.GL_R8)
    
    # Texturas do Campo (Lembre-se de colocar as imagens na pasta assets)
    textura_gramado = Texture.load_file("assets/grass/Grass001_1K-PNG_Color.png", srgb=True, drop_alpha=True)
    textura_gramado_rough = Texture.load_file("assets/grass/Grass001_1K-PNG_Roughness.png", drop_alpha=True)
    textura_gramado_normal = Texture.load_file("assets/grass/Grass001_1K-PNG_NormalGL.png", drop_alpha=True)
    
    # Escudo do Vitória (drop_alpha=False para manter a transparência se for PNG)
    logo_vitoria = Texture.load_file("assets/vitoria_bandeira.jpg", srgb=True, drop_alpha=False)
    
    textura_uniforme = Texture.load_file("assets/camisa_vitoria.png", srgb=True, drop_alpha=True)

    # -------------------------------------------------------------------------
    # 3. MATERIAIS DO CENÁRIO
    # -------------------------------------------------------------------------
    textura_atlas = Texture.load_file("assets/textura_base.png", srgb=True, drop_alpha=True)

    material_arquibancada = Material(shader)
    material_arquibancada.set_texture(0, "baseColorTexture", textura_uniforme)
    material_arquibancada.set_texture(1, "metallicTexture", blackTextureR)    
    material_arquibancada.set_texture(2, "roughnessTexture", whiteTextureR)  
    material_arquibancada.set_uniform("tiling", 1.0)

    roughness_media = Texture(np.full((1, 1), 100, dtype=np.uint8), GL.GL_RED, GL.GL_R8)
    material_jogador = Material(shader)
    material_jogador.set_texture(0, "baseColorTexture", textura_atlas)
    material_jogador.set_texture(1, "metallicTexture", blackTextureR)   # Roupa/pele 
    material_jogador.set_texture(2, "roughnessTexture", roughness_media)  # Material fosco
    material_jogador.set_uniform("tiling", 1.0) 

    material_campo = Material(shader)
    material_campo.set_texture(0, "baseColorTexture", textura_gramado)
    material_campo.set_texture(1, "metallicTexture", blackTextureR)
    material_campo.set_texture(2, "roughnessTexture", textura_gramado_rough)
    material_campo.set_texture(3, "normalTexture", textura_gramado_normal) 
    material_campo.set_uniform("tiling", 12.0)
    
    material_logo = Material(shader)
    material_logo.set_texture(0, "baseColorTexture", logo_vitoria)
    material_logo.set_texture(1, "metallicTexture", blackTextureR)
    material_logo.set_texture(2, "roughnessTexture", whiteTextureR)
    material_logo.set_uniform("tiling", 1.0)
    
    # -------------------------------------------------------------------------
    # 4. GRAFO DE CENA
    # -------------------------------------------------------------------------
    cena_root = Node(name="Cena_Principal")

   #O Gramado (Cubo achatado)
    no_campo = Node(name="Gramado")
    no_campo.render_data["mesh"] = get_mesh_cube()
    no_campo.render_data["material"] = material_campo
    no_campo.scale = np.array([30.0, 0.05, 35.0], dtype=np.float32)
    no_campo.translation = np.array([-4.5, -8.0, -3.0], dtype=np.float32)
    no_campo.rotation = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    cena_root.add_child(no_campo)

# --- ARQUIBANCADA 1 ---
    no_arquibancada = load_glb("assets/estrutura_arquibancada_02.glb")
    no_arquibancada.name = "Arquibancada1"
    no_arquibancada.scale = np.array([0.01, 0.01, 0.01], dtype=np.float32)
    no_arquibancada.translation = np.array([11.0, -8.0, 16.0], dtype=np.float32)
    no_arquibancada.rotation = np.array([-90.0, 0.0, 0.0], dtype=np.float32)
    
    # Aplica o material em todas as submalhas filhas da Arquibancada 1
    fila_arq1 = deque([no_arquibancada])
    while len(fila_arq1) > 0:
        atual = fila_arq1.popleft()
        if "mesh" in atual.render_data:
            atual.render_data["material"] = material_arquibancada # ou outro material de sua preferência
        for child in atual.children:
            fila_arq1.append(child)
    cena_root.add_child(no_arquibancada)

    # --- ARQUIBANCADA 2  ---
    no_arquibancada2 = load_glb("assets/estrutura_arquibancada_02.glb")
    no_arquibancada2.name = "Arquibancada2"
    no_arquibancada2.scale = np.array([0.01, 0.01, 0.01], dtype=np.float32)
    no_arquibancada2.translation = np.array([-20.0, -8.0, -35.0], dtype=np.float32) # Alinhada no Y com a outra (-10.0)
    no_arquibancada2.rotation = np.array([-90.0, 0.0, 180.0], dtype=np.float32) # Mesma rotação para ficar orientada igual
    
    # Aplica o material em todas as submalhas filhas da Arquibancada 2
    fila_arq2 = deque([no_arquibancada2])
    while len(fila_arq2) > 0:
        atual = fila_arq2.popleft()
        if "mesh" in atual.render_data:
            atual.render_data["material"] = material_arquibancada
        for child in atual.children:
            fila_arq2.append(child)
    cena_root.add_child(no_arquibancada2)

    # no_arquibancada_frontal = load_glb("assets/estrutura_arquibancada_02.glb")
    # no_arquibancada_frontal.name = "ArquibancadaFrontal"
    # no_arquibancada_frontal.scale = np.array([0.005, 0.01, 0.005], dtype=np.float32)
    
    # # Posicionada no fundo do campo (ajuste o X e o Z se precisar centralizar perfeitamente)
    # no_arquibancada_frontal.translation = np.array([0.0, -10.0, 15.0], dtype=np.float32)
    
    # # Rotação ajustada para virar a bancada para dentro do campo no fundo
    # no_arquibancada_frontal.rotation = np.array([-90.0, 0.0, 90.0], dtype=np.float32)
    
    # # Aplica o material em todas as submalhas filhas da Arquibancada Frontal
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
    # no_campo.scale = np.array([1.0, 1.0, 1.0], dtype=np.float32)  # Ajuste a escala se necessário
    # no_campo.translation = np.array([0.0, -0.025, 0.0], dtype=np.float32)
    # cena_root.add_child(no_campo)

    from collections import deque
    fila_campo = deque([no_arquibancada])
    while len(fila_campo) > 0:
        atual = fila_campo.popleft()
        # Se o objeto tiver uma malha mas não tiver material atribuído, 
        # aplicamos o material padrão ou garantimos que ele seja renderizado
        if "mesh" in atual.render_data and "material" not in atual.render_data:
            atual.render_data["material"] = material_campo  # reaproveita o material do gramado
        for filho in atual.children:
            fila_campo.append(filho)

    # O Placar / Escudo do Vitória ao fundo
    no_logo = Node(name="Placar")
    no_logo.render_data["mesh"] = get_mesh_cube()
    no_logo.render_data["material"] = material_logo
    no_logo.scale = np.array([36.0, 22.0, 0.2], dtype=np.float32) # Proporção 16:9 de um placar real
    no_logo.translation = np.array([-5.0, 2.0, -35.0], dtype=np.float32)
    no_logo.rotation = np.array([0.0, 0.0, 0.0], dtype=np.float32) # Virado para a câmera
    cena_root.add_child(no_logo)
    
    # As posições táticas (4-3-3)
    posicoes_433 = [
        (-5.0, -7.5, 10.0),     # Goleiro 
        (-12.5, -7.5, 5.0),    # Lateral Esq
        (-8.0, -7.5, 6.0),    # Zag Esq
        (-2.0, -7.5, 6.0),     # Zag Dir
        (2.5, -7.5, 5.0),     # Lateral Dir
        (-5.0, -7.5, 3.0),      # Volante
        (-10.0, -7.5, -1.5),    # Meia Esq
        (0.0, -7.5, -1.5),     # Meia Dir
        (-12.0, -7.5, -5.0),    # Ponta Esq
        (2.0, -7.5, -5.0),     # Ponta Dir
        (-5.0, -7.5, -10.0)     # Centroavante 
    ]
    
    time_node = Node(name="Time_Vitoria")
    cena_root.add_child(time_node)
    
    for idx, pos in enumerate(posicoes_433):
        jogador_root = load_glb("assets/low_poly_soccer_player.glb")
        jogador_root.name = f"Jogador_{idx}"
        
        jogador_root.translation = np.array(pos, dtype=np.float32)
        
        # REGISTRA O ÍNDICE E A POSIÇÃO BASE PARA O CALLBACK
        jogador_root.render_data["idx"] = idx
        jogador_root.render_data["base_pos"] = np.array(pos, dtype=np.float32)
        
        jogador_root.scale = np.array([0.015, 0.015, 0.015], dtype=np.float32)
        jogador_root.rotation = np.array([0.0, 0.0, 0.0], dtype=np.float32) 
        
        jogador_root.callbacks = [animar_jogadores]
        
        # BFS para atribuir o material do atleta
        fila_de_nos = deque([jogador_root])
        while len(fila_de_nos) > 0:
            no_atual = fila_de_nos.popleft()
            if "mesh" in no_atual.render_data:
                no_atual.render_data["material"] = material_jogador 
            for child in no_atual.children:
                fila_de_nos.append(child)
                
        time_node.add_child(jogador_root)
        
    # Posicionando a câmera da cena inteira (Visão Isométrica/TV)
    cena_root.translation = np.array([0.0, -8.0, -45.0], dtype=np.float32)
    cena_root.rotation = np.array([15.0, -25.0, 0.0], dtype=np.float32) 
    cena_root.callbacks = [animar_camera_estadio]
    runtime.scene.add_child(cena_root)
    
    # -------------------------------------------------------------------------
    # 5. LUZES DO ESTÁDIO
    # -------------------------------------------------------------------------
    luz_global = Light(LightType.DIRECTIONAL)
    luz_global.rotation = np.array([45.0, 30.0, 0.0], np.float64)
    luz_global.light_intensity = 1.0
    runtime.scene.add_child(luz_global)
   
    refletor_esq = Light(LightType.POINT)
    refletor_esq.translation = np.array([-12.0, 10.0, 5.0], np.float64)
    refletor_esq.light_color = np.array([0.9, 0.9, 1.0], np.float32)
    refletor_esq.light_intensity = 80.0
    cena_root.add_child(refletor_esq)
    
    refletor_dir = Light(LightType.POINT)
    refletor_dir.translation = np.array([12.0, 10.0, 5.0], np.float64)
    refletor_dir.light_color = np.array([1.0, 0.9, 0.9], np.float32)
    refletor_dir.light_intensity = 80.0
    cena_root.add_child(refletor_dir)

    # -------------------------------------------------------------------------
    # 6. RENDERIZAÇÃO
    # -------------------------------------------------------------------------
    runtime.loop(n=500, capture=np.arange(0, 500, 1, dtype=np.int32))
    urenderer.utils.image_to_video(NOME_DA_CENA, fps=60)
    urenderer.utils.clear_workdir(NOME_DA_CENA, image_only=True)