FROM python:3.8-alpine

#image label
ARG BUILD_DATE
ARG VCS_REF

LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-url="https://github.com/bufanda/dyndns" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.schema-version="1.0.0-rc1"

ENV DYN_INCONTAINER="TRUE"

COPY app /app
COPY requirements.txt /

WORKDIR  /
RUN pip install --no-cache-dir -r requirements.txt && \
    ln -sf /dev/stdout /var/log/dyndns.log

CMD [ "python3", "/app/dyn.py" ]
EXPOSE 18080
