# Build an egg of your project.

FROM python as build-stage

RUN pip install --no-cache-dir scrapyd-client

WORKDIR /workdir

COPY . .

RUN scrapyd-deploy --build-egg scrapyd_webnovel_jsonl.egg

# Build the image.

FROM python:alpine

# Install Scrapy dependencies - and any others for your project.

RUN apk --no-cache add --virtual build-dependencies \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    libxml2-dev \
    libxslt-dev \
    && pip install --no-cache-dir \
    scrapyd \
    beautifulsoup4 \
    selenium \
    && apk del build-dependencies \
    && apk add \
    openssl \
    libxml2 \
    libxslt \
    chromium chromium-chromedriver


# Mount two volumes for configuration and runtime.

VOLUME /etc/scrapyd/ /var/lib/scrapyd/

COPY ./scrapyd.conf /etc/scrapyd/

RUN mkdir -p /src/scrapyd_webnovel_jsonl

COPY --from=build-stage /workdir/scrapyd_webnovel_jsonl.egg /src/scrapyd_webnovel_jsonl/1.egg

EXPOSE 6800

ENTRYPOINT ["scrapyd", "--pidfile="]
