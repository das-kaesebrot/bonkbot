FROM python:3.14-alpine@sha256:5a824eb82cc75361f98611f3cfc5091ea33f10a6ccea4d4ebdabbc523b9a1614 AS build

COPY Pipfile .
COPY Pipfile.lock .

# generate the requirements file
RUN python3 -m pip install pipenv && \
    pipenv requirements > requirements.txt

FROM python:3.14-alpine@sha256:5a824eb82cc75361f98611f3cfc5091ea33f10a6ccea4d4ebdabbc523b9a1614 AS base
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