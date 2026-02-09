FROM yurivictoria/mininetwifi-p4-base:ubuntu20.04

WORKDIR /app

COPY . .

RUN sudo apt install iputils-ping

RUN export PIP_BREAK_SYSTEM_PACKAGES=1 && \
    pip3 install --no-cache-dir -r requirements.txt

RUN python3 polka_halfsiphash/build_polka.py

CMD ["python3", "run.py"]