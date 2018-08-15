import random
import numpy
import math

""" O Agendador sera responsavel por agendar chegadas e servicos
    de acordo com as taxas lambda e mi, respectivamente."""

class Agendador(object):

    def __init__(self):
        self.__testeDeCorretudeChegadaVoz   = False
        self.__testeDeCorretudeChegadaDados = False
        self.__testeDeCorretudePacotesVoz   = False
        self.__testeDeCorretudeServicoDados = False

        self.__desabilitarVoz = False
        self.__desabilitarDados = False

        self.__tamanhoPacoteVoz = 512.0 # 512 bits = 64 bytes
        self.__taxaDeTransmissao = (2.0*1000*1000)/1000 ## 2 Megabits por segundo (em ms)
        
        self.__pacoteFilaVozIndice = []
        self.__pacoteFilaVozTotal = []
        self.__pacoteFilaVozTempoDeAguardo = []
        self.__pacoteIndiceServicoDeCanal = []
        for indice in xrange(30):
            self.__pacoteFilaVozIndice.append(0)
            self.__pacoteFilaVozTotal.append(0)
            self.__pacoteFilaVozTempoDeAguardo.append(0)
            self.__pacoteIndiceServicoDeCanal.append(-1)

    
    def valorDeLComProbabilidade(self, prob):
        newProb = prob

        # 64
        if newProb < (0.3 + 3.0/(10*1436)): # Delta de Jirac e Funcao Degrau
            return 64
        newProb -= (0.3 + 3.0/(10*1436))

        # Os 447 numeros entre 64 e 512
        if newProb < 447*(3.0/(10*1436)): # Delta de Jirac
            return 65 + int(newProb / (3.0/(10*1436)))
        newProb -= 447*(3.0/(10*1436))

        # 512
        if newProb < (0.1 + 3.0/(10*1436)): # Delta de Jirac e Funcao Degrau
            return 512
        newProb -= (0.1 + 3.0/(10*1436))

        # Os 987 numeros entre 512 e 1500
        if newProb < 987*(3.0/(10*1436)): # Delta de Jirac
            return 513 + int(newProb / (3.0/(10*1436)))

        # 1500
        # Seria Delta de Jirac e Funcao Degrau
        # Mas nao eh preciso calcular sendo que eh o resto da probabilidade
        return 1500

    def setTesteDeCorretude(self, testeDeCorretudeChegadaVoz, testeDeCorretudeChegadaDados, testeDeCorretudePacotesVoz, testeDeCorretudeServicoDados):
        self.__testeDeCorretudeChegadaVoz   = testeDeCorretudeChegadaVoz
        self.__testeDeCorretudeChegadaDados = testeDeCorretudeChegadaDados
        self.__testeDeCorretudePacotesVoz   = testeDeCorretudePacotesVoz
        self.__testeDeCorretudeServicoDados = testeDeCorretudeServicoDados

    def setDesabilitarVoz(self, desabilitarVoz):
        self.__desabilitarVoz = desabilitarVoz

    def setDesabilitarDados(self, desabilitarDados):
        self.__desabilitarDados = desabilitarDados

    def configurarSemente(self, seed):
        print "Semente: %d" % (seed)
        random.seed(seed)
        numpy.random.RandomState(seed=seed)

    def deveAgendarChegadaFilaVoz(self, canal, servico, filaVoz): 
        total  = self.__pacoteFilaVozTotal[canal]
        indice = self.__pacoteFilaVozIndice[canal]
        
        if indice == total and total != 0 and filaVoz.numeroDePacotesNaFilaDeCanal(canal) > 1:
            return False
        
        return True

    def deveAgendarChegadaServicoVoz(self, canal, filaVoz): 
        subindice = self.__pacoteFilaVozIndice[canal]
        subtotal  = self.__pacoteFilaVozTotal[canal]
        
        if subindice == subtotal and filaVoz.numeroDePacotesNaFilaDeCanal(canal) == 1:
            return True
        
        return False

    def agendarChegadaFilaVoz(self, canal): 
        if self.__desabilitarVoz == True:
            return None, None, None

        espera_previa = 0
        
        indice = self.__pacoteFilaVozIndice[canal]
        total  = self.__pacoteFilaVozTotal[canal]
        if indice == total: # Inicio de uma nova remessa de pacotes de voz
            espera_previa = self.__pacoteFilaVozTempoDeAguardo[canal]
            self.__pacoteFilaVozTempoDeAguardo[canal] = 0
            indice = 0

        if indice == 0:
            self.__pacoteFilaVozIndice[canal] = 1
            self.__pacoteIndiceServicoDeCanal[canal] += 1
            
            quantidadePacotes = 0
            if self.__testeDeCorretudePacotesVoz == True:
                quantidadePacotes = int(round(random.expovariate(1.0/22.0)))
            else:
                quantidadePacotes = int(round(numpy.random.geometric(p=1.0/22.0)))

            tempoDeEspera = 0
            if self.__testeDeCorretudeChegadaVoz == True:
                tempoDeEspera = espera_previa + numpy.random.geometric(p=1.0/650)
            else:
                tempoDeEspera = espera_previa + random.expovariate(1.0/650)
            
            # Definindo a quantidade de pacotes que virao na nova remessa
            self.__pacoteFilaVozTotal[canal] = quantidadePacotes
            
            # Calculando o tempo de silencio necessario para a nova remessa comecar
            return self.__pacoteIndiceServicoDeCanal[canal], self.__pacoteFilaVozIndice[canal], tempoDeEspera

        self.__pacoteFilaVozIndice[canal] += 1
        return self.__pacoteIndiceServicoDeCanal[canal], self.__pacoteFilaVozIndice[canal], 16

    def agendarChegadaFilaDados(self, lambd):
        if self.__desabilitarDados == True:
            return None

        if self.__testeDeCorretudeChegadaDados == True:
            return numpy.random.geometric(p=lambd/1000)

        return random.expovariate(lambd/1000)

    def agendarTempoDeServicoFilaVoz(self, canal, servico, filaVoz):
        tempo = self.__tamanhoPacoteVoz/self.__taxaDeTransmissao # 0.256 ms

        indice = self.__pacoteFilaVozIndice[canal]
        total  = self.__pacoteFilaVozTotal[canal]

        if indice == total and filaVoz.numeroDePacotesNaFilaDeCanal(canal) == 1:
            if self.__pacoteFilaVozTempoDeAguardo[canal] == 0:
                self.__pacoteFilaVozTempoDeAguardo[canal] = tempo + 16

        return tempo

    def agendarTempoDeServicoFilaDados(self):
        if self.__testeDeCorretudeServicoDados == True:
            return (755*8.0)/self.__taxaDeTransmissao 

        Lbytes = self.valorDeLComProbabilidade(random.random())
        return (Lbytes*8.0)/self.__taxaDeTransmissao # Esperanca: 3.0192 ms