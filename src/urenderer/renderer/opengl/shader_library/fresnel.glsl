#ifndef LIBRARY_FRESNEL

/// Calcula a refletância de Fresnel
vec3 fresnelReflectance(vec3 baseColor, float metallic, vec3 halfAngle, vec3 lightDirection)
{
    // Refletância em incidência normal (F0): dielétricos usam ~0.04,
    // metais usam a própria cor base
    vec3 F0 = mix(vec3(0.04), baseColor, metallic);

    // Cosseno do ângulo entre o vetor half e a direção da luz
    float cosTheta = clamp(dot(halfAngle, lightDirection), 0.0, 1.0);

    // Aproximação de Schlick
    return F0 + (vec3(1.0) - F0) * pow(1.0 - cosTheta, 5.0);
}

#define LIBRARY_FRESNEL
#endif
