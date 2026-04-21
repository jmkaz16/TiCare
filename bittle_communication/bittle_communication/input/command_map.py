# Diccionario simplificado basado en tu Excel.
# Cada comando tiene solo los sinónimos esenciales.
# El resto lo resuelve spaCy + fuzzy matching.

COMMAND_MAP = {

    # buttUp
    "levanta el culo": "buttUp",
    "alza el trasero": "buttUp",
    "eleva la cadera": "buttUp",

    # calib
    "calibra": "calib",
    "calibra los motores": "calib",
    "ajusta tu postura": "calib",

    # dropped
    "déjate caer": "dropped",
    "túmbate hacia atrás": "dropped",

    # lifted
    "estira el cuello": "lifted",
    "sube la cabeza": "lifted",

    # rest
    "descansa": "rest",
    "relájate": "rest",

    # sit
    "siéntate": "sit",
    "toma asiento": "sit",

    # str
    "estírate": "str",
    "haz estiramientos": "str",

    # up
    "levántate": "up",
    "ponte de pie": "up",

    # bk
    "retrocede": "bk",
    "camina hacia atrás": "bk",

    # bkL
    "retrocede a la izquierda": "bkL",

    # bkR
    "retrocede a la derecha": "bkR",

    # jpF
    "salta hacia adelante": "jpF",
    "brinca hacia adelante": "jpF",

    # phF
    "empuja": "phF",
    "haz fuerza": "phF",

    # phL
    "empuja a la izquierda": "phL",

    # phR
    "empuja a la derecha": "phR",

    # trF
    "trota": "trF",
    "corre un poco": "trF",

    # trL
    "trota a la izquierda": "trL",

    # trR
    "trota a la derecha": "trR",

    # wkF
    "camina": "wkF",
    "avanza": "wkF",

    # wkL
    "camina a la izquierda": "wkL",
    "gira a la izquierda": "wkL",

    # wkR
    "camina a la derecha": "wkR",
    "gira a la derecha": "wkR",

    # angry
    "enfádate": "angry",
    "gruñe": "angry",

    # bx
    "boxea": "bx",
    "pelea": "bx",

    # chr
    "brinda": "chr",
    "celebra": "chr",

    # dg
    "cava": "dg",
    "escarba": "dg",

    # fiv
    "choca esos cinco": "fiv",
    "dame la pata": "fiv",
    "dame cinco": "fiv",

    # hds
    "haz el pino": "hds",
    "ponte del revés": "hds",

    # hg
    "abrázame": "hg",
    "dame un abrazo": "hg",
    "reza": "hg",

    # hi
    "saluda": "hi",
    "di hola": "hi",

    # hu
    "levanta las manos": "hu",
    "ríndete": "hu",

    # jmp
    "salta": "jmp",
    "brinca": "jmp",

    # kc
    "da una patada": "kc",
    "patea": "kc",

    # mw
    "haz el paso lunar": "mw",
    "moonwalk": "mw",

    # pd
    "hazte el muerto": "pd",
    "simula morir": "pd",

    # pee
    "haz pis": "pee",
    "orina": "pee",

    # pu
    "haz flexiones": "pu",
    "entrena": "pu",

    # scrh
    "ráscate": "scrh",
    "quítate las pulgas": "scrh",

    # snf
    "olfatea": "snf",
    "busca": "snf",

    # tbl
    "haz de mesa": "tbl",
    "ponte plano": "tbl",

    # wh
    "mueve la cabeza": "wh",
    "di que no": "wh",

    # zz
    "vuelve a cero": "zz",
    "apágate": "zz",
}