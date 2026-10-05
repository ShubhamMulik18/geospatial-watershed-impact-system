class AppError(Exception):
    """Base exception for application-level errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code or self.__class__.__name__
        super().__init__(message)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=404)