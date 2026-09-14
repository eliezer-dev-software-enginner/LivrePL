# AI_RULES.md — Regras do assistente de IA

## Regra 1: Nunca fazer push diretamente

O assistente de IA **não deve executar `git push`** por conta própria, em nenhuma circunstancia, salvo pedido explicito do usuario no momento.

Fluxo obrigatorio:

1. Fazer commit local com mensagem clara e descritiva
2. Informar ao usuario que o commit esta pronto
3. **Aguardar** o usuario permitir o push (ou executar o push manualmente)
4. So entao, com autorizacao explicita, rodar `git push origin main`

Se o usuario pedir apenas para "fazer commit" ou "aplicar a correcao", isso **não** autoriza push.

## Regra 2: Commit

- Fazer commit somente quando o usuario pedir explicitamente
- Mensagem de commit concisa, no padrao do repositorio
- Stage apenas os arquivos relevantes para a mudanca
- Nunca commitar segredos/chaves

## Regra 3: Consultar contexto no inicio de toda sessao

Em toda sessao nova, consultar antes de qualquer alteracao:

1. `README.md`
2. `docs/CONTEXT.md`
3. Codigo-fonte do projeto (`lexer.py`, `parser.py`, `interpreter.py`, `main.py`, `preprocessor.py`)
4. `docs/DECISIONS.md` (historico de modificacoes)

## Regra 4: Registrar modificacoes

Toda alteracao de codigo ou arquivo do projeto deve ser registrada em `docs/DECISIONS.md` antes do commit.