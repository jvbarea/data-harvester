# File: src/collectors/rss.py
#!/usr/bin/env python3
import os
import logging
from dotenv import load_dotenv
from supabase import create_client

# Carrega variáveis de ambiente (.env)
load_dotenv()



if __name__ == '__main__':
    # Configura logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logging.info("Iniciando Teste")
    logging.info("Função principal iniciada")
    # Configura Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    logging.info("SUPABASE_URL: %s", SUPABASE_URL)
    logging.info("SUPABASE_KEY (prefixo): %s…", SUPABASE_KEY[:8] if SUPABASE_KEY else None)
    if not SUPABASE_URL or not SUPABASE_KEY:
        logging.error('Defina SUPABASE_URL e SUPABASE_KEY no .env')
        exit(1)

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logging.info("supabase %s", supabase)

        response = supabase.table('tickers_list').select('ticker').execute()
        # Inserção de um único registro
        # response = (
        #     supabase
        #     .table("raw_news")
        #     .insert({"guid": "teste_conexao", "feed_id":"teste1", "title": "Teste de Conexão"})
        #     .execute()
        # )
        logging.info("resultado: %s",response.data)
    except Exception as e:
        logging.error("Erro ao inserir dados: %s", e)
        exit(1)