#include "protheus.ch"

Function Main()
    Local nTotal := 0
    Local aItens := {10, 20, 30}
    Local i

    ? "Inicio da execucao sem licenca..."

    For i := 1 To Len(aItens)
        nTotal += aItens[i]
    Next

    If nTotal > 50
        ? "Total alto:", Str(nTotal)
    Else
        ? "Total baixo:", Str(nTotal)
    EndIf

    Private cMsg := "definida em Main"
    MostraPrivate()

    ? "AllTrim:", "[" + AllTrim("  espacos  ") + "]"
    ? "ValType nTotal:", ValType(nTotal)
    ? "Upper:", Upper("advpl")

Return NIL

Function MostraPrivate()
    // cMsg herdada de Main() via escopo dinamico de PRIVATE
    ? "Dentro de MostraPrivate, cMsg =", cMsg
Return NIL