# GMC Sport – Back-end (FastAPI + PostgreSQL)

## Estrutura
```
backend/
├── app/
│   ├── main.py          # app, CORS, rotas, (opcional) serve o site estático
│   ├── config.py        # variáveis de ambiente (.env)
│   ├── database.py      # conexão PostgreSQL / sessão
│   ├── models.py        # tabelas: users, settings, production_logs, quinzenas
│   ├── schemas.py       # validação de entrada/saída
│   ├── security.py      # senha (bcrypt), JWT, permissões Chefe/Operador
│   └── routers/         # auth, usuarios, config, producao, pagamentos
├── requirements.txt
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

## Rodar local (Docker)
```
cd backend
cp .env.example .env      # troque SECRET_KEY
docker compose up --build
```
Documentação interativa: http://localhost:8000/docs

## Rodar sem Docker
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # ajuste DATABASE_URL e SECRET_KEY
uvicorn app.main:app --reload
```

## Rotas principais
| Método | Rota | Quem | O que faz |
|---|---|---|---|
| POST | /auth/setup-chefe | público (1x) | cria a conta do Chefe |
| POST | /auth/login/chefe | público | login com e-mail/celular + senha |
| POST | /auth/login/operador | público | login com nome + telefone + senha |
| GET | /auth/me | logado | dados do usuário logado |
| POST/GET | /usuarios | Chefe | cadastra / lista operadores (setor Selado ou Embalado) |
| GET/PATCH/DELETE | /usuarios/{id} | Chefe | ver / editar / excluir |
| GET | /config | logado | valor por bloquinho |
| PUT | /config | Chefe | altera o valor (vale para os próximos lançamentos) |
| POST | /producao | Chefe | lança produção (usuário, data, quantidade) |
| GET | /producao | logado | lista lançamentos (filtros: usuario_id, inicio, fim, pago) |
| GET | /producao/calendario?ano=&mes= | logado | total por dia do mês |
| DELETE | /producao/{id} | Chefe | exclui lançamento ainda não pago |
| GET | /resumo | Chefe | total / pendente / recebido de cada usuário |
| GET | /resumo/meu | Operador | o mesmo, só dos próprios dados |
| POST | /usuarios/{id}/pagar | Chefe | marca o pendente do usuário como recebido |
| POST | /quinzenas/fechar | Chefe | fecha a quinzena (tudo pendente vira recebido) |
| GET | /quinzenas | Chefe | histórico de quinzenas fechadas |

Autenticação: enviar `Authorization: Bearer <token>`. Operador só vê os próprios dados.

## Site estático
- Defina `CORS_ORIGINS` com o endereço do site (ex.: https://meusite.netlify.app).
- Ou aponte `STATIC_DIR` para a pasta do front-end e a API entrega o site junto.
- Hospedagem sugerida: Render ou Railway (API + PostgreSQL gerenciado). Defina
  `DATABASE_URL` (com `postgresql+psycopg://`), `SECRET_KEY` e `CORS_ORIGINS`.

## Observações
- As tabelas são criadas automaticamente na primeira execução. Para mudanças futuras no banco, use Alembic.
- Não consegui rodar a API neste ambiente (sem acesso à internet para instalar as dependências); o código foi apenas verificado quanto a erros de sintaxe. Teste em /docs antes de usar.
