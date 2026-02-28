FROM python:3.14-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

#######################

FROM python:3.14-slim

COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

ARG USERNAME=non-root
ARG USER_UID=1000
ARG USER_GID=$USER_UID

WORKDIR /app

COPY wrestling_referees.py .
COPY update_history.py .
COPY graph.py .
COPY app.sh .

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt update \
    && DEBIAN_FRONTEND=noninteractive \
        apt install --no-install-recommends --assume-yes \
        imagemagick \
    && apt clean \
    && mkdir /app/referees \
    && chown -R $USERNAME:$USERNAME /app

USER $USERNAME

CMD ["/bin/bash", "/app/app.sh"]

