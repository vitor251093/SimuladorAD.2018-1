from ..controllers.calculadora_voz import *
from ..controllers.calculadora_ic import *
from ..views.view import *

class Fase(object):
    def __init__(self, id, tempoInicial):
        self.__id = id
        self.__pacotes = []
        self.__pacotesDados = []
        self.__pacotesVoz = []
        self.__tempoInicial = tempoInicial
        self.__quantidadeDeEventosVoz = 0
        self.__quantidadeDeEventosDados = 0

        ### Atributos usados para calculos estatisticos
        self.__pacotesFilaVozPorTempo = []
        self.__pacotesFilaEsperaVozPorTempo = []
        self.__pacotesFilaDadosPorTempo = []
        self.__pacotesFilaEsperaDadosPorTempo = []
        self.__somatorioPacotesFilaVozPorTempo = 0
        self.__somatorioPacotesFilaEsperaVozPorTempo = 0
        self.__somatorioPacotesFilaDadosPorTempo = 0
        self.__somatorioPacotesFilaEsperaDadosPorTempo = 0

        self.__varianciaPorPeriodosDeChegadasDePacotesDeVoz = [] # Delta J

        self.__EX1 = 0
        self.__EX2 = 0
        
        self.__ET1 = 0
        self.__EW1 = 0
        self.__EVW1 = 0
        self.__EN1  = 0
        self.__ENq1 = 0
        
        self.__ET2 = 0
        self.__EW2 = 0
        self.__EVW2 = 0
        self.__EN2  = 0
        self.__ENq2 = 0

    def EX1(self):
        return self.__EX1
    def EX2(self):
        return self.__EX2
    def ET1(self):
        return self.__ET1
    def EW1(self):
        return self.__EW1
    def EVW1(self):
        return self.__EVW1
    def EN1(self):
        return self.__EN1
    def ENq1(self):
        return self.__ENq1
    def ET2(self):
        return self.__ET2
    def EW2(self):
        return self.__EW2
    def EVW2(self):
        return self.__EVW2
    def EN2(self):
        return self.__EN2
    def ENq2(self):
        return self.__ENq2
        
    def adicionarPacote(self, pacote):
        self.__pacotes.append(pacote)
        if pacote.ehPacoteDeVoz():
            self.__pacotesVoz.append(pacote)
        else: 
            self.__pacotesDados.append(pacote)

    # Getters
    def getID(self):
        return self.__id

    def quantidadeDePacotes(self):
        return len(self.__pacotes)

    def adicionarEventoVozAContagem(self):
        self.__quantidadeDeEventosVoz += 1

    def quantidadeDeEventosVoz(self):
        return self.__quantidadeDeEventosVoz

    def adicionarEventoDadosAContagem(self):
        self.__quantidadeDeEventosDados += 1

    def quantidadeDeEventosDados(self):
        return self.__quantidadeDeEventosDados

    def getEsperancaDeN(self, tempoAtual):
        if tempoAtual == self.__tempoInicial:
            return 0
        return (self.__somatorioPacotesFilaVozPorTempo + self.__somatorioPacotesFilaDadosPorTempo)/(tempoAtual-self.__tempoInicial)

    def getEsperancaDeN1(self, tempoAtual):
        if tempoAtual == self.__tempoInicial:
            return 0
        return (self.__somatorioPacotesFilaVozPorTempo)/(tempoAtual-self.__tempoInicial)

    def getEsperancaDeN2(self, tempoAtual):
        if tempoAtual == self.__tempoInicial:
            return 0
        return (self.__somatorioPacotesFilaDadosPorTempo)/(tempoAtual-self.__tempoInicial)

    def getEsperancaDeNq1(self, tempoAtual):
        if tempoAtual == self.__tempoInicial:
            return 0
        return (self.__somatorioPacotesFilaEsperaVozPorTempo)/(tempoAtual-self.__tempoInicial)

    def getEsperancaDeNq2(self, tempoAtual):
        if tempoAtual == self.__tempoInicial:
            return 0
        return (self.__somatorioPacotesFilaEsperaDadosPorTempo)/(tempoAtual-self.__tempoInicial)

    def getEsperancaDeTVoz(self):
        countT1 = 0
        somatorioT1 = 0.0
        for pacote in self.__pacotesVoz:
            if pacote.getTempoTerminoServico() != 0:
                countT1 += 1
                somatorioT1 += pacote.getTempoTotalSistema()
        if countT1 == 0:
            return -1
        return somatorioT1/countT1 if countT1 > 0 else 0

    def getEsperancaDeTDados(self):
        countT2 = 0
        somatorioT2 = 0.0
        for pacote in self.__pacotesDados:
            if pacote.getTempoTerminoServico() != 0:
                countT2 += 1
                somatorioT2 += pacote.getTempoTotalSistema()
        if countT2 == 0:
            return -1
        return somatorioT2/countT2 if countT2 > 0 else 0

    def getEsperancaDeWVoz(self):
        countW1 = 0
        somatorioW1 = 0.0
        for pacote in self.__pacotesVoz:
            if pacote.getTempoChegadaServico() != 0:
                countW1 += 1
                somatorioW1 += pacote.getTempoEsperaFila()
        if countW1 == 0:
            return -1
        return somatorioW1/len(self.__pacotesVoz) if len(self.__pacotesVoz) > 0 else 0

    def getEsperancaDeWDados(self):
        countW2 = 0
        somatorioW2 = 0.0
        for pacote in self.__pacotesDados:
            if pacote.getTempoTerminoServico() != 0:
                countW2 += 1
                somatorioW2 += pacote.getTempoEsperaFila()
        if countW2 == 0:
            return -1
        return somatorioW2/len(self.__pacotesDados) if len(self.__pacotesDados) > 0 else 0

    def getVarianciaDeW1(self):
        EW1 = self.getEsperancaDeWVoz()
        somatorioVW1 = 0.0
        for pacote in self.__pacotesVoz:
            if pacote.getTempoServico() != 0:
                somatorioVW1 += pacote.getVarianciaTempoEsperaFila(EW1)
        return somatorioVW1/len(self.__pacotesVoz) if len(self.__pacotesVoz) > 0 else 0

    def getVarianciaDeW2(self):
        EW2 = self.getEsperancaDeWDados()
        somatorioVW2 = 0.0
        for pacote in self.__pacotesDados:
            if pacote.getTempoTerminoServico() != 0:
                somatorioVW2 += pacote.getVarianciaTempoEsperaFila(EW2)
        return somatorioVW2/len(self.__pacotesDados) if len(self.__pacotesDados) > 0 else 0

    def inserirNumeroDePacotesPorTempoNaFilaVoz(self, numeroDePacotes, tempo):
        self.__pacotesFilaVozPorTempo.append(numeroDePacotes)
        self.__somatorioPacotesFilaVozPorTempo += tempo * numeroDePacotes

    def inserirNumeroDePacotesPorTempoNaFilaDados(self, numeroDePacotes, tempo):
        self.__pacotesFilaDadosPorTempo.append(numeroDePacotes)
        self.__somatorioPacotesFilaDadosPorTempo += tempo * numeroDePacotes

    def inserirNumeroDePacotesPorTempoNaFilaEsperaVoz(self, numeroDePacotes, tempo):
        self.__pacotesFilaEsperaVozPorTempo.append(numeroDePacotes)
        self.__somatorioPacotesFilaEsperaVozPorTempo += tempo * numeroDePacotes

    def inserirNumeroDePacotesPorTempoNaFilaEsperaDados(self, numeroDePacotes, tempo):
        self.__pacotesFilaEsperaDadosPorTempo.append(numeroDePacotes)
        self.__somatorioPacotesFilaEsperaDadosPorTempo += tempo * numeroDePacotes


    def varianciaPorPeriodosDeChegadasDePacotesDeVoz(self):
        return self.__varianciaPorPeriodosDeChegadasDePacotesDeVoz

    def calcularEstatisticas(self, tempoAtual, view, intervaloDeConfianca, lambd):
        # Calculo de estatisticas da simulacao
        # 1: Dados
        # 2: Voz

        somatorioT1 = 0.0
        somatorioW1 = 0.0
        somatorioX1 = 0.0
        divisorT1 = 0
        divisorW1 = 0
        divisorX1 = 0
        
        for pacote in self.__pacotesDados:
            if pacote.getTempoTerminoServico() != 0:
                somatorioT1 += pacote.getTempoTotalSistema()
                divisorT1 += 1
                
                somatorioX1 += pacote.getTempoTotalServico()
                divisorX1 += 1
        
                somatorioW1 += pacote.getTempoEsperaFila()
                divisorW1 += 1

        self.__ET1 = None if divisorT1 == 0 else somatorioT1/divisorT1
        self.__EW1 = None if divisorW1 == 0 else somatorioW1/divisorW1
        self.__EX1 = None if divisorX1 == 0 else somatorioX1/divisorX1
        

        somatorioT2 = 0.0
        somatorioW2 = 0.0
        somatorioX2 = 0.0
        divisorT2 = 0
        divisorW2 = 0
        divisorX2 = 0
        
        for pacote in self.__pacotesVoz:
            if pacote.getTempoTerminoServico() != 0:
                somatorioT2 += pacote.getTempoTotalSistema()
                divisorT2 += 1

                somatorioX2 += pacote.getTempoTotalServico()
                divisorX2 += 1

                somatorioW2 += pacote.getTempoEsperaFila()
                divisorW2 += 1

        self.__ET2 = None if divisorT2 == 0 else somatorioT2/divisorT2
        self.__EW2 = None if divisorW2 == 0 else somatorioW2/divisorW2
        self.__EX2 = None if divisorX2 == 0 else somatorioX2/divisorX2


        somatorioVW1 = 0.0
        for pacote in self.__pacotesDados:
            if pacote.getTempoTerminoServico() != 0:
                somatorioVW1 += pacote.getVarianciaTempoEsperaFila(self.__EW1)
        self.__EVW1 = None if divisorW1 == 0 else somatorioVW1/divisorW1

        somatorioVW2 = 0.0
        for pacote in self.__pacotesVoz:
            if pacote.getTempoTerminoServico() != 0:
                somatorioVW2 += pacote.getVarianciaTempoEsperaFila(self.__EW2)
        self.__EVW2 = None if divisorW2 == 0 else somatorioVW2/divisorW2


        self.__EN1  = self.__somatorioPacotesFilaDadosPorTempo       / (tempoAtual - self.__tempoInicial)
        self.__ENq1 = self.__somatorioPacotesFilaEsperaDadosPorTempo / (tempoAtual - self.__tempoInicial)
        self.__EN2  = self.__somatorioPacotesFilaVozPorTempo         / (tempoAtual - self.__tempoInicial)
        self.__ENq2 = self.__somatorioPacotesFilaEsperaVozPorTempo   / (tempoAtual - self.__tempoInicial)
        
        self.__varianciaPorPeriodosDeChegadasDePacotesDeVoz = CalculadoraVoz.varianciaPorPeriodosDeChegadasDePacotesDeVoz(self.__pacotesVoz)


        self.__pacotes = []
        self.__pacotesDados = []
        self.__pacotesVoz = []
        
        self.__pacotesFilaVozPorTempo = []
        self.__pacotesFilaEsperaVozPorTempo = []
        self.__pacotesFilaDadosPorTempo = []
        self.__pacotesFilaEsperaDadosPorTempo = []