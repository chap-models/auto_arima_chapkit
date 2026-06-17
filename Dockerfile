# auto_arima_chapkit Dockerfile
# chapkit-r-tidyverse ships R 4.5 + the tidyverse + forecasting stack
# (dplyr, fable, tsibble, lubridate, ...) preinstalled, plus uv +
# Python 3.13 in the base image's /app/.venv. Multi-arch (linux/amd64,
# linux/arm64); the platform ARG defaults to amd64 for parity with the
# existing compose.yml but can be overridden for a native arm64 build.
ARG BASE_PLATFORM=linux/amd64
FROM --platform=${BASE_PLATFORM} ghcr.io/dhis2-chap/chapkit-r-tidyverse:latest

# chapkit-py runs as root; matches chapkit-r / chapkit-r-tidyverse.
USER root

WORKDIR /work
# Copy lockfile + manifest first so the dep-install layer caches independently of code changes.
COPY pyproject.toml uv.lock ./

# Sync user deps into the base image's existing venv at /app/.venv. --frozen pins to
# uv.lock for reproducible builds, --no-dev skips dev-only deps (uvicorn etc. ship with
# the base), --no-install-project because this project isn't a package, just a service.
RUN --mount=type=cache,target=/root/.cache/uv \
    UV_PROJECT_ENVIRONMENT=/app/.venv uv sync --frozen --no-dev --no-install-project

COPY main.py ./
COPY scripts/ ./scripts/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
