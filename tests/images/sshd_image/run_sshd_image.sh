#!/usr/bin/env sh
cd tests/images/sshd_image || exit
docker build --tag alpine-sshd-iqa .
docker rm -f sshd-iqa
docker run -itd --name sshd-iqa alpine-sshd-iqa 2> /dev/null || docker start sshd-iqa
chmod 600 identity
chmod 600 identity.pub