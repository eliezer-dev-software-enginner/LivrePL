# Contribuição e pull requests

## Validação automática

Pull requests executam `.github/workflows/pull-request.yml` em Python 3.8 e 3.12. O workflow instala o LivrePL em modo editável e executa:

```bash
python -m unittest discover -s tests -v
```

A validação usa apenas arquivos versionados e não depende de caminhos, ambientes virtuais ou configurações existentes no computador do autor.

## Skill do projeto

A skill `.agents/skills/livrepl/SKILL.md` orienta agentes sobre lexer, parser, runtime, biblioteca padrão, testes e o limite com o AdvPLab. Para instalá-la no Codex:

```bash
mkdir -p ~/.codex/skills/livrepl
cp .agents/skills/livrepl/SKILL.md ~/.codex/skills/livrepl/SKILL.md
```

## Política de documentação

Mudanças novas devem atualizar `docs/CONTEXT.md`, `docs/DECISIONS.md` e o documento técnico relacionado quando houver alteração de arquitetura, compatibilidade ou limites.

O README deve permanecer público e portátil. Ele pode explicar instalação, exemplos, capacidades e limitações, mas não deve conter caminhos absolutos, arquivos exclusivos da máquina, histórico de sessão, detalhes internos de implementação ou relatos das ferramentas usadas para construir o projeto. Esses conteúdos ficam em `docs/` e não devem ser necessários para executar o workflow de pull request.
