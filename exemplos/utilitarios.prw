Function Main()
    Local dInicio := SToD('20240228')
    Local aValores := AFill(Array(3), 0)

    ? 'Tipo de Date():', ValType(Date())
    ? 'Data atual:', DToC(Date())
    ? 'Hora atual:', Time()
    ? 'Dois dias depois:', DToC(dInicio + 2)
    ? 'Dia / mes / ano:', Day(dInicio), Month(dInicio), Year(dInicio)
    ? 'Codigo:', StrZero(42, 5)
    ? 'Texto:', Replicate(Right('ABCD', 2), 2)
    ? 'Busca:', 'BC' $ 'ABCD'
    AFill(aValores, 9, 2, 2)
    ? 'Array:', aValores
Return Nil
