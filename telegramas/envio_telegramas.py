"""
RPA — Envio de telegramas em massa pelo sistema dos Correios (SMT à vista).

Para cada oficina da planilha, preenche remetente, destinatário e a mensagem
personalizada com o crédito pré-aprovado, faz o pagamento com o cartão
cadastrado e, ao final, abre o relatório analítico dos envios.

Impacto: processo reduzido de 9h para 1h30.

Planilha de entrada (colunas): Nome_Socio, CEP, Numero, Complemento,
CNPJ_OFICINA, Valor

Variáveis de ambiente:
    CORREIOS_USER, CORREIOS_PASSWORD, CARTAO_CVV,
    PLANILHA_TELEGRAMAS (caminho do .xlsx)
"""

import os
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ------------------------------------------------------------------
# Configuração
# ------------------------------------------------------------------
URL_LOGIN = "https://smt-avista.correios.com.br/app/"
URL_NOVO_TELEGRAMA = "https://smt-avista.correios.com.br/router.php?a=tnv"
URL_RELATORIO = "https://smt-avista.correios.com.br/router.php?a=rv#"

REMETENTE = {
    "nome": "NOME DA EMPRESA REMETENTE",
    "cep": "00000-000",
    "numero": "000",
    "complemento": "Complemento do endereço",
    "cnpj_cobranca": "00000000000000",
}

TEXTO_BASE = """Prezado(a) {nome},

A Cilia tem uma novidade importante para sua oficina!
Com base no seu alto volume de reparos na nossa plataforma, sua oficina foi selecionada para participar do lançamento do nosso novo produto de crédito.

Você já tem R$ {credito_pre_aprovado} de crédito pré aprovado disponível nesta semana, com condições exclusivas para parceiros como você.

Para acessar sua oferta:
- Se você, sócio(a), já possui uma conta na Cilia (CPF): basta entrar na plataforma e visualizar a oferta disponível.
- Se apenas seus funcionários têm conta: a solicitação precisará ser feita em seu nome, pois apenas você pode contratar o crédito.
Mas não se preocupe, basta entrar em contato com a Cilia que auxiliaremos neste processo.

Dúvidas? Estamos aqui para ajudar:
- WhatsApp/Telefone: 0800 000 0000
- E-mail: contato@empresa.com.br

Essa oferta é uma forma de apoiar o crescimento da sua oficina e fortalecer nossa parceria. Conte sempre com a gente!

Atenciosamente,
Equipe Cilia"""


def formatar_reais(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def digitar_devagar(elemento, texto):
    """Digita caractere a caractere (o site aplica máscaras em CEP e CNPJ)."""
    for c in str(texto):
        elemento.send_keys(c)


def clicar(navegador, xpath):
    navegador.find_element(By.XPATH, xpath).click()


def preencher(navegador, xpath, texto, limpar=True):
    elemento = navegador.find_element(By.XPATH, xpath)
    if limpar:
        elemento.clear()
    elemento.send_keys(texto)
    return elemento


def login(navegador):
    navegador.get(URL_LOGIN)
    navegador.maximize_window()
    time.sleep(0.5)
    preencher(navegador, '//*[@id="username"]', os.environ["CORREIOS_USER"])
    preencher(navegador, '//*[@id="password"]', os.environ["CORREIOS_PASSWORD"])
    clicar(navegador, '//*[@id="fm1"]/div/div[2]/button')
    clicar(navegador, "/html/body/main/div[2]/a[1]/div/div/img")


def preencher_remetente(navegador):
    elemento = WebDriverWait(navegador, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="nome"]'))
    )
    elemento.clear()
    elemento.click()
    elemento.send_keys(REMETENTE["nome"])
    time.sleep(0.5)

    preencher(navegador, '//*[@id="cep"]', REMETENTE["cep"])
    time.sleep(2)
    preencher(navegador, '//*[@id="numero"]', REMETENTE["numero"])
    time.sleep(0.5)
    preencher(navegador, '//*[@id="complemento"]', REMETENTE["complemento"])
    time.sleep(0.5)

    cnpj = navegador.find_element(By.ID, "cpf_cnpj_cobranca")
    cnpj.clear()
    digitar_devagar(cnpj, REMETENTE["cnpj_cobranca"])
    time.sleep(2)


