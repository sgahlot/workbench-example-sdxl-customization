FROM pytorch/torchserve-kfs-nightly:latest-gpu

USER root

COPY TorchserveModel.py ./kserve_wrapper/TorchserveModel.py

RUN mkdir /.cache && \
    chgrp -R 0 /home/model-server /.cache && \
    chmod -R g=u /home/model-server /.cache

USER model-server
