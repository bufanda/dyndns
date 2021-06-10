FROM python:3.8-alpine

#image label
ARG BUILD_DATE
ARG VCS_REF

LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-url="https://github.com/bufanda/dyndns" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.schema-version="1.0.0-rc1"

ENV DYN_INCONTAINER="TRUE"

ADD app /app
ADD requirements.txt /

WORKDIR  /
RUN pip install -r requirements.txt

CMD [ "python3", "/app/dyn.py" ]
EXPOSE 18080
