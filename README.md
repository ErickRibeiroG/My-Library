# 📚 My Library

Aplicação web em Django para organizar sua biblioteca pessoal: busque livros em milhões de títulos, organize-os em estantes (**Quero ler**, **Comprados**, **Lidos**), avalie suas leituras e acompanhe suas estatísticas.

## Recursos

- **Biblioteca por usuário**: cada conta tem os próprios livros, isolados das demais.
- **Busca resiliente**: Google Books como fonte principal, com fallback automático para a Open Library quando o Google estiver indisponível ou limitando requisições. Resultados ficam em cache e a paginação é real.
- **Estantes**: mova livros entre *Quero ler*, *Comprados* e *Lidos*. Adicionar um livro que já está na estante só muda o status, sem duplicar.
- **Avaliação** de 1 a 5 estrelas nos livros lidos (clique de novo na mesma estrela para remover).
- **Painel inicial** com total de livros, lidos no ano, páginas lidas, média de avaliação e progresso da estante.
- **Minha estante**: filtro por status, busca por título/autor/categoria, ordenação e paginação.
- **Página de detalhes** com sinopse, ficha e link para a fonte.
- **Conta**: cadastro com validação de senha, login por e-mail ou nome de usuário, perfil editável e troca de senha.
- **Interface** responsiva (menu lateral no celular), modo escuro automático e capas geradas quando o livro não tem imagem.

## Stack

Python 3.13 · Django 6 · requests · SQLite · HTML/CSS/JS puros (sem build).

## Estrutura

```
my_library/          configurações (settings lê variáveis de ambiente / .env)
account/             autenticação: backend por e-mail, formulários, login/cadastro/perfil
core/                livros: modelo, views, formulários, templatetags
  services/          integrações de busca (googlebooks.py, openlibrary.py, base.py)
templates/           layouts e parciais compartilhados (base, app, auth)
static/              css/app.css e js/app.js
```

## Como rodar

```bash
python -m venv env
# Windows: env\Scripts\activate   |   Linux/macOS: source env/bin/activate
pip install -r requirements.txt

cp .env.example .env          # opcional: ajuste as variáveis
python manage.py migrate
python manage.py createsuperuser   # opcional, para acessar /admin/
python manage.py runserver
```

Acesse http://127.0.0.1:8000/ e crie sua conta.

### Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `DJANGO_SECRET_KEY` | chave de desenvolvimento | **Obrigatória** com `DJANGO_DEBUG=False` |
| `DJANGO_DEBUG` | `True` | Modo debug |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Hosts permitidos (separados por vírgula) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | — | Origens confiáveis em produção |
| `DJANGO_DB_PATH` | `db.sqlite3` | Caminho do banco SQLite |
| `GOOGLE_BOOKS_API_KEY` | — | Recomendado; sem chave o Google limita as requisições |
| `BUSCA_CACHE_SEGUNDOS` | `3600` | Tempo de cache das buscas |
| `BUSCA_TIMEOUT_SEGUNDOS` | `6` | Timeout das chamadas às APIs |

## Rotas

| Rota | Descrição |
|---|---|
| `/` | Login |
| `/cadastro/` | Criar conta |
| `/perfil/` | Dados pessoais e senha |
| `/home/` | Painel com estatísticas e estantes |
| `/home/livros/` | Minha estante (`?status=`, `?q=`, `?ordem=`) |
| `/home/livros/<id>/` | Detalhes do livro |
| `/home/buscar/` | Busca (`?q=`, `?pagina=`) |
| `/admin/` | Administração do Django |

## Testes

```bash
python manage.py test
```

Os testes cobrem modelo, isolamento entre usuários, views, autenticação e os serviços de busca (com as APIs simuladas, sem acesso à rede).

## Produção (checklist)

- Defina `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` e `DJANGO_CSRF_TRUSTED_ORIGINS`.
- Rode `python manage.py collectstatic` e sirva `staticfiles/` (ex.: WhiteNoise ou o servidor web).
- Use um servidor WSGI (gunicorn / waitress) e, se possível, PostgreSQL.
- Para mais de um processo, troque o cache em memória (`CACHES`) por Redis ou banco.
