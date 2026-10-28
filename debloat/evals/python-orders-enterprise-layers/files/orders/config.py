class Settings:
    """Application settings."""

    ENABLE_NOTIFICATIONS = True
    CURRENCY = "USD"
    MAX_ITEMS = 50
    ID_PREFIX = "ord-"
    ID_WIDTH = 4


def get_settings():
    return Settings()
