FROM python:3.8-slim

WORKDIR /sonarqube_exporter/
RUN mkdir /sonarqube_exporter/logs && chmod 777 /sonarqube_exporter/logs

COPY . .
RUN /usr/local/bin/python3 -m pip install --upgrade pip
RUN pip3 install -r requirements.txt

EXPOSE 8198
ENTRYPOINT [ "/bin/sh",  "entrypoint.sh" ]
