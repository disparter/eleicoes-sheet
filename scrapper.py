import dataclasses
import datetime
import json
import os
import re
import unidecode
from dataclasses import dataclass

from dataclasses_json import dataclass_json
from time import sleep
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select


@dataclass_json
@dataclass
class PesquisaEleitoralCandidato:
    cargo: str
    ambito: str
    candidato_nome: str
    partido: str
    valor_referencia: float
    data_publicacao: datetime.datetime
    instituto_nome: str
    resultado_tse: float
    margem_erro: int
    diferenca: float
    acertou_posicao: bool
    acertou_margem: bool


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


class Scrapper:
    select_cargos = None
    select_ambitos = None
    select_institutos = None
    cargos = []
    ambitos = []
    institutos_pesquisa = []
    resultados = []
    cargo = None
    instituto = None
    ambito = None
    driver = None

    def start(self):
        try:
            self.load_context()
            for cargo in self.cargos:
                self.cargo = cargo
                for ambito in self.ambitos:
                    self.ambito = ambito
                    for instituto in self.institutos_pesquisa:
                        self.instituto = instituto
                        try:
                            Select(self.select_cargos).select_by_value(cargo)
                            Select(self.select_ambitos).select_by_value(ambito)
                            Select(self.select_institutos).select_by_value(instituto)
                            sleep(1)
                            print(f"Buscando registro para {instituto} e {cargo} no {ambito}")
                            self.criar_registro_pesquisa(instituto, self.obter_margem_erro())
                            print(f"Obtido registro para {instituto} e {cargo} no {ambito}")
                        except Exception as e:
                            print(f"Falhou em criar registro para {instituto} e {cargo} no {ambito}")
                            self.load_context()

            resultados_compilados = PesquisaEleitoralCandidato.schema().dumps(self.resultados, many=True)
            with open(f'data.json', 'w') as f:
                f.write(resultados_compilados)
                print(f'data.json foi criado')
        finally:
            self.driver.quit()

    def load_context(self):
        options = Options()
        options.headless = True
        load_dotenv()
        webdriver_path = os.getenv('WEBDRIVER_PATH')
        self.driver = webdriver.Chrome(options=options, executable_path=webdriver_path)
        base_url = f'https://www.poder360.com.br/agregador-de-pesquisas/'
        self.driver.get(base_url)
        sleep(0.5)
        selects = self.driver.find_elements(By.TAG_NAME, "select")
        self.select_cargos = selects[0]
        self.cargos = [x.get_attribute('value') for x in self.select_cargos.find_elements(By.TAG_NAME, "option")]
        self.select_ambitos = selects[1]
        self.ambitos = [x.get_attribute('value') for x in self.select_ambitos.find_elements(By.TAG_NAME, "option")][1:]
        self.select_institutos = self.driver.find_elements(By.TAG_NAME, "select")[7]
        self.institutos_pesquisa = [x.get_attribute('value') for x in
                                    self.select_institutos.find_elements(By.TAG_NAME, "option")][1:]

    def obter_data(self, cabecalho):
        return datetime.datetime.strptime(cabecalho.split(" ")[2], "%d/%m/%Y")

    def obter_valor_cargo(self):
        if self.cargo == 'Governador':
            return 3
        if self.cargo == 'Senador':
            return 5
        raise NotImplementedError('opcao apenas para governador e senador por enquanto')

    def obter_resultado_tse(self, nome_candidato):
        root_window = self.driver.window_handles[0]
        try:
            self.driver.execute_script("window.open('about:blank','secondtab');")
            self.driver.switch_to.window("secondtab")
            if self.cargo == 'Presidente':
                tse_url = f"https://resultados.tse.jus.br/oficial/app/index.html#/divulga/votacao-nominal;e=544;cargo=1;uf={self.ambito.lower()}"
            else:
                tse_url = f"https://resultados.tse.jus.br/oficial/app/index.html#/divulga/votacao-nominal;e=546;cargo={self.obter_valor_cargo()};uf={self.ambito.lower()}"
            self.driver.get(tse_url)
            sleep(1)
            lista_candidatos = self.driver.find_element(By.TAG_NAME, "app-lista-candidatos")
            divs = lista_candidatos.text.split("\n")
            linha_idx = -1
            for idx, linha in enumerate(divs):
                if nome_candidato.upper() in unidecode.unidecode(linha):
                    linha_idx = idx
                    break
            if linha_idx > -1:
                return float(divs[linha_idx + 4][-6:-1].replace(",", "."))
            else:
                return .0
        except Exception as e1:
            print(
                f"Falha ao obter dados do TSE de candidato {nome_candidato} para {self.instituto} e {self.cargo} no {self.ambito}")
            return .0
        finally:
            self.driver.switch_to.window(root_window)

    def calcular_diferenca(self, valor, valor_tse):
        return abs(valor - valor_tse)

    def obter_valor(self, linha):
        resultado = re.search(".{4}%", linha)
        if resultado:
            return float(resultado.group(0)[0:4])
        return .0

    def obter_nome_candidato(self, linha):
        resultado = linha.split(" ")
        if resultado:
            return unidecode.unidecode(resultado[0])
        return ""

    def obter_partido(self, linha):
        resultado = linha.split(" ")
        if resultado and len(resultado) > 3:
            return resultado[len(resultado) - 2]
        return ""

    def verificar_posicao(self):
        return False

    def verificar_margem(self, diferenca, margem_erro):
        return diferenca <= 2 * margem_erro

    def obter_margem_erro(self):
        return 3

    def criar_registro_pesquisa(self, intituto, margem_erro):
        tabela = self.driver.find_element(By.CLASS_NAME, "poll")
        cabecalho = tabela.find_elements(By.TAG_NAME, 'tr')[:1][0]
        data = self.obter_data(cabecalho.text)
        linhas = tabela.find_elements(By.TAG_NAME, 'tr')[1:-2]
        for linha in linhas:
            texto_linha = linha.text
            nome_candidato = self.obter_nome_candidato(texto_linha)
            valor_tse = self.obter_resultado_tse(nome_candidato)
            valor = self.obter_valor(texto_linha)
            diferenca = self.calcular_diferenca(valor, valor_tse)
            resultado = PesquisaEleitoralCandidato(
                candidato_nome=nome_candidato, partido=self.obter_partido(texto_linha), valor_referencia=valor,
                data_publicacao=data, instituto_nome=intituto, resultado_tse=valor_tse,
                margem_erro=margem_erro, diferenca=diferenca,
                acertou_posicao=self.verificar_posicao(),
                acertou_margem=self.verificar_margem(diferenca, margem_erro), cargo=self.cargo, ambito=self.ambito
            )
            self.resultados.append(resultado)


if __name__ == '__main__':
    scrapper = Scrapper()
    scrapper.start()
