from collections import deque

import numpy as np
import urenderer
from OpenGL import GL
from urenderer.geometry.mesh.cube import get_mesh_cube
from urenderer.node import Node
from urenderer.renderer.opengl import Material, Texture
from urenderer.geometry.mesh.sphere import get_mesh_sphere
from copy import copy

def update_rotation(node: Node, deltaTime: float, time_since_start: float) -> None:

    time_since_start /= 10
    t = time_since_start - int(time_since_start)

    node.rotation[0] = 0
    node.rotation[1] = 360*t
    node.rotation[2] = 0


def update_scale(node: Node, deltaTime: float, time_since_start: float) -> None:
    scale = np.sin(5*time_since_start)/10
    scale += 0.8

    node.scale = scale * np.ones(3)


def update_cube(node: Node, deltaTime: float, time_since_start: float) -> None:

    # Posição = dv/dt -> posição_t = posição_{t-1}+DeltaT*v
    center: np.array = node.center
    position = node.translation

    r = position-center

    r_2d = np.array([r[0], r[2]])
    v_dir = np.array([-r_2d[1], r_2d[0]])

    v = v_dir*node.angular_velocity
    v = np.array([v[0], 0.0, v[1]])

    node.translation += deltaTime*v

    # Rotação = f(tempo)
    time_since_start /= 10
    t = time_since_start - int(time_since_start)
    node.rotation[0] = 0
    node.rotation[1] = -360*node.angular_velocity*t
    node.rotation[2] = 0


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

    starrySkyTexture = Texture.load_file("assets/Blue-universe-956981.jpg",
                                         srgb=True, drop_alpha=True)

    rockBasecolor = Texture.load_file("assets/Rock035_1K-JPG/Rock035_1K-JPG_Color.jpg",
                                      srgb=True, drop_alpha=True)
    rockRoughness = Texture.load_file("assets/Rock035_1K-JPG/Rock035_1K-JPG_Roughness.jpg",
                                      drop_alpha=True)

      # IMPORTANTE: Corrigido o carregamento da bandeira para evitar que fique preta/invisível (srgb=True)
    vitoriaBandeira = Texture.load_file("assets/vitoria_bandeira.jpg", srgb=True, drop_alpha=True)
    vitoriaBandeiraM = Texture(np.zeros((1, 1), np.uint8), GL.GL_RED, GL.GL_R8)
    vitoriaBandeiraR = Texture(255*np.ones((1, 1), np.uint8), GL.GL_RED, GL.GL_R8)

    grassBasecolor = Texture.load_file("assets/Grass003_1K-JPG_Color.jpg", srgb=True, drop_alpha=True)
    grassRoughness = Texture.load_file("assets/Grass003_1K-JPG_Roughness.jpg", drop_alpha=True)
    grassMetallic = Texture(np.zeros((1, 1), np.uint8), GL.GL_RED, GL.GL_R8)
    grassNormal = Texture.load_file("assets/Grass003_1K-JPG_NormalGL.jpg", drop_alpha=True)

    materialBasic = Material(shader)
    materialBasic.set_texture(0, "baseColorTexture", whiteTexture)
    materialBasic.set_texture(1, "metallicTexture", blackTextureR)
    materialBasic.set_texture(2, "roughnessTexture", whiteTextureR)

    materialBackground = Material(shader)
    materialBackground.set_texture(0, "baseColorTexture", vitoriaBandeira)

    materialCube = Material(shader)
    materialCube.set_texture(0, "baseColorTexture", vitoriaBandeira)
    materialCube.set_texture(1, "metallicTexture", blackTextureR)
    materialCube.set_texture(2, "roughnessTexture", whiteTextureR)
        # NOVO MATERIAL: Criado exclusivamente para o chão
    materialGramado = Material(shader)
    materialGramado.set_texture(0, "baseColorTexture", grassBasecolor)
    materialGramado.set_texture(1, "metallicTexture", grassMetallic)
    materialGramado.set_texture(2, "roughnessTexture", grassRoughness)
    materialGramado.set_texture(3, "normalTexture", grassNormal)
    
    chao = Node()
    chao.name = "Chao"
    chao.render_data["mesh"] = get_mesh_cube()
    # Atribuímos o novo material de relva
    chao.render_data["material"] = materialGramado 
    chao.scale = np.array([80.0, 1.0, 80.0], dtype=np.float32)
    chao.translation = np.array([0.0, -2.0, -15.0], dtype=np.float32) # Base em Y = -1.0
    runtime.scene.add_child(chao)

    muro = Node()
    muro.name = "Muro"
    muro.render_data["mesh"] = get_mesh_cube()
    muro.render_data["material"] = materialCube 
    muro.scale = np.array([60.0, 15.0, 0.5], dtype=np.float32)
    muro.translation = np.array([0.0, 4.0, -5.1], dtype=np.float32) # Afastado em Z = -15.0
    runtime.scene.add_child(muro)

    alejandro = urenderer.geometry.mesh.load_glb("assets/source/Alejandro.glb")
    alejandro.render_data["material"] = materialBasic
    alejandro.translation = np.array([5, 5, -7])
    alejandro.rotation = np.array([30, 0, 0], np.float32)
    runtime.scene.add_child(alejandro)

    alejandro_base = urenderer.geometry.mesh.load_glb("assets/source/Alejandro.glb")

    malha_de_jogadores = alejandro_base.render_data.get("mesh")

    material_jogador = copy(materialBasic)

    # 5 jogadores distribuídos simetricamente no eixo X. 
    posicoes_x = np.linspace(-6.0, 6.0, 5)
    posicoes_x2 = np.linspace(-3.0, 3.0, 5)
    def instanciar_jogador(posicao, nome):
        jogador = urenderer.geometry.mesh.load_glb("assets/source/Alejandro.glb")
        jogador.name = nome
        
        # Como o .glb é uma árvore com várias partes (corpo, roupa),
        # aplicamos o material a todos os nós filhos.
        nos = [jogador]
        while len(nos) > 0:
            n = nos.pop(0)
            nos.extend(n.children)
            n.render_data["material"] = materialBasic

        # Rotação e Translação
        jogador.rotation = np.array([10, 0, 0], np.float32)
        jogador.translation = posicao
        runtime.scene.add_child(jogador)

    # 1. Linha de Trás (Z = -5.0)
    for i in range(5):
        pos = np.array([posicoes_x[i], -0.5, -2.0], dtype=np.float32)
        instanciar_jogador(pos, f"Jogador_Tras_{i}")

    # 2. Linha do Meio (Z = -2.0)
    for i in range(5):
        pos = np.array([posicoes_x2[i], -1.0, -1.0], dtype=np.float32)
        instanciar_jogador(pos, f"Jogador_Meio_{i}")

    # 3. Jogador Destaque / Capitão (Frente, Z = 2.0)
    pos_capitao = np.array([0.0, -1.5, 0.0], dtype=np.float32)
    instanciar_jogador(pos_capitao, "Jogador_Destaque")

    # --- A BOLA ---
    bola = Node()
    bola.name = "Bola"
    bola.render_data["mesh"] = get_mesh_sphere()
    # Podemos usar o material básico ou criar um branco novo
    bola.render_data["material"] = materialBasic 
    
    # Reduzimos a escala da primitiva para parecer uma bola de futebol
    bola.translation = np.array([0.0, -1.7, -2.0], dtype=np.float32)
    
    # Posição: 
    # X = 0.0 (ao centro)
    # Y = -0.85 (para não ficar enterrada no chão, já que a esfera tem raio e o chão está em -1.0)
    # Z = -5.5 (um pouco à frente do capitão, que está em -6.0)
    bola.translation = np.array([0.0, -5.0, -2.0], dtype=np.float32)
    
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
    light2.light_color = np.array([0.0, 0.0, 1.0], np.float32)
    light2.light_intensity = 5.0
    runtime.scene.add_child(light2)

    light3 = urenderer.node.Light(urenderer.node.LightType.POINT)
    light3.translation = np.array([1, -1, -2], np.float64)
    light3.light_color = np.array([1.0, 0.0, 1.0], np.float32)
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

 