def preencher_destinatario(navegador, row):
    clicar(navegador, '//*[@id="tabs2"]/nav/a[2]')
    time.sleep(1)

    digitar_devagar(navegador.find_element(By.XPATH, '//*[@id="nome-destinatario_0"]'), row["Nome_Socio"])
    time.sleep(1)
    digitar_devagar(navegador.find_element(By.XPATH, '//*[@id="cep-destinatario_0"]'), row["CEP"])
    time.sleep(3)  # aguarda o preenchimento automático do endereço
    preencher(navegador, '//*[@id="numero-destinatario_0"]', str(row["Numero"]), limpar=False)
    time.sleep(0.5)
    preencher(navegador, '//*[@id="complemento-destinatario_0"]', str(row["Complemento"]), limpar=False)
    time.sleep(1)
    digitar_devagar(navegador.find_element(By.ID, "cpf_cnpj_destinatario_0"), row["CNPJ_OFICINA"])
    time.sleep(3)


def preencher_mensagem(navegador, row):
    clicar(navegador, '//*[@id="tabs2"]/nav/a[3]')
    time.sleep(3)

    mensagem = TEXTO_BASE.format(
        nome=row["Nome_Socio"],
        credito_pre_aprovado=formatar_reais(row["Valor"]),
    )
    campo = navegador.find_element(By.XPATH, '//*[@id="conteudo_mensagem"]/div/div[1]/div/div[2]/div[2]/div[1]')
    campo.clear()
    campo.click()
    campo.send_keys(mensagem)
    time.sleep(1)


def pagar_e_enviar(navegador):
    navegador.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)

    aba_pagamento = navegador.find_element(By.XPATH, '//*[@id="tabs2"]/nav/a[4]')
    aba_pagamento.click()
    aba_pagamento.click()
    time.sleep(3)

    navegador.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(0.3)

    clicar(navegador, '//*[@id="termoAceite"]')
    clicar(navegador, '//*[@id="enviar"]')
    time.sleep(3)

    clicar(navegador, '//*[@id="btn-pagar-com-cartao-bk"]/div')
    time.sleep(1)
    clicar(navegador, '//*[@id="btn-pagar"]')
    time.sleep(1)

    # Seleciona o cartão já cadastrado na conta
    clicar(navegador, "/html/body/main/div[1]/section[1]/table/tbody/tr[1]/td[2]/div/button[1]")
    time.sleep(0.5)
    preencher(navegador, '//*[@id="cvv"]', os.environ["CARTAO_CVV"])
    time.sleep(0.5)
    clicar(navegador, '//*[@id="formInputs"]/div[2]/div[1]/div[2]/label[1]/input')
    time.sleep(0.5)
    clicar(navegador, '//*[@id="btnSendOrder"]')
    time.sleep(2)


def main():
    navegador = webdriver.Chrome()
    login(navegador)

    df = pd.read_excel(os.environ["PLANILHA_TELEGRAMAS"])
    print(df.head(10))
    time.sleep(1)

    for _, row in df.iterrows():
        print(f"Enviando telegrama para {row['Nome_Socio']}...")
        preencher_remetente(navegador)
        preencher_destinatario(navegador, row)
        preencher_mensagem(navegador, row)
        pagar_e_enviar(navegador)
        navegador.get(URL_NOVO_TELEGRAMA)

    # Relatório analítico dos envios
    time.sleep(1)
    navegador.get(URL_RELATORIO)
    time.sleep(1)
    clicar(navegador, '//*[@id="analitico"]')


if __name__ == "__main__":
    main()
