from ..controllers.calculadora_voz import *
from ..controllers.calculadora_ic import *
from ..views.view import *

class Fase(object):
    def __init__(self, id, tempoInicial):
        self.id = id
        self.pacotes = []
        self.__pacotesDados = []
        self.__pacotesVoz = []
        self.__tempoInicial = tempoInicial
        self.quantidadeDeEventosVoz = 0
        self.quantidadeDeEventosDados = 0

        ### Atributos usados para calculos estatisticos
        self.__somatorioPacotesFilaVozPorTempo = 0
        self.__somatorioPacotesFilaEsperaVozPorTempo = 0
        self.__somatorioPacotesFilaDadosPorTempo = 0
        self.__somatorioPacotesFilaEsperaDadosPorTempo = 0

        self.__varianciaPorPeriodosDeChegadasDePacotesDeVoz = [] # Delta J

        self.EX1 = 0
        self.EX2 = 0
        
        self.ET1 = 0
        self.EW1 = 0
        self.EVW1 = 0
        self.EN1  = 0
        self.ENq1 = 0
        
        self.ET2 = 0
        self.EW2 = 0
        self.EVW2 = 0
        self.EN2  = 0
        self.ENq2 = 0
        
    def adicionarPacote(self, pacote):
        self.pacotes.append(pacote)
        if pacote.canal != -1:
            self.__pacotesVoz.append(pacote)
        else: 
            self.__pacotesDados.append(pacote)

    # Getters
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
            if pacote.tempoTerminoServico != 0:
                countT1 += 1
                somatorioT1 += pacote.getTempoTotalSistema()
        if countT1 == 0:
            return -1
        return somatorioT1/countT1 if countT1 > 0 else 0

    def getEsperancaDeTDados(self):
        countT2 = 0
        somatorioT2 = 0.0
        for pacote in self.__pacotesDados:
            if pacote.tempoTerminoServico != 0:
                countT2 += 1
                somatorioT2 += pacote.getTempoTotalSistema()
        if countT2 == 0:
            return -1
        return somatorioT2/countT2 if countT2 > 0 else 0

    def getEsperancaDeX1(self):
        countX1 = 0
        somatorioX1 = 0.0
        for pacote in self.__pacotesDados:
            if pacote.tempoTerminoServico != 0:
                countX1 += 1
                somatorioX1 += pacote.getTempoTotalServico()
        if countX1 == 0:
            return -1
        return somatorioX1/countX1 if countX1 > 0 else 0

    def getEsperancaDeWVoz(self):
        countW1 = 0
        somatorioW1 = 0.0
        for pacote in self.__pacotesVoz:
            if pacote.tempoChegadaServico != 0:
                countW1 += 1
                somatorioW1 += pacote.getTempoEsperaFila()
        if countW1 == 0:
            return -1
        return somatorioW1/countW1 if countW1 > 0 else 0

    def getEsperancaDeWDados(self):
        countW2 = 0
        somatorioW2 = 0.0
        for pacote in self.__pacotesDados:
            if pacote.tempoChegadaServico != 0:
                countW2 += 1
                somatorioW2 += pacote.getTempoEsperaFila()
        if countW2 == 0:
            return -1
        return somatorioW2/countW2 if countW2 > 0 else 0

    def getVarianciaDeW1(self):
        countVW1 = 0
        EW1 = self.getEsperancaDeWVoz()
        somatorioVW1 = 0.0
        for pacote in self.__pacotesVoz:
            if pacote.tempoChegadaServico != 0:
                countVW1 += 1
                somatorioVW1 += pacote.getVarianciaTempoEsperaFila(EW1)
        return somatorioVW1/countVW1 if countVW1 > 0 else 0

    def getVarianciaDeW2(self):
        countVW2 = 0
        EW2 = self.getEsperancaDeWDados()
        somatorioVW2 = 0.0
        for pacote in self.__pacotesDados:
            if pacote.tempoChegadaServico != 0:
                countVW2 += 1
                somatorioVW2 += pacote.getVarianciaTempoEsperaFila(EW2)
        return somatorioVW2/countVW2 if countVW2 > 0 else 0

    def inserirNumeroDePacotesPorTempoNaFilaVoz(self, numeroDePacotes, tempo):
        self.__somatorioPacotesFilaVozPorTempo += tempo * numeroDePacotes

    def inserirNumeroDePacotesPorTempoNaFilaDados(self, numeroDePacotes, tempo):
        self.__somatorioPacotesFilaDadosPorTempo += tempo * numeroDePacotes

    def inserirNumeroDePacotesPorTempoNaFilaEsperaVoz(self, numeroDePacotes, tempo):
        self.__somatorioPacotesFilaEsperaVozPorTempo += tempo * numeroDePacotes

    def inserirNumeroDePacotesPorTempoNaFilaEsperaDados(self, numeroDePacotes, tempo):
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
            if pacote.tempoTerminoServico != 0:
                somatorioT1 += pacote.getTempoTotalSistema()
                divisorT1 += 1
                
                somatorioX1 += pacote.getTempoTotalServico()
                divisorX1 += 1
        
            if pacote.tempoChegadaServico != 0:
                somatorioW1 += pacote.getTempoEsperaFila()
                divisorW1 += 1

        self.ET1 = None if divisorT1 == 0 else somatorioT1/divisorT1
        self.EW1 = None if divisorW1 == 0 else somatorioW1/divisorW1
        self.EX1 = None if divisorX1 == 0 else somatorioX1/divisorX1
        

        somatorioT2 = 0.0
        somatorioW2 = 0.0
        somatorioX2 = 0.0
        divisorT2 = 0
        divisorW2 = 0
        divisorX2 = 0
        
        for pacote in self.__pacotesVoz:
            if pacote.tempoTerminoServico != 0:
                somatorioT2 += pacote.getTempoTotalSistema()
                divisorT2 += 1

                somatorioX2 += pacote.getTempoTotalServico()
                divisorX2 += 1

            if pacote.tempoChegadaServico != 0:
                somatorioW2 += pacote.getTempoEsperaFila()
                divisorW2 += 1

        self.ET2 = None if divisorT2 == 0 else somatorioT2/divisorT2
        self.EW2 = None if divisorW2 == 0 else somatorioW2/divisorW2
        self.EX2 = None if divisorX2 == 0 else somatorioX2/divisorX2


        somatorioVW1 = 0.0
        for pacote in self.__pacotesDados:
            if pacote.tempoChegadaServico != 0:
                somatorioVW1 += pacote.getVarianciaTempoEsperaFila(self.EW1)
        self.EVW1 = None if divisorW1 == 0 else somatorioVW1/divisorW1

        somatorioVW2 = 0.0
        for pacote in self.__pacotesVoz:
            if pacote.tempoChegadaServico != 0:
                somatorioVW2 += pacote.getVarianciaTempoEsperaFila(self.EW2)
        self.EVW2 = None if divisorW2 == 0 else somatorioVW2/divisorW2


        self.EN1  = self.__somatorioPacotesFilaDadosPorTempo       / (tempoAtual - self.__tempoInicial)
        self.ENq1 = self.__somatorioPacotesFilaEsperaDadosPorTempo / (tempoAtual - self.__tempoInicial)
        self.EN2  = self.__somatorioPacotesFilaVozPorTempo         / (tempoAtual - self.__tempoInicial)
        self.ENq2 = self.__somatorioPacotesFilaEsperaVozPorTempo   / (tempoAtual - self.__tempoInicial)
        
        self.__varianciaPorPeriodosDeChegadasDePacotesDeVoz = CalculadoraVoz.varianciaPorPeriodosDeChegadasDePacotesDeVoz(self.__pacotesVoz)


        self.pacotes = []
        self.__pacotesDados = []
        self.__pacotesVoz = []
