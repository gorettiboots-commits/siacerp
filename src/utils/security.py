import hmac

import bcrypt


def hash_contrasena(plano: str) -> str:
    return bcrypt.hashpw(plano.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_contrasena(plano: str, hash_almacenado: str) -> bool:
    try:
        return bcrypt.checkpw(plano.encode("utf-8"), hash_almacenado.encode("utf-8"))
    except ValueError:
        return False


def es_hash_bcrypt(valor: str) -> bool:
    return valor.startswith(("$2a$", "$2b$", "$2y$"))


def coincide_plano(plano: str, almacenado: str) -> bool:
    return hmac.compare_digest(plano.encode("utf-8"), almacenado.encode("utf-8"))
