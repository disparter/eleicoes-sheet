import dataclasses
import datetime
import json
import os
from dataclasses import dataclass

from dataclasses_json import dataclass_json
from time import sleep
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait


@dataclass_json
@dataclass
class PesquisaEleitoralCandidato:
    candidato_nome: str
    partido: str
    valor_referencia: int
    data_publicacao: datetime.datetime
    instituto_nome: str
    resultado_tse: int
    margem_erro: int
    diferenca: int
    acertou_posicao: bool
    acertou_margem: bool


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


options = Options()
options.headless = True
load_dotenv()
webdriver_path = os.getenv('WEBDRIVER_PATH')
driver = webdriver.Chrome(options=options, executable_path=webdriver_path)


def obter_data(cabecalho):
    pass


def obter_resultado_tse():
    pass


def calcular_diferenca(valor, valor_tse):
    pass


def obter_valor(linha):
    pass


def obter_nome_candidato(linha):
    pass


def obter_partido(linha):
    pass


def verificar_posicao():
    pass


def verificar_margem(diferenca, margem_erro):
    pass


def criar_registro_pesquisa(intituto, margem_erro):
    tabela = driver.find_element(By.CLASS_NAME, "poll")
    cabecalho = tabela.find_elements(By.TAG_NAME, 'tr')[:1]
    data = obter_data(cabecalho)
    linhas = tabela.find_elements(By.TAG_NAME, 'tr')[1:]
    resultados = []
    for linha in linhas:
        valor_tse = obter_resultado_tse()
        valor = obter_valor(linha)
        diferenca = calcular_diferenca(valor, valor_tse)
        resultado = PesquisaEleitoralCandidato(
            candidato_nome=obter_nome_candidato(linha), partido=obter_partido(linha), valor_referencia=valor,
            data_publicacao=data, instituto_nome=intituto, resultado_tse=obter_resultado_tse(),
            margem_erro=margem_erro, diferenca=diferenca,
            acertou_posicao=verificar_posicao(),
            acertou_margem=verificar_margem(diferenca, margem_erro)
        )
        resultados.append(resultado)
    return resultados

if __name__ == '__main__':
    try:
        base_url = f'https://www.poder360.com.br/agregador-de-pesquisas/'
        sleep(0.1)
        driver.get(base_url)
        sleep(0.5)
        selects = driver.find_elements(By.TAG_NAME, "select")
        select_cargos = selects[0]
        cargos = [x.get_attribute('value') for x in select_cargos.find_elements(By.TAG_NAME, "option")]
        select_ambitos = selects[1]
        ambitos = [x.get_attribute('value') for x in select_ambitos.find_elements(By.TAG_NAME, "option")][1:]
        select_anos = selects[2]
        ano = [x.get_attribute('value') for x in select_anos.find_elements(By.TAG_NAME, "option")]
        select_turnos = selects[3]
        turnos = [x.get_attribute('value') for x in select_turnos.find_elements(By.TAG_NAME, "option")]
        select_institutos = driver.find_elements(By.TAG_NAME, "select")[7]
        institutos_pesquisa = [x.get_attribute('value') for x in
                               select_institutos.find_elements(By.TAG_NAME, "option")][1:]
    
        for cargo in cargos:
            Select(select_cargos).select_by_value(cargo)
            sleep(0.5)
            if cargo != 'Presidente':
                for ambito in ambitos:
                    Select(select_ambitos).select_by_value(ambito)
                    sleep(0.5)
                    for instituto in institutos_pesquisa:
                        try:
                            nome_arquivo = instituto+ambito+cargo
                            Select(select_institutos).select_by_value(instituto)
                            sleep(0.5)
                            resultados = criar_registro_pesquisa()
                            resultados_compilados = PesquisaEleitoralCandidato.schema().dumps(resultados, many=True)
                            with open(f'data/{nome_arquivo}.json', 'w') as f:
                                f.write(resultados_compilados)
                                print(f'{nome_arquivo}.json was created')
                        except:
                            pass
    finally:
        driver.quit()
