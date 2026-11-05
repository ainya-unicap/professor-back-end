# Forrageia · Professor (back-end)

API da área do professor do app Forrageia (Meu Canteiro). É ela que guarda os dados e aplica as regras. As telas ficam no repositório [professor-front](https://github.com/ainya-unicap/professor-front), que consome esta API.

Feito com Django e Django REST Framework, com autenticação por token JWT.

## Estrutura

```
config/       configurações do projeto e rotas principais
accounts/     usuários, login, cadastro e permissões
turmas/       turmas, matrículas, código de convite e painel do professor
relatorios/   relatórios dos alunos e status de correção
```

## Como funciona

### Usuários

O usuário é identificado pelo **e-mail**, que também é o login. Cada usuário tem um **papel**, `professor` ou `aluno`, e é o backend que define esse papel. O front só lê o papel e decide quais telas mostrar.

### Autenticação

Depois do login ou do cadastro, a API devolve dois tokens:

- `access`: enviado em todas as chamadas protegidas, no cabeçalho `Authorization: Bearer <token>`.
- `refresh`: usado para gerar um novo `access` quando ele expira.

Toda rota exige o token, exceto login, cadastro e renovação de token. As rotas da área do professor também exigem que o usuário tenha papel `professor`; um aluno recebe `403`.

### Modelos

- **Turma**: pertence a um professor e tem nome, período (`2026.1`, `2026.2`...), instituição, prazos e um **código de convite** de 6 caracteres gerado automaticamente. Um professor não pode ter duas turmas com o mesmo nome no mesmo período.
- **Matrícula**: liga um aluno a uma turma.
- **Relatório**: de um aluno em uma turma, com a planta acompanhada, as seções (introdução, objetivo, desenvolvimento, conclusão e referências), o PDF gerado pelo aluno, a nota, o feedback e o status `rascunho`, `entregue` (aguardando correção) ou `corrigido`. Relatórios em rascunho não aparecem para o professor.
- **Foto do relatório**: imagens do canteiro anexadas ao desenvolvimento, com legenda e ordem.

Os arquivos (PDF e fotos) não ficam públicos: só são entregues pelas rotas da API, para o professor da turma.

## Endpoints

| Método | Rota | O que faz |
|---|---|---|
| `POST` | `/api/auth/login/` | Valida e-mail e senha e devolve os tokens e os dados do usuário |
| `POST` | `/api/auth/cadastro/` | Cria uma conta de professor e já devolve os tokens e os dados do usuário |
| `POST` | `/api/auth/token/refresh/` | Gera um novo `access` a partir do `refresh` |
| `GET` | `/api/turmas/` | Lista as turmas do professor logado |
| `POST` | `/api/turmas/` | Cria uma turma para o professor logado |
| `GET` | `/api/turmas/<id>/` | Detalhe da turma, com link de convite e lista de alunos |
| `GET` | `/api/turmas/<id>/relatorios/` | Relatórios entregues da turma (aguardando correção primeiro) |
| `PATCH` | `/api/turmas/<id>/prazos/` | Atualiza os prazos da turma |
| `POST` | `/api/turmas/<id>/novo-codigo/` | Gera um novo código de convite (o anterior deixa de valer) |
| `GET` | `/api/professor/painel/` | Resumo do painel do professor |
| `GET` | `/api/professor/pendentes/` | Quantos relatórios aguardam correção (usado no menu) |
| `GET` | `/api/relatorios/<id>/` | Relatório completo, com o anterior e o próximo da turma |
| `PATCH` | `/api/relatorios/<id>/avaliacao/` | Salva nota e feedback; com `concluir` marca como corrigido |
| `GET` | `/api/relatorios/<id>/pdf/` | Download do PDF do relatório |
| `GET` | `/api/relatorios/<id>/fotos/<foto_id>/` | Imagem de uma foto do relatório |

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

Resposta `201`:

```json
{
  "id": 1,
  "nome": "Turma A",
  "periodo": "2026.1",
  "instituicao": "UNICAP",
  "codigo_convite": "K7MPQ3",
  "ativa": true,
  "alunos": 0,
  "relatorios_entregues": 0,
  "aguardando_correcao": 0,
  "inicio_registros": null,
  "encerramento_registros": null,
  "limite_entrega": null,
  "prazo_correcao": null,
  "aceitar_atrasadas": false
}
```

Erros de validação voltam com `400`, por exemplo `{"nome": ["Você já tem uma turma com esse nome neste período."]}`. A listagem devolve só as turmas do professor logado, no mesmo formato.

### Detalhe da turma

Além dos campos da listagem, devolve `link_convite` (montado a partir da configuração `CONVITE_URL_BASE` do `.env`, que deve apontar para a página do app do aluno que recebe o código) e `alunos_lista`:

```json
[
  { "id": 11, "nome": "Pedro Sá", "status": "entregue", "relatorio_id": 101 },
  { "id": 13, "nome": "Bruno Lima", "status": "corrigido", "relatorio_id": 103 },
  { "id": 14, "nome": "Carla Reis", "status": "sem_relatorio", "relatorio_id": null }
]
```

A lista vem ordenada: primeiro quem aguarda correção, depois os corrigidos e por fim quem ainda não entregou.

### Prazos

```json
{
  "inicio_registros": "2026-03-02",
  "encerramento_registros": "2026-06-05",
  "limite_entrega": "2026-06-12",
  "prazo_correcao": "2026-06-26",
  "aceitar_atrasadas": false
}
```

Todos são opcionais e podem ser `null`. As datas preenchidas precisam seguir a ordem acima; se uma vier antes da anterior, a resposta é `400` com o erro no campo.

### Relatório e avaliação

O detalhe traz o aluno, a turma (com o prazo de correção), as seções, as fotos (`id` e `legenda`), `tem_pdf`, a nota, o feedback e os ids do relatório `anterior` e `proximo` da mesma turma, na ordem de entrega.

Avaliação:

```json
{ "nota": "8.5", "feedback": "Ótimo acompanhamento.", "concluir": true }
```

- A nota vai de 0 a 10, com até duas casas decimais.
- Sem `concluir`, nota e feedback são salvos e o relatório continua aguardando correção.
- Com `concluir`, a nota passa a ser obrigatória e o relatório é marcado como corrigido.

### Painel

Junta numa resposta tudo o que a tela inicial do professor precisa, considerando só as turmas ativas:

```json
{
  "periodo_atual": "2026.1",
  "instituicao": "UNICAP",
  "resumo": {
    "aguardando_correcao": 7,
    "turmas_com_pendencia": 2,
    "turmas_ativas": 2,
    "alunos": 34,
    "prazo_avaliacao": "2026-06-20"
  },
  "turmas": [ "... até 3 turmas, no formato da listagem ..." ],
  "aguardando": [
    { "id": 10, "aluno": "Pedro Sá", "planta": "Camelo", "turma": "Turma A", "entregue_em": "..." }
  ]
}
```

- `aguardando_correcao`: relatórios com status `entregue`.
- `alunos`: alunos distintos matriculados nas turmas ativas.
- `prazo_avaliacao`: o próximo prazo de correção que ainda não passou, ou `null`.
- `aguardando`: os 4 relatórios entregues há mais tempo.

### Tokens

O `access` vale 30 minutos e o `refresh` vale 8 horas.

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

Para acessar o admin (`/admin/`), crie um superusuário com `python manage.py createsuperuser`. Pelo admin dá para cadastrar turmas, matrículas e relatórios de teste para ver o painel com dados.

## Testes

```bash
python manage.py test
```

## Fluxo de trabalho

- Uma branch por tela, criada a partir da `main`, por exemplo `feat/cadastro`.
- Um PR por tela, contra a `main`.
- Quando a tela também mexer no front, a branch tem o mesmo nome nos dois repositórios.
