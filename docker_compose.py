#!/usr/bin/env python3

import os, sys
from colors import colors
from generate import generate_docker_compose

def docker_compose_run(argv):
    generate_docker_compose(argv)

    subdir = argv[0]
    if subdir.endswith('/'):
      subdir = subdir[:-1]
    SUBDIR_REL = './%s' % subdir

    OUTPUT_DOCKER_COMPOSE_FILE = 'generated.docker-compose.yaml'

    print('%s -> Changing directory to %s' % (colors.reset, SUBDIR_REL))
    os.chdir(SUBDIR_REL)
    print('%s -> Running: docker-compose --file %s %s' % (colors.reset, OUTPUT_DOCKER_COMPOSE_FILE, ' '.join(argv[1:])))
    os.system('docker-compose --file %s %s' % (OUTPUT_DOCKER_COMPOSE_FILE, ' '.join(argv[1:])))
    sys.exit(0)

if __name__ == "__main__":
   docker_compose_run(sys.argv[1:])