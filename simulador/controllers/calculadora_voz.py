
class CalculadoraVoz(object):

    @staticmethod
    def varianciaPorPeriodosDeChegadasDePacotesDeVoz(todosOsPacotes):
        valoresJ = []
        somatorioJ = []
        divisorJ = []

        ultimoIndiceVistoEmCanal = []
        numeroDeVezesQueCanalFoiPercorrido = []
        for indice in range(30):
            ultimoIndiceVistoEmCanal.append(0)
            numeroDeVezesQueCanalFoiPercorrido.append(0)

        for pacote in todosOsPacotes:
            if pacote.ehPacoteDeVoz():
                canalAtual = pacote.getCanal() # 0 a 29
                indice = pacote.getIndiceEmCanal() # 1+
                
                if ultimoIndiceVistoEmCanal[canalAtual] == indice:
                    numeroDeVezesQueCanalFoiPercorrido[canalAtual] += 1
                ultimoIndiceVistoEmCanal[canalAtual] = indice
                    
                if indice == 1:
                    chegada = pacote.getTempoChegadaFila()
                    if numeroDeVezesQueCanalFoiPercorrido[canalAtual] <= len(somatorioJ):
                        valoresJ.append([chegada])
                        somatorioJ.append(chegada)
                        divisorJ.append(1)
                    else:
                        valoresJ[numeroDeVezesQueCanalFoiPercorrido[canalAtual]].append(chegada)
                        somatorioJ[numeroDeVezesQueCanalFoiPercorrido[canalAtual]] += chegada
                        divisorJ[numeroDeVezesQueCanalFoiPercorrido[canalAtual]] += 1

        mediaIntervaloDeChegadaPorPeriodo = []
        for indice in range(len(somatorioJ)):
            mediaIntervaloDeChegadaPorPeriodo.append(somatorioJ[indice]/divisorJ[indice] if divisorJ[indice] != 0 else 0)

        varianciaPorPeriodos = [] # Delta J
        for indice in range(len(somatorioJ)):
            varianciaPorPeriodo = 0
            for canal in range(len(valoresJ[indice])):
                varianciaPorCanal = (valoresJ[indice][canal] - mediaIntervaloDeChegadaPorPeriodo[indice]) ** 2
                varianciaPorPeriodo += varianciaPorCanal
            if len(valoresJ[indice]) > 0:
                varianciaPorPeriodo /= len(valoresJ[indice])
            varianciaPorPeriodos.append(varianciaPorPeriodo)

        return varianciaPorPeriodos

    @staticmethod
    def esperancaEVarianciaDaVarianciaDeChegadasDePacotesDeVoz(fases):
        esperancaDaVarianciaPorFase = [] # E[DeltaK]
        for fase in fases:
            deltaJ = 0
            varianciaPorPeriodos = fase.varianciaPorPeriodosDeChegadasDePacotesDeVoz() # Delta J
            for varianciaPorPeriodo in varianciaPorPeriodos:
                deltaJ += varianciaPorPeriodo
            deltaJ /= len(varianciaPorPeriodos)
            esperancaDaVarianciaPorFase.append(deltaJ)
        
        esperancaDaVarianciaTotal = 0 # E[Delta]
        for esperancaDaVariancia in esperancaDaVarianciaPorFase:
            esperancaDaVarianciaTotal += esperancaDaVariancia
        esperancaDaVarianciaTotal /= len(esperancaDaVarianciaPorFase)

        varianciaDaVarianciaPorFase = [] # V(DeltaK)
        for fase in fases:
            vdeltaJ = 0
            varianciaPorPeriodos = fase.varianciaPorPeriodosDeChegadasDePacotesDeVoz() # Delta J
            for varianciaPorPeriodo in varianciaPorPeriodos:
                vdeltaJ += (varianciaPorPeriodo - esperancaDaVarianciaPorFase[fase.getID()]) ** 2
            vdeltaJ /= (len(varianciaPorPeriodos) - 1)
            varianciaDaVarianciaPorFase.append(vdeltaJ)

        varianciaDaVarianciaTotal = 0 # V(Delta)
        for varianciaDaVariancia in varianciaDaVarianciaPorFase:
            varianciaDaVarianciaTotal += varianciaDaVariancia
        varianciaDaVarianciaTotal /= len(varianciaDaVarianciaPorFase)

        return esperancaDaVarianciaPorFase, esperancaDaVarianciaTotal, varianciaDaVarianciaPorFase, varianciaDaVarianciaTotal
