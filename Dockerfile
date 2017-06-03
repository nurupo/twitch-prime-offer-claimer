FROM debian:stretch-slim

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
      ca-certificates \
      chromium \
      libgconf-2-4 \
      python3 \
      python3-requests \
      python3-selenium \
      unzip \
      wget && \
    rm -rf /var/lib/apt/lists/* && \
    wget https://chromedriver.storage.googleapis.com/2.29/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    rm *.zip && \
    mv chromedriver /usr/local/bin

WORKDIR /script

ENV PYTHONIOENCODING=utf8

CMD python3 twitch-prime-offer-claimer.py
