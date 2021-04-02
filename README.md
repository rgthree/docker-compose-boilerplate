# docker-compose-boilerplate

Boilerplate and python pre-process scripts, including setup for Traefik and
Cloudflare.

YAML doesn't support advanced enough mixins, so we use python to generate a
valid `docker-compose.yaml` and local `.env` file from.

## Setup

1. Run `init.py` which will disconnect the boilerplate from this repo and
   rename the template files.
2. Install ruamel.yaml: `pip3 install ruamel.yaml`
2. Go ahead and delete `init.py`.
2. Configure base, global environment vars in `base.env`
3. Configure any domain names or other Traefik config in
   `proxy/volumes/traefik/dynamic_conf.toml` and
   `proxy/volumes/traefik/traefik.toml`