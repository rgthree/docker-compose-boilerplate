#!/usr/bin/env python3

import os, shutil, sys
from colors import colors

def main(argv):
  shutil.rmtree('.git')
  os.remove('.gitignore')
  os.rename('base.env.template', 'base.env')
  os.rename('base.docker-compose.yaml.template', 'base.docker-compose.yaml')
  os.rename('proxy/x.env.template', 'proxy/x.env')
  os.rename('proxy/x.docker-compose.yaml.template', 'proxy/x.docker-compose.yaml')
  os.rename('proxy/volumes/traefik/dynamic_conf.toml.template', 'proxy/volumes/traefik/dynamic_conf.toml')
  os.rename('proxy/volumes/traefik/traefik.toml.template', 'proxy/volumes/traefik/traefik.toml')

  print('%s%s [SUCCESS] %s You can now delete init.py as well: rm init.py' % (colors.fg.green, colors.bold, colors.reset))

if __name__ == "__main__":
   main(sys.argv[1:])