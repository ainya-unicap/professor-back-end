# Forrageia · Professor (back-end)

API da área do professor do app Forrageia (Meu Canteiro). É ela que guarda os dados e aplica as regras. As telas ficam no repositório [professor-front](https://github.com/ainya-unicap/professor-front), que consome esta API.

Feito com Django e Django REST Framework, com autenticação por token JWT.

## Estrutura

```
config/       configurações do projeto e rotas principais
accounts/     usuários, login, cadastro e permissões
turmas/       turmas, matrículas e código de convite
relatorios/   relatórios entregues pelos alunos e o PDF de cada um
```

## Como funciona

### Usuários

O usuário é identificado pelo **e-mail**, que também é o login. Cada usuário tem um **papel**, `professor` ou `aluno`, e é o backend que define esse papel. O front só lê o papel e decide quais telas mostrar.

### Autenticação

Depois do login ou do cadastro, a API devolve dois tokens:

- `access`: enviado em todas as chamadas protegidas, no cabeçalho `Authorization: Bearer <token>`.
- `refresh`: usado para gerar um novo `access` quando ele expira.

Toda rota exige o token, exceto login, cadastro e renovação de token. As rotas de turmas e relatórios também exigem papel `professor`; um aluno recebe `403`. Cada professor só enxerga as próprias turmas; turma ou relatório de outro professor responde `404`.

O `access` vale 30 minutos e o `refresh` vale 8 horas.

### Modelos

- **Turma**: pertence a um professor e tem nome, período (`2026.1`, `2026.2`...), instituição e um **código de convite** de 6 caracteres gerado automaticamente. Um professor não pode ter duas turmas com o mesmo nome no mesmo período.
- **Matrícula**: liga um aluno a uma turma.
- **Relatório**: de um aluno em uma turma, com a planta acompanhada, o PDF e o status `rascunho` ou `entregue`. Só os entregues aparecem para o professor.

O PDF não fica público: ele só é entregue pela rota da API, para o professor da turma.

## Endpoints

| Método | Rota | O que faz |
|---|---|---|
| `POST` | `/api/auth/login/` | Valida e-mail e senha e devolve os tokens e os dados do usuário |
| `POST` | `/api/auth/cadastro/` | Cria uma conta de professor e já devolve os tokens e os dados do usuário |
| `POST` | `/api/auth/token/refresh/` | Gera um novo `access` a partir do `refresh` |
| `GET` | `/api/turmas/` | Lista as turmas do professor logado |
| `POST` | `/api/turmas/` | Cria uma turma para o professor logado |
| `GET` | `/api/turmas/<id>/` | Dados de uma turma, com o link de convite |
| `GET` | `/api/turmas/<id>/relatorios/` | Relatórios entregues da turma, do mais recente para o mais antigo |
| `GET` | `/api/relatorios/<id>/pdf/` | Download do PDF de um relatório |

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

### Turmas

Criação:

```json
{ "nome": "Turma A", "periodo": "2026.1", "instituicao": "UNICAP" }
```

Resposta `201` (a listagem e o detalhe usam o mesmo formato):

```json
{
  "id": 1,
  "nome": "Turma A",
  "periodo": "2026.1",
  "instituicao": "UNICAP",
  "codigo_convite": "K7MPQ3",
  "link_convite": "https://<app do aluno>/convite/K7MPQ3",
  "ativa": true,
  "alunos": 18,
  "relatorios_entregues": 13
}
```

- `link_convite` é montado com a configuração `CONVITE_URL_BASE` do `.env`, que deve apontar para a página do app do aluno que recebe o código.
- Erros de validação voltam com `400`, por exemplo `{"nome": ["Você já tem uma turma com esse nome neste período."]}`.

### Relatórios da turma

```json
[
  { "id": 10, "aluno": "Pedro Sá", "planta": "Camelo", "entregue_em": "2026-06-09T13:00:00Z", "tem_pdf": true }
]
```

Quando `tem_pdf` é `true`, o arquivo pode ser baixado em `/api/relatorios/<id>/pdf/`.

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

Para acessar o admin (`/admin/`), crie um superusuário com `python manage.py createsuperuser`. Pelo admin dá para cadastrar matrículas e relatórios de teste.

## Testes

```bash
python manage.py test
```

## Fluxo de trabalho

- Uma branch por tela, criada a partir da `main`, por exemplo `feat/cadastro`.
- Um PR por tela, contra a `main`.
- Quando a tela também mexer no front, a branch tem o mesmo nome nos dois repositórios.
