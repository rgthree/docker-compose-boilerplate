#!/usr/bin/env python3

import os, sys
from docker-compose import docker_compose_run

def main(argv):
    docker_compose_run([argv[0]] + ['up'] + argv[1:])
    sys.exit(0)

if __name__ == "__main__":
   main(sys.argv[1:])