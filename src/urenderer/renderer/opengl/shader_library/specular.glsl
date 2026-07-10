#ifndef LIBRARY_SPECULAR

#define PI 3.14159265359

// Calcula a refletância especular da superfície utilizando o modelo de Blinn-Phong.
vec3 specularReflectance(vec3 fresnel, vec3 normal, vec3 halfAngle, vec3 viewDirection, vec3 LightDirection, float roughness)
{
    float shininess = 2.0 / (roughness * roughness + 0.0001) - 2.0;
    shininess = max(shininess, 1.0);

    float NdotH = max(dot(normal, halfAngle), 0.0);
    float specIntensity = pow(NdotH, shininess);

    return vec3(specIntensity);
}

#define LIBRARY_SPECULAR
#endif
