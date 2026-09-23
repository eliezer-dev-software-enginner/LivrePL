User Function ex13()
    Local aNums := {5, -3, 8, -1, 0, 12, -7}
    Local nPositivos := 0
    Local nNegativos := 0
    ContarNumeros(aNums, @nPositivos, @nNegativos)
    ? "Total positivos: " + cValToChar(nPositivos)
    ? "Total negativos: " + cValToChar(nNegativos)
Return NIL

Static Function ContarNumeros(aNums, nPos, nNeg)
    Local i
    For i := 1 To Len(aNums)
        If aNums[i] > 0
            nPos += 1
        ElseIf aNums[i] < 0
            nNeg += 1
        EndIf
    Next i
Return NIL
