from collections import deque

import numpy as np
import urenderer
from OpenGL import GL
from urenderer.geometry.mesh.cube import get_mesh_cube
from urenderer.node import Node
from urenderer.renderer.opengl import Material, Texture
from urenderer.geometry.mesh.sphere import get_mesh_sphere
from copy import copy

# Podemos dar um nome a cena
NOME_DA_CENA = "vitoria_fc"

if __name__ == "__main__":
    urenderer.utils.clear_workdir(NOME_DA_CENA)
    renderer = urenderer.renderer.OpenGLRenderer(1920, 1080)
    renderer.background_color = np.array([0, 0, 0, 1], np.float32)
    runtime = urenderer.application.Runtime(
        renderer, name=NOME_DA_CENA)

    # Configuramos a luz ambiente da cena
    renderer.ambient_color = np.array([0.1, 0.1, 0.1], dtype=np.float32)

    # Carregamos o shader e texturas
    shader = urenderer.renderer.Shader(
        "assets/vertex.vs", "assets/05-fragment.fs")

    whiteTextureR = Texture(255*np.ones((1, 1), np.uint8), GL.GL_RED, GL.GL_R8)
    blackTextureR = Texture(np.zeros((1, 1), np.uint8), GL.GL_RED, GL.GL_R8)

    whiteTexture = Texture(255*np.ones((1, 1, 3), np.uint8),
                           GL.GL_RGB, GL.GL_RGB)
    blackTexture = Texture(np.zeros((1, 1, 3), np.uint8),
                           GL.GL_RGB, GL.GL_RGB)
    light_red = np.ones((1, 1, 3), np.uint8)
    light_red[0, 0, 0] = 255
    light_red[0, 0, 1] = 25
    light_red[0, 0, 2] = 50
    redTexture = Texture(light_red, GL.GL_RGB, GL.GL_RGB)

      # IMPORTANTE: Corrigido o carregamento da bandeira para evitar que fique preta/invisível (srgb=True)
    vitoriaBandeira = Texture.load_file("assets/vitoria_bandeira.jpg", srgb=True, drop_alpha=True)
    brickBasecolor = Texture.load_file("assets/brick/Bricks097_1K-JPG_Color.jpg", srgb=True, drop_alpha=True)
    brickRoughness = Texture.load_file("assets/brick/Bricks097_1K-JPG_Roughness.jpg", drop_alpha=True)
    brickMetallic = Texture(np.zeros((1, 1), np.uint8), GL.GL_RED, GL.GL_R8)
    brickNormal = Texture.load_file("assets/brick/Bricks097_1K-JPG_NormalGL.jpg", drop_alpha=True)

    grassBasecolor = Texture.load_file("assets/grass/Grass003_1K-JPG_Color.jpg", srgb=True, drop_alpha=True)
    grassRoughness = Texture.load_file("assets/grass/Grass003_1K-JPG_Roughness.jpg", drop_alpha=True)
    grassMetallic = Texture(np.zeros((1, 1), np.uint8), GL.GL_RED, GL.GL_R8)
    grassNormal = Texture.load_file("assets/grass/Grass003_1K-JPG_NormalGL.jpg", drop_alpha=True)

    alejandroTexturas = []
    for i in range(11):
        if i != 1:
            alejandroTexturas.append(Texture.load_file(f'assets/alejandro/textures/gltf_embedded_{i}.jpeg', srgb=True,drop_alpha=True))
        else:
            alejandroTexturas.append(Texture(255*np.ones((1, 1, 3), np.uint8),GL.GL_RGB, GL.GL_RGB)) 

    materialBasic = Material(shader)
    materialBasic.set_texture(0, "baseColorTexture", whiteTexture)
    materialBasic.set_texture(1, "metallicTexture", blackTextureR)
    materialBasic.set_texture(2, "roughnessTexture", whiteTextureR)

    materialMuro = Material(shader)
    materialMuro.set_texture(0, "baseColorTexture", vitoriaBandeira)
    materialMuro.set_texture(1, "metallicTexture", brickMetallic)
    materialMuro.set_texture(2, "roughnessTexture", brickRoughness)

        # NOVO MATERIAL: Criado exclusivamente para o chão
    materialGramado = Material(shader)
    materialGramado.set_texture(0, "baseColorTexture", grassBasecolor)
    materialGramado.set_texture(1, "metallicTexture", grassMetallic)
    materialGramado.set_texture(2, "roughnessTexture", grassRoughness)
    materialGramado.set_texture(3, "normalTexture", grassNormal)

    materialAlejandro = Material(shader)
    alejandroRoughness1 = Texture.load_file('assets/alejandro/textures/gltf_embedded_1@channels=G.jpeg', srgb=False, drop_alpha=True)
    alejandroMetallic1  = Texture.load_file('assets/alejandro/textures/gltf_embedded_1@channels=B.jpeg', srgb=False, drop_alpha=True)
    materiais_alejandro = {}
    for j in range(11):
        if j == 1:
            continue
 
        tex_cor = Texture.load_file(f'assets/alejandro/textures/gltf_embedded_{j}.jpeg', srgb=True, drop_alpha=True)
        
        # Instancia um material PBR exclusivo para essa parte do corpo
        mat = Material(shader)
        mat.set_texture(0, "baseColorTexture", tex_cor)
        mat.set_texture(1, "metallicTexture", alejandroMetallic1)     # Usa o mapa de metal correto
        mat.set_texture(2, "roughnessTexture", alejandroRoughness1)   # Usa o mapa de rugosidade correto
        mat.set_uniform("tiling", 1.0)
        
        materiais_alejandro[j] = mat

    mapeamento_texturas = {
                "headnode": 9,          # Pele do rosto/cabeça
                "armsnode": 9,          # Braços (geralmente compartilham a textura de pele 0)
                "handsnode": 3,         # Mãos (geralmente compartilham a textura de pele 0)
                "torsonode": 3,         # Torso / Camisa / Uniforme
                "legsnode": 3,          # Pernas / Calções / Meiões
                "hairnode": 4,          # Cabelo
                "facialhairnode": 4,    # Barba / Bigode
                "accessorynode": 6,     # Chuteiras, munhequeiras ou óculos
                "eyesnode": 5,          # Olhos (Íris e esclera)
            }
    # ================= CONSTRUÇÃO DA CENA (CONTAINER) =================
    
    materialGramado.set_uniform("tiling", 40.0)
    materialBasic.set_uniform("tiling", 1.0)
    materialMuro.set_uniform("tiling", 1.0)

    materialBola = Material(shader)
    materialBola.set_texture(0, "baseColorTexture", redTexture)
    materialBola.set_uniform("tiling", 1.0)
    
    chao = Node()
    chao.name = "Chao"
    chao.render_data["mesh"] = get_mesh_cube()
    # Atribuímos o novo material de relva
    chao.render_data["material"] = materialGramado 
    chao.scale = np.array([80.0, 1.0, 80.0], dtype=np.float32)
    chao.translation = np.array([0.0, -2.0, -15.0], dtype=np.float32) 
    runtime.scene.add_child(chao)

    muro = Node()
    muro.name = "Muro"
    muro.render_data["mesh"] = get_mesh_cube()
    muro.render_data["material"] = materialMuro 
    muro.scale = np.array([60.0, 15.0, 0.5], dtype=np.float32)
    muro.translation = np.array([0.0, 4.0, -5.1], dtype=np.float32) 
    runtime.scene.add_child(muro)

    alejandro_base = urenderer.geometry.mesh.load_glb("assets/alejandro/Alejandro.glb")

    malha_de_jogadores = alejandro_base.render_data.get("mesh")

    material_jogador = copy(materialBasic)

    # 5 jogadores distribuídos simetricamente no eixo X. 
    posicoes_x = np.linspace(-6.0, 6.0, 5)
    posicoes_x2 = np.linspace(-3.0, 3.0, 5)
    def instanciar_jogador(posicao, nome):
        jogador = urenderer.geometry.mesh.load_glb("assets/alejandro/Alejandro.glb")
        jogador.name = nome
        
        # Como o .glb é uma árvore com várias partes (corpo, roupa),
        # aplicamos o material a todos os nós filhos.
        nos = [jogador]
        while len(nos) > 0:
            n = nos.pop(0)
            nos.extend(n.children)

            nome = n.name.lower()
            if nome in mapeamento_texturas:
                id_textura = mapeamento_texturas[nome]
                n.render_data["material"] = materiais_alejandro[id_textura]
            else:
                n.render_data["material"] = materiais_alejandro[0]

        # Rotação e Translação
        jogador.rotation = np.array([10, 0, 0], np.float32)
        jogador.translation = posicao
        runtime.scene.add_child(jogador)

    # 1. Linha de Trás (
    for i in range(5):
        pos = np.array([posicoes_x[i], -0.5, -1.5], dtype=np.float32)
        instanciar_jogador(pos, f"Jogador_Tras_{i}")

    # 2. Linha do Meio 
    for i in range(5):
        pos = np.array([posicoes_x2[i], -1.0, -0.5], dtype=np.float32)
        instanciar_jogador(pos, f"Jogador_Meio_{i}")

    # 3. Jogador Destaque / Capitão 
    pos_capitao = np.array([0.0, -1.5, 1.0], dtype=np.float32)
    instanciar_jogador(pos_capitao, "Jogador_Destaque")

    # --- A BOLA ---
    bola = Node()
    bola.name = "Bola"
    bola.render_data["mesh"] = get_mesh_sphere()
    bola.render_data["material"] = materialBola

    bola.scale = np.array([0.2, 0.2, 0.2], dtype=np.float32)  # Reduzimos a escala da primitiva para parecer uma bola de futebol
    # Reduzimos a escala da primitiva para parecer uma bola de futebol
    bola.translation = np.array([0.0, -1.2, 1.5], dtype=np.float32)
    

    #bola.translation = np.array([0.0, -5.0, -2.0], dtype=np.float32)
    
    runtime.scene.add_child(bola)

    runtime.camera.vertical_fov = 100.0
    runtime.camera.translation = np.array([0.0, 1.0, 4.0], dtype=np.float32)

    # Adicionamos luzes a cena

    light = urenderer.node.Light(urenderer.node.LightType.DIRECTIONAL)
    light.rotation = np.array([45, 45, 45], np.float64)
    light.light_intensity = 3.0
    runtime.scene.add_child(light)

    light2 = urenderer.node.Light(urenderer.node.LightType.POINT)
    light2.translation = np.array([-1, -1, -2], np.float64)
    light2.light_color = np.array([1.0, 1.0, 1.0], np.float32)
    light2.light_intensity = 5.0
    runtime.scene.add_child(light2)

    light3 = urenderer.node.Light(urenderer.node.LightType.POINT)
    light3.translation = np.array([1, -1, -2], np.float64)
    light3.light_color = np.array([1.0, 1.0, 1.0], np.float32)
    light3.light_intensity = 5.0

    # Renderizamos a cena

    video = True
    if video:
        # Renderização salvando video
        # Podemos ajustar os parâmetros para alterar o tamanho ou frequência de sampling
        runtime.loop(n=4000, capture=np.arange(0, 4000, 40, dtype=np.int32))
        urenderer.utils.image_to_video(NOME_DA_CENA, fps=30)
        urenderer.utils.clear_workdir(NOME_DA_CENA, image_only=True)
    else:
        # Renderização salvando frames
        runtime.loop(capture=[1])

 
