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
                somatorioT1 += pacote.getTempoTotalFila()
        if countT1 == 0:
            return -1
        return somatorioT1/len(self.__pacotesVoz)

    def getEsperancaDeT2(self):
        countT2 = 0
        somatorioT2 = 0.0
        for pacote in self.__pacotesDados:
            if pacote.getTempoTerminoServico() != 0:
                countT2 += 1
                somatorioT2 += pacote.getTempoTotalFila()
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


    def calcularEstatisticas(self, tempoAtual, view, intervaloDeConfianca):
        # Calculo de estatisticas da simulacao
        PacotesT1 = []
        PacotesW1 = []
        PacotesT2 = []
        PacotesW2 = []
        somatorioT1 = 0.0
        somatorioW1 = 0.0
        somatorioT2 = 0.0
        somatorioW2 = 0.0
        for Pacote in self.__pacotes:
            if Pacote.getTempoServico() != 0:
                PacotesW1.append(Pacote.getTempoEsperaFila())
                somatorioW1 += Pacote.getTempoEsperaFila()
            
            if Pacote.getTempoChegadaFila() != 0:
                PacotesT1.append(Pacote.getTempoTotalFila())
                somatorioT1 += Pacote.getTempoTotalFila()
            
            if Pacote.getTempoTerminoServico() != 0:
                PacotesT2.append(Pacote.getTempoTotalFila())
                somatorioT2 += Pacote.getTempoTotalFila()
                
                PacotesW2.append(Pacote.getTempoEsperaFila())
                somatorioW2 += Pacote.getTempoEsperaFila()

        ET1 = somatorioT1/len(self.__pacotes)
        EW1 = somatorioW1/len(self.__pacotes)
        ET2 = somatorioT2/len(self.__pacotes)
        EW2 = somatorioW2/len(self.__pacotes)

        PacotesVW1 = []
        PacotesVW2 = []
        somatorioVW1 = 0.0
        somatorioVW2 = 0.0
        for Pacote in self.__pacotes:
            if Pacote.getTempoServico() != 0:
                PacotesVW1.append(Pacote.getVarianciaTempoEsperaFila(EW1))
                somatorioVW1 += Pacote.getVarianciaTempoEsperaFila(EW1)
            
            if Pacote.getTempoTerminoServico() != 0:
                PacotesVW2.append(Pacote.getVarianciaTempoEsperaFila(EW2))
                somatorioVW2 += Pacote.getVarianciaTempoEsperaFila(EW2)
        EVW1 = somatorioVW1/len(self.__pacotes)
        EVW2 = somatorioVW2/len(self.__pacotes)

        EN1  = self.__somatorioPessoasFilaVozPorTempo       / (tempoAtual - self.__tempoInicial)
        ENq1 = self.__somatorioPessoasFilaEspera1PorTempo / (tempoAtual - self.__tempoInicial)
        EN2  = self.__somatorioPessoasFilaDadosPorTempo       / (tempoAtual - self.__tempoInicial)
        ENq2 = self.__somatorioPessoasFilaEspera2PorTempo / (tempoAtual - self.__tempoInicial)

        if self.__id == -1:
            view.imprimir("Fase Transiente:")
        else:
            view.imprimir("\nFase Recorrente %d:" % (self.__id + 1))

        # Impressao dos resultados das estatisticas
        view.imprimir("E[T1]:  %f" % (ET1))
        view.imprimir("E[W1]:  %f" % (EW1))
        view.imprimir("V(W1):  %f" % (EVW1))
        view.imprimir("E[N1]:  %f" % (EN1))
        view.imprimir("E[Nq1]: %f" % (ENq1))
        view.imprimir("E[T2]:  %f" % (ET2))
        view.imprimir("E[W2]:  %f" % (EW2))
        view.imprimir("V(W2):  %f" % (EVW2))
        view.imprimir("E[N2]:  %f" % (EN2))
        view.imprimir("E[Nq2]: %f" % (ENq2))

        calculadora = CalculadoraIC(intervaloDeConfianca)
        view.imprimir("IC E[T1]:  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras(PacotesT1)))
        view.imprimir("IC E[W1]:  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras(PacotesW1)))
        view.imprimir("IC V(W1):  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras(PacotesVW1)))
        view.imprimir("IC E[N1]:  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostrasComMedia(self.__pessoasFilaVozPorTempo, EN1)))
        view.imprimir("IC E[Nq1]: %f - %f" % (calculadora.intervaloDeConfiancaDeAmostrasComMedia(self.__pessoasFilaEspera1PorTempo, ENq1)))
        view.imprimir("IC E[T2]:  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras(PacotesT2)))
        view.imprimir("IC E[W2]:  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras(PacotesW2)))
        view.imprimir("IC V(W2):  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostras(PacotesVW2)))
        view.imprimir("IC E[N2]:  %f - %f" % (calculadora.intervaloDeConfiancaDeAmostrasComMedia(self.__pessoasFilaDadosPorTempo, EN2)))
        view.imprimir("IC E[Nq2]: %f - %f" % (calculadora.intervaloDeConfiancaDeAmostrasComMedia(self.__pessoasFilaEspera2PorTempo, ENq2)))