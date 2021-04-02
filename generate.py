#!/usr/bin/env python3

import os, sys, copy, shutil
import re
import ruamel.yaml # https://sourceforge.net/p/ruamel-yaml/code/ci/default/tree/comments.py
from colors import colors

yaml = ruamel.yaml.YAML()

# Emitter to clear out empty lines in lists.
class Emitter(ruamel.yaml.emitter.Emitter):
    def write_comment(self, comment, pre=False):
        if comment.value.replace('\n', ''):
            ruamel.yaml.emitter.Emitter.write_comment(self, comment, pre)

yaml.Emitter = Emitter


def generate_docker_compose(argv):
    subdir = argv[0]
    if subdir.endswith('/'):
      subdir = subdir[:-1]
    SUBDIR_REL = './%s' % subdir

    script_dir=os.path.dirname(os.path.abspath(__file__))
    print(script_dir)
    os.chdir(script_dir)

    if not os.path.isdir(SUBDIR_REL):
      print('Error: "%s" is not a directory.' % subdir)
      sys.exit()

    GENERATED_STRING = 'This file is generated from up.py. Do not edit it directly.'

    BASE_ENV = './base.env'
    BASE_DOCKER_COMPOSE = './base.docker-compose.yaml'

    X_ENV = '%s/x.env' % SUBDIR_REL
    X_DOCKER_COMPOSE = '%s/x.docker-compose.yaml' % SUBDIR_REL
    TPL_DOCKER_COMPOSE = '%s/tpl.docker-compose.yaml' % SUBDIR_REL

    OUTPUT_ENV = '%s/.env' % SUBDIR_REL
    OUTPUT_TEMP_DOCKER_COMPOSE = '%s/temp.docker-compose.yaml' % SUBDIR_REL
    OUTPUT_DOCKER_COMPOSE_FILE = 'generated.docker-compose.yaml'
    OUTPUT_DOCKER_COMPOSE = '%s/%s' % (SUBDIR_REL, OUTPUT_DOCKER_COMPOSE_FILE)

    X_BASE_MIXIN_PATTERN = re.compile(r'(\s*)x-base:\s*true.*')
    X_BASE_MIXIN_PATTERN = re.compile(r'(\s*)x-base-no-networks:\s*true.*')

    if os.path.isfile(X_ENV):
      print('%s -> Generating %s by combining %s and %s' % (colors.reset, OUTPUT_ENV, BASE_ENV, X_ENV))
      with open(OUTPUT_ENV,'wb') as wfd:
          wfd.write(("# %s\n" % GENERATED_STRING).encode())
          for f in [BASE_ENV, X_ENV]:
              with open(f,'rb') as fd:
                  shutil.copyfileobj(fd, wfd)
                  wfd.write("\n".encode())

    if os.path.isfile(X_DOCKER_COMPOSE):
      print('%s -> Generating temporary %s by combining %s and %s' % (colors.reset, OUTPUT_TEMP_DOCKER_COMPOSE, BASE_DOCKER_COMPOSE, X_DOCKER_COMPOSE))
      with open(OUTPUT_TEMP_DOCKER_COMPOSE,'wb') as wfd:
          for f in [BASE_DOCKER_COMPOSE, X_DOCKER_COMPOSE]:
              with open(f,'rb') as fd:
                  for line in fd:
                      line = line.replace('x-base: true'.encode(), '<<: *base'.encode())
                      line = line.replace('x-base-no-networks: true'.encode(), '<<: *base-no-networks'.encode())
                      wfd.write(line)
                  wfd.write("\n".encode())

    if os.path.isfile(OUTPUT_TEMP_DOCKER_COMPOSE):
      print('%s -> Using temporary %s' % (colors.reset, OUTPUT_TEMP_DOCKER_COMPOSE))
      with open(OUTPUT_TEMP_DOCKER_COMPOSE) as file:
          data = yaml.load(file)
      os.remove(OUTPUT_TEMP_DOCKER_COMPOSE)
    else:
      print('%s -> Using templated %s' % (colors.reset, TPL_DOCKER_COMPOSE))
      with open(TPL_DOCKER_COMPOSE) as file:
          data = yaml.load(file)

    for service_name in data['services']:
        service = data['services'][service_name]
        print('%s -> Evaluating service: %s%s' % (colors.reset, colors.fg.orange, service_name))

        # If there's no container_name set, then set the service name to it, otherwise docker-compose
        # will append a "_1" and sometimes a prefix.
        if not 'container_name' in service:
            print('%s   -> Setting container_name to %s' % (colors.reset, service_name))
            service.insert(0, 'container_name', service_name, comment='Generated.')

        # If we have an "x-volumes" then let's take it, and extend it on our current
        # list from a potential base.
        if 'x-volumes' in service:
            print('%s   -> Combining x-volumes' % (colors.reset))
            volumes_list = copy.deepcopy(service.get('volumes', ruamel.yaml.comments.CommentedSeq()))
            volumes_list.extend(service['x-volumes'])
            service.update({
              'volumes': volumes_list,
            })
            service.pop('x-volumes')

        # If we have an "x-environment" then let's take it, and extend it on our current environment
        # list from a potential base.
        if 'x-environment' in service:
            print('%s   -> Combining x-environment' % (colors.reset))
            environment_list = copy.deepcopy(service.get('environment', ruamel.yaml.comments.CommentedSeq()))
            environment_list.extend(service['x-environment'])
            service.update({
              'environment': environment_list,
            })
            service.pop('x-environment')

        # If we have an x-traefik then lets set up all the labels.
        if 'x-traefik' in service:
            print('%s   -> Setting traefik labels and network' % (colors.reset))
            x_traefik = service['x-traefik']

            rule = x_traefik['rule'] if 'rule' in x_traefik else ''
            if not rule:
              domain = x_traefik['domain'] if 'domain' in x_traefik else '${LAB_DOMAIN}'
              subdomain = x_traefik['subdomain'] if 'subdomain' in x_traefik else ''
              host = '%s.%s' % (subdomain, domain) if subdomain else domain
              rule = 'Host(`%s`)' % (host)

            has_forward_auth = x_traefik['traefik-forward-auth']
            middlewares=['headers@file']
            if has_forward_auth:
              middlewares.append('traefik-forward-auth')
            if 'additional-middlewares' in x_traefik:
              middlewares.extend(x_traefik['additional-middlewares'])

            labels_list = copy.deepcopy(service.get('labels', ruamel.yaml.comments.CommentedSeq()))
            labels_list.insert(0, 'traefik.enable=true')
            labels_list.extend([
              # Http - Redirects to http in the traefik config as "ssl-redirect"
              # 'traefik.http.routers.%s-http.rule=Host(`%s.${LAB_DOMAIN}`)' % (service_name, subdomain),
              # 'traefik.http.routers.%s-http.entrypoints=http' % service_name,
              # 'traefik.http.routers.%s-http.middlewares=ssl-redirect@file' % service_name,
              # Https
              'traefik.http.routers.%s.rule=%s' % (service_name, rule),
              'traefik.http.routers.%s.entrypoints=https' % service_name,
              'traefik.http.routers.%s.tls=true' % service_name,
              # 'traefik.http.routers.%s.middlewares=headers@file%s' % (service_name, ',traefik-forward-auth' if has_forward_auth else ''),
              'traefik.http.routers.%s.middlewares=%s' % (service_name, ','.join(middlewares)),
            ])
            if 'loadbalancer-port' in x_traefik:
              labels_list.extend([
                'traefik.http.routers.%s.service=%s_service' % (service_name, service_name),
                'traefik.http.services.%s_service.loadbalancer.server.port=%s' % (service_name, x_traefik['loadbalancer-port']),
              ])

            networks_list = copy.deepcopy(service.get('networks', ruamel.yaml.comments.CommentedSeq()))
            networks_list.append('traefik_proxy')

            service.update({
              'networks': networks_list,
              'labels': labels_list,
            })
            service.pop('x-traefik')


    print('%s -> Outputting %s' % (colors.reset, OUTPUT_DOCKER_COMPOSE))
    with open(OUTPUT_DOCKER_COMPOSE, 'w') as fp:
        fp.write("# %s\n" % GENERATED_STRING)
        yaml.indent(mapping=2, sequence=2, offset=2)
        yaml.dump(data, fp)


if __name__ == "__main__":
   generate_docker_compose(sys.argv[1:])