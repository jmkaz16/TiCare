# Diccionario simplificado basado en tu Excel.
# Cada comando tiene solo los sinónimos esenciales.
# El resto lo resuelve spaCy + fuzzy matching.

# Acciones
COMMAND_MAP = {
    "buscar": "buscar",
    "busca": "buscar",
    "encuentra": "buscar",
    "localiza": "buscar",
    # añade aquí más verbos si quieres
}

# Lugares
PLACES_MAP = {
    "cocina": "la cocina",
    "salon": "el salón",
    "salón": "el salón",
    "habitacion": "la habitación",
    "habitación": "la habitación",
    "baño": "el baño",
    # etc.
}

# Objetos (para fuzzy de objetos)
OBJECTS_MAP = {
    "botella": "botella",
    "llaves": "llaves",
    "cartera": "cartera",
    "mando": "mando",
    "gafas": "gafas",
    # añade los que quieras
}

# Respuestas afirmativas / negativas para confirmación
YES_MAP = {
    "sí": "yes",
    "si": "yes",
    "claro": "yes",
    "vale": "yes",
    "correcto": "yes",
    "afirmativo": "yes",
}

NO_MAP = {
    "no": "no",
    "negativo": "no",
    "para": "no",
    "me he equivocado": "no",
    "cancela": "no",
}

# Palabras de parada (stop) por voz
STOP_MAP = {
    "para": "stop",
    "detente": "stop",
    "stop": "stop",
    "quieto": "stop",
    "basta": "stop",
    "cancela": "stop",
}
