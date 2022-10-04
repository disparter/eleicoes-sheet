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


def obter_data(cabecalho):
    return datetime.datetime.strptime(cabecalho.split(" ")[2], "%d/%m/%Y")


def obter_valor_cargo():
    if cargo == 'Governador':
        return 3
    if cargo == 'Senador':
        return 5
    raise NotImplementedError('opcao apenas para governador e senador por enquanto')


def obter_resultado_tse(nome_candidato):
    root_window = driver.window_handles[0]
    try:
        driver.execute_script("window.open('about:blank','secondtab');")
        driver.switch_to.window("secondtab")
        if cargo == 'Presidente':
            tse_url = f"https://resultados.tse.jus.br/oficial/app/index.html#/divulga/votacao-nominal;e=544;cargo=1;uf={ambito.lower()}"
        else:
            tse_url = f"https://resultados.tse.jus.br/oficial/app/index.html#/divulga/votacao-nominal;e=546;cargo={obter_valor_cargo()};uf={ambito.lower()}"
        driver.get(tse_url)
        sleep(1)
        lista_candidatos = driver.find_element(By.TAG_NAME, "app-lista-candidatos")
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
        print(f"Falha ao obter dados do TSE de candidato {nome_candidato} para {instituto} e {cargo} no {ambito}")
        return .0
    finally:
        driver.switch_to.window(root_window)


def calcular_diferenca(valor, valor_tse):
    return abs(valor - valor_tse)


def obter_valor(linha):
    resultado = re.search(".{4}%", linha)
    if resultado:
        return float(resultado.group(0)[0:4])
    return .0


def obter_nome_candidato(linha):
    resultado = linha.split(" ")
    if resultado:
        return unidecode.unidecode(resultado[0])
    return ""


def obter_partido(linha):
    resultado = linha.split(" ")
    if resultado and len(resultado) > 3:
        return resultado[len(resultado) - 2]
    return ""


def verificar_posicao():
    return False


def verificar_margem(diferenca, margem_erro):
    return diferenca <= 2 * margem_erro


def obter_margem_erro():
    return 3


def criar_registro_pesquisa(intituto, margem_erro):
    tabela = driver.find_element(By.CLASS_NAME, "poll")
    cabecalho = tabela.find_elements(By.TAG_NAME, 'tr')[:1][0]
    data = obter_data(cabecalho.text)
    linhas = tabela.find_elements(By.TAG_NAME, 'tr')[1:-2]
    for linha in linhas:
        texto_linha = linha.text
        nome_candidato = obter_nome_candidato(texto_linha)
        valor_tse = obter_resultado_tse(nome_candidato)
        valor = obter_valor(texto_linha)
        diferenca = calcular_diferenca(valor, valor_tse)
        resultado = PesquisaEleitoralCandidato(
            candidato_nome=nome_candidato, partido=obter_partido(texto_linha), valor_referencia=valor,
            data_publicacao=data, instituto_nome=intituto, resultado_tse=valor_tse,
            margem_erro=margem_erro, diferenca=diferenca,
            acertou_posicao=verificar_posicao(),
            acertou_margem=verificar_margem(diferenca, margem_erro), cargo=cargo, ambito=ambito
        )
        resultados.append(resultado)


options = Options()
options.headless = True
load_dotenv()
webdriver_path = os.getenv('WEBDRIVER_PATH')
driver = webdriver.Chrome(options=options, executable_path=webdriver_path)

try:
    base_url = f'https://www.poder360.com.br/agregador-de-pesquisas/'
    driver.get(base_url)
    sleep(0.5)
    selects = driver.find_elements(By.TAG_NAME, "select")
    select_cargos = selects[0]
    cargos = [x.get_attribute('value') for x in select_cargos.find_elements(By.TAG_NAME, "option")]
    select_anos = selects[2]
    ano = [x.get_attribute('value') for x in select_anos.find_elements(By.TAG_NAME, "option")]
    select_turnos = selects[3]
    turnos = [x.get_attribute('value') for x in select_turnos.find_elements(By.TAG_NAME, "option")]

    resultados = []
    for cargo in cargos:
        select_ambitos = selects[1]
        ambitos = [x.get_attribute('value') for x in select_ambitos.find_elements(By.TAG_NAME, "option")][1:]
        for ambito in ambitos:
            try:
                Select(select_ambitos).select_by_value(ambito)
                sleep(1)
            except Exception as e:
                print(f"Falhou ao buscar novos registros de ambitos para {ambito} e {cargo}")
                break

            try:
                select_institutos = driver.find_elements(By.TAG_NAME, "select")[7]
                sleep(1)
                institutos_pesquisa = [x.get_attribute('value') for x in
                                       select_institutos.find_elements(By.TAG_NAME, "option")][1:]
                for instituto in institutos_pesquisa:
                    try:
                        Select(select_institutos).select_by_value(instituto)
                        sleep(1)
                        print(f"Buscando registro para {instituto} e {cargo} no {ambito}")
                        criar_registro_pesquisa(instituto, obter_margem_erro())
                        print(f"Obtido registro para {instituto} e {cargo} no {ambito}")
                    except Exception as e:
                        print(f"Falhou em criar registro para {instituto} e {cargo} no {ambito}")
            except Exception as e:
                print(f"Falhou ao buscar novos registros de institutos para {ambito} e {cargo}")
                break

        selects = driver.find_elements(By.TAG_NAME, "select")
        select_cargos = selects[0]
        cargos = [x.get_attribute('value') for x in select_cargos.find_elements(By.TAG_NAME, "option")]
        print(f"Terminou de obter dados para {cargo}")

    resultados_compilados = PesquisaEleitoralCandidato.schema().dumps(resultados, many=True)
    with open(f'data.json', 'w') as f:
        f.write(resultados_compilados)
        print(f'data.json foi criado')
finally:
    driver.quit()
