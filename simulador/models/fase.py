from ..controllers.calculadora_ic import *
from ..views.view import *

class Fase(object):
    def __init__(self, id, tempoInicial):
        self.__id = id
        self.__pacotes = []
        self.__pacotesDados = []
        self.__pacotesVoz = []
        self.__tempoInicial = tempoInicial

        ### Atributos usados para calculos estatisticos
        self.__pessoasFilaVozPorTempo = []
        self.__pessoasFilaEspera1PorTempo = []
        self.__pessoasFilaDadosPorTempo = []
        self.__pessoasFilaEspera2PorTempo = []
        self.__somatorioPessoasFilaVozPorTempo = 0
        self.__somatorioPessoasFilaEspera1PorTempo = 0
        self.__somatorioPessoasFilaDadosPorTempo = 0
        self.__somatorioPessoasFilaEspera2PorTempo = 0
        
    def adicionarPacote(self, pacote):
        self.__pacotes.append(pacote)
        if pacote.getCanal() == -1:
            self.__pacotesDados.append(pacote)
        else: 
            self.__pacotesVoz.append(pacote)

    # Getters
    def getID(self):
        return self.__id

    def quantidadeDePacotes(self):
        return len(self.__pacotes)

    def getEsperancaDeN(self, tempoAtual):
        if tempoAtual == self.__tempoInicial:
            return 0
        return (self.__somatorioPessoasFilaVozPorTempo + self.__somatorioPessoasFilaDadosPorTempo)/(tempoAtual-self.__tempoInicial)

    def getEsperancaDeN1(self, tempoAtual):
        if tempoAtual == self.__tempoInicial:
            return 0
        return (self.__somatorioPessoasFilaVozPorTempo)/(tempoAtual-self.__tempoInicial)

    def getEsperancaDeN2(self, tempoAtual):
        if tempoAtual == self.__tempoInicial:
            return 0
        return (self.__somatorioPessoasFilaDadosPorTempo)/(tempoAtual-self.__tempoInicial)

    def getEsperancaDeNq1(self, tempoAtual):
        if tempoAtual == self.__tempoInicial:
            return 0
        return (self.__somatorioPessoasFilaEspera1PorTempo)/(tempoAtual-self.__tempoInicial)

    def getEsperancaDeNq2(self, tempoAtual):
        if tempoAtual == self.__tempoInicial:
            return 0
        return (self.__somatorioPessoasFilaEspera2PorTempo)/(tempoAtual-self.__tempoInicial)

    def getEsperancaDeT1(self):
        countT1 = 0
        somatorioT1 = 0.0
        for pacote in self.__pacotesVoz:
            if pacote.getTempoTerminoServico() != 0:
                countT1 += 1
                somatorioT1 += pacote.getTempoTotalSistema()
        if countT1 == 0:
            return -1
        return somatorioT1/len(self.__pacotesVoz)

    def getEsperancaDeT2(self):
        countT2 = 0
        somatorioT2 = 0.0
        for pacote in self.__pacotesDados:
            if pacote.getTempoTerminoServico() != 0:
                countT2 += 1
                somatorioT2 += pacote.getTempoTotalSistema()
        if countT2 == 0:
            return -1
        return somatorioT2/len(self.__pacotesDados)

    def getEsperancaDeW1(self):
        countW1 = 0
        somatorioW1 = 0.0
        for pacote in self.__pacotesVoz:
            if pacote.getTempoTerminoServico() != 0:
                countW1 += 1
                somatorioW1 += pacote.getTempoEsperaFila()
        if countW1 == 0:
            return -1
        return somatorioW1/len(self.__pacotesVoz)

    def getEsperancaDeW2(self):
        countW2 = 0
        somatorioW2 = 0.0
        for pacote in self.__pacotesDados:
            if pacote.getTempoTerminoServico() != 0:
                countW2 += 1
                somatorioW2 += pacote.getTempoEsperaFila()
        if countW2 == 0:
            return -1
        return somatorioW2/len(self.__pacotesDados)

    def getVarianciaDeW1(self):
        EW1 = self.getEsperancaDeW1()
        somatorioVW1 = 0.0
        for Pacote in self.__pacotesVoz:
            if Pacote.getTempoServico() != 0:
                somatorioVW1 += Pacote.getVarianciaTempoEsperaFila(EW1)
        return somatorioVW1/len(self.__pacotesVoz)

    def getVarianciaDeW2(self):
        EW2 = self.getEsperancaDeW2()
        somatorioVW2 = 0.0
        for Pacote in self.__pacotesDados:
            if Pacote.getTempoTerminoServico() != 0:
                somatorioVW2 += Pacote.getVarianciaTempoEsperaFila(EW2)
        return somatorioVW2/len(self.__pacotesDados)

    def inserirNumeroDePacotesPorTempoNaFilaVoz(self, numeroDePacotes, tempo):
        self.__pessoasFilaVozPorTempo.append(numeroDePacotes)
        self.__somatorioPessoasFilaVozPorTempo += tempo * numeroDePacotes

    def inserirNumeroDePacotesPorTempoNaFilaDados(self, numeroDePacotes, tempo):
        self.__pessoasFilaDadosPorTempo.append(numeroDePacotes)
        self.__somatorioPessoasFilaDadosPorTempo += tempo * numeroDePacotes

    def inserirNumeroDePacotesPorTempoNaFilaEspera1(self, numeroDePacotes, tempo):
        self.__pessoasFilaEspera1PorTempo.append(numeroDePacotes)
        self.__somatorioPessoasFilaEspera1PorTempo += tempo * numeroDePacotes

    def inserirNumeroDePacotesPorTempoNaFilaEspera2(self, numeroDePacotes, tempo):
        self.__pessoasFilaEspera2PorTempo.append(numeroDePacotes)
        self.__somatorioPessoasFilaEspera2PorTempo += tempo * numeroDePacotes


    def calcularEstatisticas(self, tempoAtual, view, intervaloDeConfianca, lambd):
        # Calculo de estatisticas da simulacao
        PacotesX1 = []
        PacotesT1 = []
        PacotesW1 = []
        PacotesT2 = []
        PacotesW2 = []
        somatorioX1 = 0.0
        somatorioT1 = 0.0
        somatorioW1 = 0.0
        somatorioT2 = 0.0
        somatorioW2 = 0.0
        divisorX1 = 0
        divisorT1 = 0
        divisorW1 = 0
        divisorT2 = 0
        divisorW2 = 0
        for Pacote in self.__pacotesDados:
            if Pacote.getTempoTerminoServico() != 0:
                PacotesT1.append(Pacote.getTempoTotalSistema())
                somatorioT1 += Pacote.getTempoTotalSistema()
                divisorT1 += 1
                
                PacotesW1.append(Pacote.getTempoEsperaFila())
                somatorioW1 += Pacote.getTempoEsperaFila()
                divisorW1 += 1

                PacotesX1.append(Pacote.getTempoTotalServico())
                somatorioX1 += Pacote.getTempoTotalServico()
                divisorX1 += 1

        for Pacote in self.__pacotesVoz:
            if Pacote.getTempoTerminoServico() != 0:
                PacotesT2.append(Pacote.getTempoTotalSistema())
                somatorioT2 += Pacote.getTempoTotalSistema()
                divisorT2 += 1
                
                PacotesW2.append(Pacote.getTempoEsperaFila())
                somatorioW2 += Pacote.getTempoEsperaFila()
                divisorW2 += 1

        EX1 = 0 if divisorX1 == 0 else somatorioX1/divisorX1
        ET1 = 0 if divisorT1 == 0 else somatorioT1/divisorT1
        EW1 = 0 if divisorW1 == 0 else somatorioW1/divisorW1
        ET2 = 0 if divisorT2 == 0 else somatorioT2/divisorT2
        EW2 = 0 if divisorW2 == 0 else somatorioW2/divisorW2

        PacotesVW1 = []
        PacotesVW2 = []
        somatorioVW1 = 0.0
        somatorioVW2 = 0.0
        for Pacote in self.__pacotesDados:
            if Pacote.getTempoTerminoServico() != 0:
                PacotesVW1.append(Pacote.getVarianciaTempoEsperaFila(EW1))
                somatorioVW1 += Pacote.getVarianciaTempoEsperaFila(EW1)
        for Pacote in self.__pacotesVoz:
            if Pacote.getTempoTerminoServico() != 0:
                PacotesVW2.append(Pacote.getVarianciaTempoEsperaFila(EW2))
                somatorioVW2 += Pacote.getVarianciaTempoEsperaFila(EW2)

        EVW1 = 0 if divisorW1 == 0 else somatorioVW1/divisorW1
        EVW2 = 0 if divisorW2 == 0 else somatorioVW2/divisorW2

        EN1  = self.__somatorioPessoasFilaVozPorTempo     / (tempoAtual - self.__tempoInicial)
        ENq1 = self.__somatorioPessoasFilaEspera1PorTempo / (tempoAtual - self.__tempoInicial)
        EN2  = self.__somatorioPessoasFilaDadosPorTempo   / (tempoAtual - self.__tempoInicial)
        ENq2 = self.__somatorioPessoasFilaEspera2PorTempo / (tempoAtual - self.__tempoInicial)

        if self.__id == -1:
            view.imprimir("Fase Transiente:")
        else:
            view.imprimir("\nFase Recorrente %d:" % (self.__id + 1))

        # Impressao dos resultados das estatisticas
        view.imprimir("p (Dados):      %f" % (EX1*lambd))
        view.imprimir("Fila e estavel: %s" % ("Sim" if EX1*lambd < 0.8314 else "Nao"))
        view.imprimir("E[X]  (Dados):  %f" % (EX1))
        view.imprimir("E[T]  (Dados):  %f" % (ET1))
        view.imprimir("E[W]  (Dados):  %f" % (EW1))
        view.imprimir("V(W)  (Dados):  %f" % (EVW1))
        view.imprimir("E[N]  (Dados):  %f" % (EN1))
        view.imprimir("E[Nq] (Dados):  %f" % (ENq1))
        view.imprimir("E[T]  (Voz):    %f" % (ET2))
        view.imprimir("E[W]  (Voz):    %f" % (EW2))
        view.imprimir("V(W]  (Voz):    %f" % (EVW2))
        view.imprimir("E[N]  (Voz):    %f" % (EN2))
        view.imprimir("E[Nq] (Voz):    %f" % (ENq2))

        calculadora = CalculadoraIC(intervaloDeConfianca)
        view.imprimir("IC E[X]  (Dados):  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras(PacotesX1)))
        view.imprimir("IC E[T]  (Dados):  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras(PacotesT1)))
        view.imprimir("IC E[W]  (Dados):  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras(PacotesW1)))
        view.imprimir("IC V(W)  (Dados):  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras(PacotesVW1)))
        view.imprimir("IC E[N]  (Dados):  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostrasComMedia(self.__pessoasFilaVozPorTempo, EN1)))
        view.imprimir("IC E[Nq] (Dados):  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostrasComMedia(self.__pessoasFilaEspera1PorTempo, ENq1)))
        view.imprimir("IC E[T]  (Voz):    %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras(PacotesT2)))
        view.imprimir("IC E[W]  (Voz):    %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras(PacotesW2)))
        view.imprimir("IC V(W)  (Voz):    %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras(PacotesVW2)))
        view.imprimir("IC E[N]  (Voz):    %f - %f" % (calculadora.intervaloDeConfiancaDeAmostrasComMedia(self.__pessoasFilaDadosPorTempo, EN2)))
        view.imprimir("IC E[Nq] (Voz):    %f - %f" % (calculadora.intervaloDeConfiancaDeAmostrasComMedia(self.__pessoasFilaEspera2PorTempo, ENq2)))