# Diccionario simplificado basado en tu Excel.
# Cada comando tiene solo los sinónimos esenciales.
# El resto lo resuelve spaCy + fuzzy matching.

COMMAND_MAP = {

    # Search
    "encuentra": "src",
    "busca": "src",

    # Stop
    "para": "stp",
    "detente": "stp",
    "quieto": "stp",

}

PLACES_MAP = {
    "baño": "pl1",
    "aseo": "pl1",
    "servicio": "pl1",

    "cocina": "pl2",
    "cocinita": "pl2",

    "salón": "pl3",
    "sala": "pl3",
    "living": "pl3",

    "dormitorio": "pl4",
    "cuarto": "pl4",
    "habitación": "pl4",

    "jardín": "pl5",
    "patio": "pl5",
    "terraza": "pl5",
}