"""GitHub API boundary for nf-core module metadata and files."""

def fetch_directory_entries(api_url: str, github_token: str | None) -> list[dict]:
    """Fetch GitHub API directory entries for a repository path.

    Example:
        >>> fetch_directory_entries("https://api.github.com/...", None)
        [{'name': 'fastqc', 'type': 'dir'}]

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    requests
    """
    ...

def fetch_raw_text(raw_url: str) -> str:
    """Fetch a raw file's text content from GitHub.

    Example:
        >>> fetch_raw_text("https://raw.githubusercontent.com/.../meta.yml")
        'contents of meta.yml'

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    requests
    """
    ...

def fetch_rate_limit(github_token: str | None) -> dict:
    """Fetch GitHub rate limit status.

    Example:
        >>> fetch_rate_limit(None)
        {'limit': 60, 'remaining': 59, 'reset_time': 1700000000}

    DEPENDS_ON:
    None

    EXTERNAL_DEPENDS_ON:
    requests
    """
    ...
