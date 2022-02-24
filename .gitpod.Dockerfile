FROM gitpod/workspace-full

RUN curl -s https://smartpy.io/cli/install.sh | bash /dev/stdin --yes
RUN pip install smartpy