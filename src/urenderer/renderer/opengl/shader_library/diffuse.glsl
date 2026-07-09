#ifndef LIBRARY_DIFUSE

#define PI 3.14159265359

//Calcula a refletância difusa da superfície utilizando o modelo de Lambert
vec3 diffuseReflectance(vec3 fresnel, vec3 baseColor, float metallic)
{
    // Metais não possuem componente difusa (toda a luz é refletida especularmente
    // ou absorvida); apenas dielétricos espalham luz internamente
    vec3 diffuseColor = baseColor * (1.0 - metallic);

    // Conservação de energia: a fração de luz que não foi refletida
    // especularmente (fresnel) é a que sobra para difusão
    vec3 kd = vec3(1.0) - fresnel;

    // Modelo de Lambert normalizado pela área do hemisfério (PI)
    return kd * diffuseColor / PI;

}

#define LIBRARY_DIFUSE
#endif
