FROM panubo/python-bureaucrat

COPY . /srv/git

RUN source /srv/ve27/bin/activate && \
    cd /srv/git && \
    pip install --upgrade pip && \
    pip install git+git://github.com/adlibre/Adlibre-DMS.git
