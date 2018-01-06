FROM python:2.7

ARG DMS_VERSION=release/1.2
ARG GUNICORN_VERSION=19.7.1

WORKDIR /usr/src/app
EXPOSE 8000
ENV PYTHONBUFFERED=1
ENV PYTHONPATH="/usr/local/adlibre_dms"
ENV PATH="/usr/local/adlibre_dms:${PATH}"

# App config
ENV DJANGO_SETTINGS_MODULE=settings_prod
ENV PROJECT_PATH=/usr/src/app

# and tools to make our life easier
RUN export DEBIAN_FRONTEND=noninteractive && apt-get -y update && \
  apt-get -y install --no-install-recommends vim && \
  apt-get -y install libgs9 libtiff5 libpoppler46 a2ps && \
  apt-get -y autoremove && apt-get -y clean && rm -rf /var/lib/apt/lists/*

# Consistent uid for underprivileged web user
RUN groupadd www --gid 1000 && \
  useradd www --uid 1000 --gid 1000 -d /usr/src/app && mkdir -p /usr/src/app

# Copy skel layout
COPY . /usr/src/app/

# Set permissions so we can work out the box
RUN mkdir -p $PROJECT_PATH/www/static && \
    chown -R www:www $PROJECT_PATH/www/static $PROJECT_PATH/log $PROJECT_PATH/documents $PROJECT_PATH/db

# Install with pip
RUN pip install --no-cache-dir git+https://github.com/adlibre/Adlibre-DMS.git@${DMS_VERSION} && \
    pip install --no-cache-dir gunicorn==${GUNICORN_VERSION}

USER www
RUN manage.py collectstatic --noinput
ENTRYPOINT ["/usr/src/app/deployment/entry.sh"]
CMD ["web"]
