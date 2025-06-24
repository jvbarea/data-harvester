# Data Harvester

**Data Harvester** é um serviço de ingestão e distribuição de dados financeiros com foco em **notícias corporativas**, **notícias macroeconômicas** e, futuramente, **cotações de ações**. Ele coleta feeds RSS de diversas fontes, limpa e normaliza o conteúdo, armazena em um banco PostgreSQL (via Supabase) e serve como base para toda a cadeia de análise e notificação.

## Funcionalidades Principais

- **Coleta Agendada de RSS**  
  Captura automaticamente, a cada 5 minutos, os itens de múltiplos feeds corporativos e macroeconômicos.

- **Armazenamento Imutável**  
  As notícias brutas são guardadas em `raw_news` e `raw_news_macro`, preservando o JSON/XML original para auditoria e reprocessamento.

- **Pipeline de Limpeza**  
  Separadamente, roda jobs de limpeza que extraem título, corpo e metadados em `cleaned_news` e `cleaned_news_macro`, prontos para NLP e machine learning.

- **Integração com Supabase**  
  Usa a SDK oficial (`supabase-py`) para inserir dados e empregar Row Level Security (RLS), garantindo acesso seguro e multi-tenant.

- **Módulo de Mapeamento de Empresas**  
  Lê dinamicamente a tabela `company_map` para extrair tickers e nomes canônicos sem necessidade de re-deploy do código.

## Estrutura do Repositório


## Tecnologias

- **Python 3.12**  
- **feedparser**, **requests**, **BeautifulSoup**  
- **Supabase (Postgres + RLS + pg_cron)**  
- **GitHub Actions** para agendamento e CI/CD  

## Como Começar

1. Crie um projeto no Supabase e habilite as extensões `pgcrypto` e `pg_cron`.  
2. Configure seu `.env` local com `SUPABASE_URL` e `SUPABASE_KEY`.  
3. Ajuste e insira suas fontes de RSS em `feeds_corporate.yml` e `feeds_macro.yml`.  
4. Execute localmente com:
   ```bash
   python src/collectors/rss.py --debug
   python src/collectors/rss_macro.py --debug
