def validar_dominio_tenant(dominio: str) -> None:
    if not dominio.replace("-", "").isalnum() or dominio != dominio.lower():
        raise ValueError("El dominio solo permite minusculas, numeros y guiones.")
