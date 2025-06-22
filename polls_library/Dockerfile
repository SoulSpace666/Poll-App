#https://github.com/astral-sh/uv-docker-example/blob/main/multistage.Dockerfile

FROM ghcr.io/astral-sh/uv:python3.13-alpine AS builder
WORKDIR /app

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

RUN rm -f pyproject.toml uv.lock .python-version

FROM python:3.13-alpine AS main-stage

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 

WORKDIR /app
# Copy the application from the builder
COPY --from=builder /app /app

# # Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

RUN chmod +x ./docker-entrypoint.sh

# CMD ["sleep", "1000"]
ENTRYPOINT ["./docker-entrypoint.sh"]