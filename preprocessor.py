# preprocessor.py
# Pré-processador simples (escopo v1 do documento de escopo):
#   - #define NOME valor  -> substituição simples de constantes
#   - #include "..."      -> no-op (não simulamos os .ch completos)
#   - #command / #xtranslate -> fora do escopo v1, linhas são removidas
#
# Roda ANTES do lexer. Substituições são best-effort (por palavra, sem
# analisar se a palavra está dentro de uma string).

import re

_DEFINE_RE = re.compile(
    r"^\s*#\s*define\s+([A-Za-z_][A-Za-z0-9_]*)\b\s*(.*)$",
    re.IGNORECASE,
)
_INCLUDE_RE = re.compile(r"^\s*#\s*include\b", re.IGNORECASE)
_COMMAND_RE = re.compile(r"^\s*#\s*(command|xtranslate)\b", re.IGNORECASE)


def preprocess(source: str) -> str:
    defines = {}
    out_lines = []

    for raw in source.splitlines():
        m = _DEFINE_RE.match(raw)
        if m:
            name = m.group(1)
            value = m.group(2).strip()
            defines[name.upper()] = value
            continue
        if _INCLUDE_RE.match(raw):
            continue
        if _COMMAND_RE.match(raw):
            # fora do escopo v1; remove a linha
            continue
        if raw.lstrip().startswith("#"):
            # diretiva não reconhecida / linha de comentário '#...'
            continue
        out_lines.append(raw)

    text = "\n".join(out_lines)

    for name, value in defines.items():
        text = re.sub(rf"\b{name}\b", value, text, flags=re.IGNORECASE)

    return text