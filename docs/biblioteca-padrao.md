# Biblioteca padrao do LivrePL

Atualizacao: 05/10/2026. O interpretador registra 69 funcoes sem depender de TestLab, AppServer ou banco.

| Grupo | Funcoes |
|---|---|
| Texto e conversao | Len, Str, CValToChar, AllTrim, Upper, Lower, SubStr, Val, Space, PadR, PadL, StrTran, Chr, At, Left, EncodeUTF8, Transform, Right, Replicate, RAt, LTrim, RTrim, Trim, Asc, StrZero, PadC |
| Arrays | AAdd, ASize, ALen, AClone, AScan, Array, AFill, ACopy, ADel, AIns, ATail, AEval |
| Datas e relogio | Date, Time, CToD, DToC, SToD, DToS, Day, Month, Year, Seconds |
| Numeros e condicoes | IIf, Round, Int, Abs, Max, Min, Empty |
| Tipos, blocos e erros | ValType, Type, Eval, UserException, Throw, ErrorBlock, Break, FreeObj |
| Terminal e arquivos | ConOut, Alert, FCreate, FWrite, FClose, FError |

## Migracao do TestLab

Foram centralizadas 21 funcoes antes exclusivas do TestLab: StrTran, Chr, At, Type, AClone, ErrorBlock, Break, Left, EncodeUTF8, FreeObj, Transform, DToC, CToD, AScan, ConOut, Alert, Date, Time, FCreate, FWrite e FClose.

O TestLab conserva overrides de Date/Time para os valores do fixture, de arquivos para armazenamento virtual e de Alert para a saida headless. As demais funcoes acima sao herdadas. APIs de banco/RDD, MVC, SMTP e dicionario de dados continuam na camada de ambiente do TestLab.

## Recursos acrescentados apos pesquisa

As 23 novas funcoes sao SToD, DToS, Day, Month, Year, Right, Replicate, RAt, LTrim, RTrim, Trim, Asc, StrZero, PadC, Array, AFill, ACopy, ADel, AIns, ATail, AEval, FError e Seconds. O operador `$` tambem e reconhecido diretamente pelo LivrePL.

## Comportamento e limites

- `AdvPLDate` representa datas entre 01/01/0100 e 31/12/2999, inclusive uma data vazia distinta de NIL. Date() usa o relogio do sistema. Data + numero inteiro desloca dias; data - data retorna quantidade de dias. Erros de tipo e de intervalo produzem AdvPLRuntimeError.
- CToD/DToC usam DD/MM/AAAA por padrao. O atributo `Interpreter.date_format` permite outro formato Python em integracoes; comandos AdvPL SET DATE/SET CENTURY ainda nao sao interpretados. CToD/SToD invalidos retornam data vazia; DToC de data vazia retorna texto vazio e DToS retorna oito espacos.
- Type avalia expressoes suportadas pelo parser no escopo atual, incluindo LOCAL/PRIVATE. Variaveis ausentes e expressoes invalidas retornam U. ValType identifica datas, blocos e objetos como D/B/O.
- AClone copia arrays recursivamente, conserva ciclos e referencias a objetos. ACopy copia referencias de arrays aninhados; AFill atribui a mesma referencia a cada posicao. ADel/AIns mantem o tamanho do array. AEval recebe valor e indice original em seu bloco.
- ErrorBlock armazena/restaura o handler e o invoca em erros de avaliacao com objeto ERROR e Description. Break pode transferir o controle para RECOVER. Retry e semantica completa de erros do AppServer permanecem fora da cobertura.
- Chr/Asc usam os codigos CP1252 de 0 a 255. Strings internas sao Unicode; EncodeUTF8 preserva o texto logico e nao modela buffers de bytes ou pagina de codigo do AppServer.
- Transform cobre numero com casas decimais/separadores, @E, @! e datas. Nao implementa todo o catalogo de pictures. PadC aceita preenchimento opcional; PadL/PadR mantem o comportamento anterior.
- Alert e ConOut escrevem no terminal; Alert nao abre dialogo nem oferece selecao de botoes.
- FCreate/FWrite/FClose usam arquivos locais e bytes CP1252; FWrite aceita quantidade opcional. FCreate retorna -1 em falha, FWrite retorna zero e FClose retorna falso. FError informa o codigo do sistema operacional. Atributos especiais, compartilhamento exclusivo, caminhos do SmartClient e demais parametros de plataforma ainda nao sao reproduzidos.

## Referencias oficiais consultadas

- [Catalogo de snippets mantido pela TOTVS](https://github.com/totvs/advpl-vscode/blob/master/snippets/advpl.json): assinaturas e descricoes de texto, arrays, conversoes, datas e arquivos.
- [Day — TDN](https://tdn.totvs.com/display/tec/Day): componente dia e retorno zero para data vazia.
- [LTrim — TDN](https://tdn.totvs.com/display/framework/LTrim): remocao de espacos a esquerda.
- [Conversao de texto para data — suporte TOTVS](https://centraldeatendimento.totvs.com/hc/es/articles/360025970853-Cross-Segmentos-TOTVS-BackOffice-L%C3%ADnea-Protheus-MI-ADVPL-Como-convertir-un-caracter-String-a-tipo-fecha-Data-en-ADVPL): CToD e SToD.
- [Tipos de dados — TDN](https://tdn.totvs.com/plugins/viewsource/viewpagesrc.action?pageId=152798746): datas vazias, intervalo de anos e referencias de arrays.

As assinaturas e os exemplos guiam a implementacao local; isso nao certifica compatibilidade integral com todas as versoes do AppServer.
