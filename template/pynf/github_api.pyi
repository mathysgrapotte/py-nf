"""GitHub API boundary for nf-core module metadata and files."""

def fetch_directory_entries(api_url: str, github_token: str | None) -> list[dict]:
    """Fetch GitHub API directory entries.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    requests
    """
    ...

def fetch_raw_text(raw_url: str) -> str:
    """Fetch a raw file's text content.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    requests
    """
    ...

def fetch_rate_limit(github_token: str | None) -> dict:
    """Fetch GitHub rate limit status.

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    requests
    """
    ...
