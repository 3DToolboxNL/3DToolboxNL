#FROM ghcr.io/osgeo/gdal:ubuntu-small-latest
FROM ghcr.io/osgeo/gdal:ubuntu-full-3.8.5

RUN apt-get update && apt-get install -y git \
					 liblaszip8 \
                                         python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip

# next line equivalent to: pip install pygments prompt-toolkit setproctitle xonsh
RUN pip3 install 'xonsh[full]'
RUN pip3 install laspy[laszip]
RUN pip3 install xontrib-argcomplete xontrib-sh

RUN git clone https://gitlab.com/Oslandia/py3dtiles.git
RUN python -m pip install -e /py3dtiles

# allow numba to do its thing even with unprivileged user
ENV NUMBA_CACHE_DIR=/tmp

COPY interactive.xsh /etc/xonshrc
COPY interactive.xsh /root/.xonshrc

COPY freshem2pc.xsh /usr/bin/freshem2pc
COPY lut.csv /home/lut.csv
COPY sample.vrt /home/sample.vrt

RUN mkdir /.local /.cache /.config
RUN chmod -R 777 /.local /.cache /.config /tmp

CMD ["/usr/bin/freshem2pc.xsh"]
