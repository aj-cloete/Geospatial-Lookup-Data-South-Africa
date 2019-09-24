FROM python:3.7-slim-stretch as base

ENV PATH=/root/.local/bin:$PATH TERM=linux PYTHONUTF8=1 PYTHONIOENCODING=utf-8
ARG DEBIAN_FRONTEND=noninteractive


RUN set -x \
  && apt-get update \
  && apt-get install -yqq --no-install-recommends apt-utils \
    libspatialindex-dev \
    wget \
    zip 

RUN pip install --user -U --no-warn-script-location \
  fiona \
  geopandas \
  geopy \
  matplotlib \
  numpy \
  pandas==0.24.2 \
  pyarrow \
  pyproj \
  rtree \
  shapely \
  six

RUN rm -rf \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/man \
        /usr/share/doc \
        /usr/share/doc-base 

COPY ./* /geo/
WORKDIR /geo

CMD /bin/bash
