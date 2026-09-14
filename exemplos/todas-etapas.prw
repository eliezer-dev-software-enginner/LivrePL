# Exemplo combinando tudo da Etapa 4: DO CASE, BEGIN SEQUENCE,
# code blocks (Eval) e CLASS/METHOD com heranca.

Function Main()
    Local n := 2

    Do Case
    Case n == 1
        ? "um"
    Case n == 2
        ? "dois"
    Otherwise
        ? "outro"
    EndCase

    Begin Sequence
        Local aVazio := {}
        ? aVazio[1]
    Recover Using cErro
        ? "Erro capturado:", cErro
    End Sequence

    Local bSoma := {|x, y| x + y}
    ? "Eval bloco:", Eval(bSoma, 2, 3)

    Local oPessoa := Pessoa():New("Maria", 30)
    oPessoa:Cumprimentar()
    ? "Idade:", oPessoa:nIdade

    Local oAluno := Aluno():New("Joao", 20, "Turma A")
    oAluno:Cumprimentar()          // herdado de Pessoa
    ? "Turma:", oAluno:cTurma

Return NIL

Class Pessoa
    Data cNome
    Data nIdade

    Method New(cNome, nIdade) Constructor
    Method Cumprimentar()
EndClass

Method New(cNome, nIdade) Class Pessoa
    ::cNome := cNome
    ::nIdade := nIdade
Return Self

Method Cumprimentar() Class Pessoa
    ? "Ola, meu nome e " + ::cNome
Return NIL

Class Aluno From Pessoa
    Data cTurma

    Method New(cNome, nIdade, cTurma) Constructor
EndClass

Method New(cNome, nIdade, cTurma) Class Aluno
    ::cNome := cNome
    ::nIdade := nIdade
    ::cTurma := cTurma
Return Self