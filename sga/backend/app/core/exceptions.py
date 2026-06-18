class DomainError(Exception):
    """Error de regla de negocio."""

    def __init__(self, message: str, code: str = "domain_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(DomainError):
    def __init__(self, message: str = "Recurso no encontrado.") -> None:
        super().__init__(message, code="not_found")


class ConflictError(DomainError):
    def __init__(self, message: str = "Conflicto de estado.") -> None:
        super().__init__(message, code="conflict")


class UnauthorizedError(DomainError):
    def __init__(self, message: str = "No autorizado.") -> None:
        super().__init__(message, code="unauthorized")


class ForbiddenError(DomainError):
    def __init__(self, message: str = "Acceso denegado.") -> None:
        super().__init__(message, code="forbidden")


class ValidationError(DomainError):
    def __init__(self, message: str = "Datos invalidos.") -> None:
        super().__init__(message, code="validation")
