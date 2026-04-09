
# Módulo encargado de dividir una frase larga en "chunks" semánticos,
# es decir, en órdenes independientes que luego serán procesadas
# por el parser principal (tiago_spacy.parse_command).
#
# Estrategia:
# 1) División por conectores explícitos (y, luego, después, luego de, y después, etc.)
# 2) Si la división por conectores no produce múltiples chunks, se intenta
#    una división basada en la estructura sintáctica con spaCy:
#    - separar por verbos coordinados / múltiples verbos principales
# 3) Normalización y limpieza de cada chunk

# El objetivo es ser robusto frente a frases como:
# "Perro, camina hacia adelante y salta"  -> ["camina hacia adelante", "salta"]
# "Perro, gira a la izquierda luego saluda" -> ["gira a la izquierda", "saluda"]

from typing import List
import re
import spacy

# Cargar spaCy 
nlp = spacy.load("es_core_news_sm")

# Lista de conectores comunes que suelen separar órdenes
# Incluimos variantes con y sin comas y con espacios para facilitar el split.
CONNECTORS = [
    r"\s+y\s+",            # " y "
    r"\s+luego\s+",        # " luego "
    r"\s+después\s+",      # " después "
    r"\s+entonces\s+",     # " entonces "
    r"\s+a continuación\s+", # " a continuación "
    r"\s+seguidamente\s+", # " seguidamente "
    r"\s+y después de eso\s+",
    r"\s+luego de eso\s+",
    r"\s*,\s*"             # coma como separador 
]

# Expresiones para limpiar puntuación sobrante al inicio/final
TRIM_RE = re.compile(r"^[\s,\.¡!¿?]+|[\s,\.¡!¿?]+$")

def _split_by_connectors(text: str) -> List[str]:
    """
    Intenta dividir la frase usando los conectores definidos.
    Devuelve una lista de chunks limpios si encuentra más de uno,
    o la lista original (un solo elemento) si no hay división.
    """
    # Empezamos con el texto original en una lista
    chunks = [text]
    for conn in CONNECTORS:
        new_chunks = []
        for ch in chunks:
            # Usamos re.split para soportar expresiones regulares
            parts = re.split(conn, ch, flags=re.IGNORECASE)
            # Añadir partes resultantes
            for p in parts:
                p_clean = TRIM_RE.sub("", p)
                if p_clean:
                    new_chunks.append(p_clean)
        chunks = new_chunks

        # Si ya tenemos más de 1 chunk, podemos seguir intentando refinar,
        # pero si la división produjo múltiples elementos, la consideramos válida.
    return chunks

def _split_by_syntax(text: str) -> List[str]:
    """
    Estrategia de respaldo: usar spaCy para detectar múltiples verbos
    y crear chunks alrededor de cada verbo principal.
    Ejemplo: "camina y salta" -> detecta dos verbos y separa.
    Esta función intenta reconstruir frases mínimas que contengan
    cada verbo y sus complementos inmediatos.
    """
    doc = nlp(text)
    verb_indices = [token.i for token in doc if token.pos_ == "VERB"]

    # Si no hay verbos o solo uno, devolvemos el texto entero
    if len(verb_indices) <= 1:
        return [text.strip()]

    chunks = []
    # Para cada verbo, tomamos desde el comienzo del verbo anterior (o 0)
    # hasta el comienzo del siguiente verbo, intentando incluir complementos.
    for i, vi in enumerate(verb_indices):
        start = vi
        # retroceder para incluir partículas o pronombres que preceden al verbo
        # (ej: "por favor, levántate" -> incluir "por favor," no es crítico)
        # Buscamos el token más a la izquierda que pertenezca a la misma oración
        # o que sea parte del subtree del verbo.
        verb_token = doc[vi]
        # Tomamos el subtree del verbo para incluir objetos y complementos
        subtree_tokens = list(verb_token.subtree)
        if subtree_tokens:
            # start index del subtree
            start = subtree_tokens[0].i
            end = subtree_tokens[-1].i + 1
        else:
            # fallback: hasta el siguiente verbo o final
            if i + 1 < len(verb_indices):
                end = verb_indices[i + 1]
            else:
                end = len(doc)

        # Si hay solapamiento con el siguiente verbo, ajustamos end
        if i + 1 < len(verb_indices):
            next_vi = verb_indices[i + 1]
            # incluir hasta justo antes del siguiente verbo
            end = min(end, next_vi)

        chunk_span = doc[start:end]
        chunk_text = chunk_span.text.strip()
        chunk_text = TRIM_RE.sub("", chunk_text)
        if chunk_text:
            chunks.append(chunk_text)

    # Si por alguna razón no se generaron chunks, devolvemos el texto original
    if not chunks:
        return [text.strip()]

    # Filtrar duplicados y devolver
    unique_chunks = []
    for c in chunks:
        if c not in unique_chunks:
            unique_chunks.append(c)
    return unique_chunks

def semantic_chunk(text: str) -> List[str]:
    """
    Función pública: recibe una frase y devuelve una lista de órdenes (chunks).
    Pasos:
    1) Normaliza espacios y puntuación básica.
    2) Intenta dividir por conectores explícitos.
    3) Si la división no produjo múltiples chunks, intenta división sintáctica.
    4) Devuelve la lista final de chunks limpios.
    """
    if not text or not text.strip():
        return []

    # Normalización básica: quitar espacios extremos y comillas innecesarias
    text_norm = text.strip()
    text_norm = TRIM_RE.sub("", text_norm)

    # 1) División por conectores
    chunks = _split_by_connectors(text_norm)

    # Si la división produjo más de 1 chunk, lo consideramos válido
    if len(chunks) > 1:
        return [c.strip() for c in chunks if c.strip()]

    # 2) División por sintaxis (spaCy)
    chunks_syntax = _split_by_syntax(text_norm)
    if len(chunks_syntax) > 1:
        return [c.strip() for c in chunks_syntax if c.strip()]

    # 3) No se pudo dividir: devolvemos la frase original como único chunk
    return [text_norm]

