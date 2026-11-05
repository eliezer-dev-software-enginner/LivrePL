# Instruções para agentes

Use a skill versionada em `.agents/skills/livrepl/SKILL.md` para mudanças neste repositório.

- Leia `docs/CONTEXT.md`, `docs/DECISIONS.md` e os documentos técnicos relacionados antes de editar.
- Mantenha aqui apenas a linguagem AdvPL independente do Protheus; fixtures, banco simulado, MVC, browse e RPO pertencem ao AdvPLab.
- Toda mudança nova deve atualizar a documentação pertinente em `docs/`.
- Preserve o README como entrada pública de instalação e uso. Detalhes de implementação, decisões, caminhos locais e configuração da máquina pertencem a `docs/`.
- Rode `python -m unittest discover -s tests -v` antes de concluir.
