FROM pytorch/torchserve:latest-gpu

USER root

RUN chmod -R +rwx /home/model-server
RUN chown -R 1000970123:1000970123 /home/model-server

RUN mkdir /.cache
RUN chown -R 1000970123:1000970123 /.cache

USER model-server
ENTRYPOINT ["/usr/local/bin/dockerd-entrypoint.sh"]
