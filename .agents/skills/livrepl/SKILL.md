---
name: livrepl
description: Desenvolver, testar e documentar o LivrePL, interpretador da linguagem AdvPL pura sem AppServer. Use para lexer, parser, AST, runtime, escopo, tipos, biblioteca padrão e CLI da linguagem; recursos específicos do Protheus e fixtures pertencem ao AdvPLab.
---

# Desenvolvimento do LivrePL

Use esta skill ao alterar o interpretador LivrePL ou investigar comportamento da linguagem AdvPL independente do Protheus.

## Escopo

O LivrePL fornece a base simplificada da linguagem: pré-processamento, carregamento de fontes, lexer, parser, AST, execução, tipos, escopo, funções padrão e CLI. Ele roda código AdvPL puro no terminal sem AppServer, banco, licença ou interface.

Não adicione aqui banco simulado, SX3, aliases Protheus, MVC, FWBrowse, fixtures ou compilação no RPO. Esses recursos pertencem ao AdvPLab, que estende o LivrePL para testes de código Protheus.

## Fluxo de trabalho

Ao reproduzir chamadas da CLI, aceite as formas equivalentes `livrepl arquivo.prw Funcao` e `livrepl --run arquivo.prw Funcao`. Preserve caminhos relativos com subdiretorios e use `--arg` para texto ou `--args-json` para valores tipados.

Na CLI, erros conhecidos devem produzir diagnostico curto, vermelho em terminal interativo e codigo diferente de zero, sem traceback. Preserve `NO_COLOR` e mantenha `run_file()` propagando excecoes para uso programatico.

1. Leia `docs/CONTEXT.md`, `docs/DECISIONS.md` e o documento técnico relacionado.
2. Reproduza a sintaxe ou o comportamento com o menor fonte `.prw` possível.
3. Preserve nomes case-insensitive, arrays 1-based, escopo dinâmico de `PRIVATE`, isolamento de `LOCAL` e persistência de `STATIC`.
4. Mude a camada correta: preprocessador, carregador, lexer, parser, runtime ou biblioteca padrão.
5. Cubra o comportamento com teste automatizado e execute `python -m unittest discover -s tests -v`.
6. Quando a CLI ou o uso público mudar, valide também um exemplo em `exemplos/`.
7. Atualize a documentação pertinente e revise o diff antes de concluir.

O suporte do LivrePL é deliberadamente menor que o ecossistema Protheus. Não declare equivalência com AppServer nem aceite uma API de framework apenas para fazer um fonte específico passar.

## Documentação

Mudanças novas devem ser registradas em `docs/`. Use `docs/CONTEXT.md` para o estado consolidado, `docs/DECISIONS.md` para decisões e um documento técnico específico quando a alteração exigir explicar desenho, compatibilidade ou limites.

O README deve explicar o produto para quem encontrou somente o repositório: propósito, requisitos, instalação, primeiros exemplos, capacidades, limitações e links. Não inclua caminhos absolutos do computador, arquivos locais, histórico de sessão, ferramentas usadas para construir uma mudança ou detalhes internos extensos. Coloque esses assuntos em `docs/`, `AGENTS.md` ou documentação de contribuição. Atualize o README quando a instalação ou o uso público mudar.

## Instalação da skill

No checkout do LivrePL:

```bash
mkdir -p ~/.codex/skills/livrepl
cp .agents/skills/livrepl/SKILL.md ~/.codex/skills/livrepl/SKILL.md
```

Depois, reinicie a sessão do agente para que a skill seja descoberta.
