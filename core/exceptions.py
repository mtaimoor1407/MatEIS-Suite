"""Custom exceptions so the UI can show friendly messages instead of tracebacks."""


class MatEISError(Exception):
    """Base class for every error raised on purpose by MatEIS."""


class ValidationError(MatEISError):
    """User or data input is outside the allowed range or has the wrong type."""


class DuplicateMaterialError(MatEISError):
    """A material with the same name already exists in the database."""


class MaterialNotFoundError(MatEISError):
    """The requested material is not in the database."""


class DatabaseError(MatEISError):
    """The SQLite file could not be read or written."""
