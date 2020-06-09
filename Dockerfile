FROM alpine

ENV PYTHONUNBUFFERED=1

RUN echo "**** install Python ****" && \
    apk add --no-cache python3 git && \
    if [ ! -e /usr/bin/python ]; then ln -sf python3 /usr/bin/python ; fi && \
    \
    echo "**** install pip ****" && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --no-cache --upgrade pip setuptools wheel && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi

RUN git clone https://github.com/stuartgraham/MetOffice2Influx.git
WORKDIR /MetOffice2Influx
RUN pip install -r requirements.txt
RUN rm .gitignore Dockerfile requirements.txt
RUN apk del git 
CMD ["python3", "./main.py"]