# Forrageia · Professor (back-end)

API da área do professor do app Forrageia (Meu Canteiro). É ela que guarda os dados e aplica as regras. As telas ficam no repositório [professor-front](https://github.com/ainya-unicap/professor-front), que consome esta API.

Feito com Django e Django REST Framework, com autenticação por token JWT.

## Estrutura

```
config/       configurações do projeto e rotas principais
accounts/     usuários, login e cadastro
turmas/       turmas, convites e prazos (em construção)
relatorios/   relatórios dos alunos e correção (em construção)
```

## Como funciona

### Usuários

O usuário é identificado pelo **e-mail**, que também é o login. Cada usuário tem um **papel**, `professor` ou `aluno`, e é o backend que define esse papel. O front só lê o papel e decide quais telas mostrar.

### Autenticação

Depois do login ou do cadastro, a API devolve dois tokens:

- `access`: enviado em todas as chamadas protegidas, no cabeçalho `Authorization: Bearer <token>`.
- `refresh`: usado para gerar um novo `access` quando ele expira.

Toda rota exige o token, exceto login, cadastro e renovação de token.

## Endpoints

| Método | Rota | O que faz |
|---|---|---|
| `POST` | `/api/auth/login/` | Valida e-mail e senha e devolve os tokens e os dados do usuário |
| `POST` | `/api/auth/cadastro/` | Cria uma conta de professor e já devolve os tokens e os dados do usuário |
| `POST` | `/api/auth/token/refresh/` | Gera um novo `access` a partir do `refresh` |

### Login

Requisição:

```json
{ "email": "prof@exemplo.com", "password": "..." }
```

Resposta `200`:

```json
{
  "access": "...",
  "refresh": "...",
  "usuario": {
    "id": 1,
    "nome": "Maria Lima",
    "email": "prof@exemplo.com",
    "matricula": null,
    "papel": "professor"
  }
}
```

Se o e-mail ou a senha estiverem errados, a resposta é `401`.

### Cadastro

Requisição:

```json
{ "nome": "Maria Lima", "email": "prof@exemplo.com", "password": "..." }
```

Se der certo, a resposta é `201`, no mesmo formato do login. Se der errado, a resposta é `400`, com a lista de erros de cada campo:

```json
{ "email": ["Já existe uma conta com este e-mail."] }
```

Regras do cadastro:

- O nome precisa ter nome e sobrenome. Os espaços sobrando são removidos.
- O e-mail precisa ser único, sem diferenciar maiúsculas de minúsculas, e é salvo em minúsculas.
- A senha passa pelos validadores padrão do Django: tamanho mínimo, senhas comuns, senha só com números e senha parecida com os dados do usuário.
- A conta é criada sempre com o papel `professor`.

## Rodando localmente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 8000
```

Preencha o `.env` a partir do `.env.example`. O `.env` não vai para o git.

Para acessar o admin (`/admin/`), crie um superusuário com `python manage.py createsuperuser`.

## Testes

```bash
python manage.py test
```

## Fluxo de trabalho

- Uma branch por tela, criada a partir da `main`, por exemplo `feat/cadastro`.
- Um PR por tela, contra a `main`.
- Quando a tela também mexer no front, a branch tem o mesmo nome nos dois repositórios.
