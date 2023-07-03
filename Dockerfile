FROM python:3.9.10-alpine3.15

RUN apk add --update --no-cache docker && \
    pip install --upgrade pip && \
    pip install docker

COPY ./src/technitium-companion.py /technitium-companion.py
COPY ./run.sh /run.sh
COPY ./build_finished.sh /build_finished.sh

RUN chmod +x /run.sh && chmod +x build_finished.sh

ENTRYPOINT ["/run.sh"]
