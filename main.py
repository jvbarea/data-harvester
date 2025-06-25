# File: src/main.py
#!/usr/bin/env python3
import time
import logging
import argparse
from src.collectors.rss import run_corporate
from src.collectors.rss_macro import run_macro

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Orquestrador de RSS corporate + macro'
    )
    parser.add_argument('-d', '--debug', action='store_true', help='Ativa DEBUG')
    parser.add_argument('--which', choices=['corporate','macro','all'], default='all', help='Define qual coletor rodar')
    parser.add_argument('-o', '--once', action='store_true', help='Executa apenas uma vez')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='[%(levelname)s] %(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.info('Orquestrador iniciado: %s, once=%s', args.which, args.once)

    def do_run():
        if args.which in ('corporate','all'):
            logging.info('→ rodando corporate')
            run_corporate(args.debug)
        if args.which in ('macro','all'):
            logging.info('→ rodando macro')
            run_macro(args.debug)

    if args.once:
        do_run()
    else:
        while True:
            do_run()
            time.sleep(60)
