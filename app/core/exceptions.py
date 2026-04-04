class AppError(Exception):
    """Loi nghiep vu tong quat."""


class NotFoundError(AppError):
    """Khong tim thay du lieu."""


class BadRequestError(AppError):
    """Input khong hop le."""


class ExternalFetchError(AppError):
    """Nguon ben ngoai loi hoac khong parse duoc."""
