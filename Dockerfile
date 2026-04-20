FROM python:3.14-alpine@sha256:dd4d2bd5b53d9b25a51da13addf2be586beebd5387e289e798e4083d94ca837a AS build

COPY Pipfile .
COPY Pipfile.lock .

# generate the requirements file
RUN python3 -m pip install pipenv && \
    pipenv requirements > requirements.txt

FROM python:3.14-alpine@sha256:dd4d2bd5b53d9b25a51da13addf2be586beebd5387e289e798e4083d94ca837a AS base
ENV PYTHONUNBUFFERED=true

ARG SCRIPT_ROOT=/usr/local/bin/bonkbot

RUN adduser -u 1100 -D bonkbot
RUN mkdir -pv ${SCRIPT_ROOT}
RUN chown -R 1100:1100 ${SCRIPT_ROOT}

WORKDIR ${SCRIPT_ROOT}

COPY --from=build requirements.txt .
RUN python3 -m pip install -r requirements.txt
COPY --chown=1100:1100 bonkbot bonkbot
USER bonkbot

CMD [ "/usr/bin/env", "python3", "-m", "bonkbot.main" ]