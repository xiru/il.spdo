def valida_cpf_cnpj(cpf_cnpj):
    if cpf_cnpj is None:
        return True
    cpf_cnpj = ''.join([c for c in cpf_cnpj if c.isdigit()])
    if len(cpf_cnpj) == 11:
        return valida_cpf(cpf_cnpj)
    elif len(cpf_cnpj) == 14:
        return valida_cnpj(cpf_cnpj)
    return False

def valida_cpf(cpf):
    cpf = map(int, cpf)
    soma = cpf[0]*10 + cpf[1]*9 + cpf[2]*8 + cpf[3]*7 + cpf[4]*6 + \
           cpf[5]*5 + cpf[6]*4 + cpf[7]*3 + cpf[8]*2
    valor = (soma/11)*11
    resultado = soma - valor
    if resultado == 1 or resultado == 0:
        primeiro_digito = 0
    else:
        primeiro_digito = 11 - resultado
    soma = cpf[0]*11 + cpf[1]*10 + cpf[2]*9 + cpf[3]*8 + cpf[4]*7 + \
           cpf[5]*6 + cpf[6]*5 + cpf[7]*4 + cpf[8]*3 + primeiro_digito*2
    valor = (soma/11)*11
    resultado = soma - valor
    if resultado == 1 or resultado == 0:
        segundo_digito = 0
    else:
        segundo_digito = 11 - resultado
    return cpf[-2] == primeiro_digito and cpf[-1] == segundo_digito

def valida_cnpj(cnpj):
    cnpj = map(int, cnpj)
    soma = cnpj[0]*5 + cnpj[1]*4 + cnpj[2]*3 + cnpj[3]*2 + cnpj[4]*9 + cnpj[5]*8 + \
           cnpj[6]*7 + cnpj[7]*6 + cnpj[8]*5 + cnpj[9]*4 + cnpj[10]*3 + cnpj[11]*2
    resultado = soma % 11
    if resultado < 2:
        primeiro_digito = 0
    else:
        primeiro_digito = 11 - resultado
    soma = cnpj[0]*6 + cnpj[1]*5 + cnpj[2]*4 + cnpj[3]*3 + cnpj[4]*2 + cnpj[5]*9 + \
           cnpj[6]*8 + cnpj[7]*7 + cnpj[8]*6 + cnpj[9]*5 + cnpj[10]*4 + cnpj[11]*3 + primeiro_digito*2
    resultado = soma % 11
    if resultado < 2:
        segundo_digito = 0
    else:
        segundo_digito = 11 - resultado
    return cnpj[-2] == primeiro_digito and cnpj[-1] == segundo_digito
