#version 330 core

#include "light.glsl"
#include "fresnel.glsl"
#include "diffuse.glsl"
#include "specular.glsl"

#define MAX_LIGHT 10
#define PI 3.14159265359

// Suporte a texturas com tiling

in vec3 worldPosition;
in vec3 worldNormal;
in vec2 uv;

uniform vec3 ambientColor;
uniform sampler2D baseColorTexture;
uniform sampler2D metallicTexture;
uniform sampler2D roughnessTexture;
uniform float tiling;

uniform Light lights[MAX_LIGHT];
uniform vec3 cameraPos;

out vec4 FragColor;

void main()
{
    vec3 normal = normalize(worldNormal);

    // Direção de visualização (do fragmento para a câmera)
    vec3 viewDir = normalize(cameraPos - worldPosition);

    vec2 uvTiled = uv * tiling;

    // Amostragem das texturas
    vec3 baseColor   = texture(baseColorTexture, uvTiled).rgb;
    float metallic   = texture(metallicTexture,   uvTiled).r;
    float roughness  = texture(roughnessTexture,  uvTiled).r;

    // Acumulador de cor (luz direta)
    vec3 color = vec3(0.0);

    // Luz ambiente (global)
    vec3 ambient = ambientColor * baseColor;

    // Loop sobre todas as luzes ativas
    for (int i = 0; i < MAX_LIGHT; i++)
    {
        Light light = lights[i];
        if (light.type == LIGHT_UNSET)
            break;

        // Dados da luz
        float attenuation = computeLightAttenuation(light, worldPosition);
        vec3 lightColor   = light.color * light.intensity;
        vec3 lightDir     = computeLightDirection(light, worldPosition);

        // Half‑angle (vetor médio entre luz e visão)
        vec3 halfAngle = normalize(lightDir + viewDir);

        // Fresnel (Schlick)
        vec3 F = fresnelReflectance(baseColor, metallic, halfAngle, lightDir);

        // Difusa (Lambert)
        vec3 diffuse = diffuseReflectance(F, baseColor, metallic);

        // Especular (Blinn‑Phong)
        vec3 specular = specularReflectance(F, normal, halfAngle,
                                            viewDir, lightDir, roughness);

        // Refletância final = difusa + especular ponderada por Fresnel
        vec3 reflectance = diffuse + F * specular;

        // Fator N·L (Lambert)
        float NdotL = max(dot(normal, lightDir), 0.0);

        // Contribuição desta luz
        vec3 contribution = reflectance * lightColor * NdotL * attenuation;
        color += contribution;
    }

    FragColor = vec4(ambient + color, 1.0);
}
