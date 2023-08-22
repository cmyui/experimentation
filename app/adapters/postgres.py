import urllib.parse


def create_dsn(
    dialect: str,
    user: str,
    host: str,
    port: int,
    database: str,
    password: str | None = None,
    driver: str | None = None,
) -> str:
    if driver is not None:
        scheme = f"{dialect}+{driver}"
    else:
        scheme = dialect

    if password is not None:
        netloc = f"{user}:{password}@{host}:{port}"
    else:
        netloc = f"{user}@{host}:{port}"

    return urllib.parse.urlunparse((scheme, netloc, database, "", "", ""))
