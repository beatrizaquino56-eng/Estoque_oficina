import re

# 1. VALIDAÇÃO DE PLACA (Antiga e Mercosul)
def validar_placa(placa):
    # Remove hifens, espaços e deixa tudo em maiúsculo
    placa_limpa = placa.strip().upper().replace("-", "").replace(" ", "")
    
    # Padrão Antigo: 3 letras e 4 números (Ex: ABC1234)
    padrao_antigo = r'^[A-Z]{3}\d{4}$'
    # Padrão Mercosul: 3 letras, 1 número, 1 letra, 2 números (Ex: ABC1D23)
    padrao_mercosul = r'^[A-Z]{3}\d[A-Z]\d{2}$'
    
    if re.match(padrao_antigo, placa_limpa) or re.match(padrao_mercosul, placa_limpa):
        return True, placa_limpa  # Retorna True e a placa formatada sem hífen
    return False, "Placa inválida! Use o formato ABC-1234 ou ABC1D23."

# 2. SANITIZAÇÃO DE TEXTO (Evita strings vazias mascaradas)
def texto_valido(texto):
    if not texto or texto.strip() == "":
        return False
    return True

# 3. VALIDAÇÃO DE NÚMEROS (Quantidade e Custos)
def validar_valores(quantidade, custo=0.0):
    if quantidade < 0:
        return False, "A quantidade não pode ser negativa!"
    if custo < 0:
        return False, "O custo/preço não pode ser negativo!"
    return True, "Sucesso"