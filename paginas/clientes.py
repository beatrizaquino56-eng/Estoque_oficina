import streamlit as st
import pandas as pd
import re  
from supabase import create_client, Client
from validacoes import validar_placa, texto_valido, validar_valores

# Função para formatar o telefone com parênteses no DDD e hífen
def formatar_telefone(num):
    apenas_numeros = re.sub(r'\D', '', num)
    if len(apenas_numeros) == 11:
        return f"({apenas_numeros[:2]}) {apenas_numeros[2:7]}-{apenas_numeros[7:]}"
    elif len(apenas_numeros) == 10:
        return f"({apenas_numeros[:2]}) {apenas_numeros[2:6]}-{apenas_numeros[6:]}"
    return num

# NOVO: Função para formatar o CPF automaticamente
def formatar_cpf(num):
    apenas_numeros = re.sub(r'\D', '', num)
    if len(apenas_numeros) == 11:
        return f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:9]}-{apenas_numeros[9:]}"
    return num

# 1. Conexão com o Banco de Dados (Usando chaves em MAIÚSCULAS para sincronizar com o app.py)
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

# 2. Título da Página
st.title("👥 Gerenciamento de Clientes")
st.write("Bem-vindo ao controle de clientes e ordens de serviço da oficina.")

# =========================================================================
st.header("👥 Cadastro de Clientes e Entrada de Veículos")
aba_cad_cliente, aba_ver_clientes = st.tabs(["📝 Cadastrar Cliente/Carro", "📋 Carros no Pátio / OS"])

with aba_cad_cliente:
    st.subheader("📝 Nova Ordem de Entrada")
    col1, col2 = st.columns(2)
    
    with col1:
        nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: João Silva")
        
        # NOVO: Entrada e formatação do CPF
        cpf_input = st.text_input("CPF do Cliente (Apenas números)", placeholder="Ex: 12345678901", max_chars=14)
        cpf = formatar_cpf(cpf_input)
        
        veiculo = st.text_input("Veículo (Modelo/Ano)", placeholder="Ex: Gol G6 2014")
        placa_input = st.text_input("Placa do Carro", placeholder="Ex: ABC1234")
        placa = placa_input.upper().strip() 
        
    with col2:
        telefone_input = st.text_input("Número de Telefone (com DDD)", placeholder="Ex: 16999999999")
        telefone = formatar_telefone(telefone_input)
        
        custo_previsto_reparo = st.number_input("Custo Previsto do Reparo (R$)", min_value=0.0, value=0.0, step=50.0)
        data_chegada = st.date_input("Data de Entrada/Chegada", value=pd.Timestamp.now().date(), format="DD/MM/YYYY")
        data_prevista_entrega = st.date_input("Data Prevista para Entrega", value=pd.Timestamp.now().date(), format="DD/MM/YYYY")
    
    # Caixa de texto ocupando a largura total para melhor visualização
    defeito = st.text_area("Defeito Relatado / Sintomas", placeholder="Ex: Barulho na suspensão dianteira ao passar por lombadas...")
        
    if st.button("Gravar Entrada do Veículo", key="btn_cliente"):
        if nome_cliente == "" or veiculo == "" or cpf_input == "":
            st.error("Por favor, preencha os campos obrigatórios: Nome, CPF e Veículo!")
        else:
            novo_cliente = {
                "nome_cliente": nome_cliente, 
                "cpf": cpf,  # NOVO: Coluna adicionada aqui
                "veiculo": veiculo, 
                "placa": placa, 
                "telefone": telefone, 
                "data_chegada": str(data_chegada),
                "data_prevista_entrega": str(data_prevista_entrega),
                "custo_previsto_reparo": float(custo_previsto_reparo),
                "defeito": defeito, 
                "status": "Aguardando Diagnóstico"
            }
            try:
                supabase.table("clientes").insert(novo_cliente).execute()
                st.success("✔️ Salvo com sucesso!")
            except Exception as e:
                st.error("❌ Erro retornado pelo Supabase:")
                st.code(str(e))  # <--- Isso vai mostrar na tela o nome do campo errado!
                st.success(f"Sucesso! Registro de '{nome_cliente}' gravado com sucesso!")
                st.rerun()
            
with aba_ver_clientes:
    st.subheader("📋 Veículos no Pátio")
    
    resposta_clientes = supabase.table("clientes").select("*").order("id", desc=True).execute()
    dados_clientes = pd.DataFrame(resposta_clientes.data)
    
    if not dados_clientes.empty:
        c_busca, c_filtro = st.columns([2, 1])
        with c_busca:
            busca_patio = st.text_input("🔍 Buscar por Nome, Placa ou CPF:", placeholder="Digite para filtrar...")
        with c_filtro:
            lista_status_opcoes = ["Todos", "Aguardando Diagnóstico", "Em Manutenção", "Aguardando Peças", "Pronto / Retirada"]
            filtro_status = st.selectbox("🚦 Filtrar por Status:", lista_status_opcoes)
        
        # Filtros Inteligentes
        if busca_patio:
            condicao_busca = dados_clientes['nome_cliente'].str.contains(busca_patio, case=False, na=False) | dados_clientes['placa'].str.contains(busca_patio, case=False, na=False)
            
            # NOVO: Permite buscar por CPF se a coluna existir na tabela
            if 'cpf' in dados_clientes.columns:
                condicao_busca = condicao_busca | dados_clientes['cpf'].str.contains(busca_patio, case=False, na=False)
                
            dados_clientes = dados_clientes[condicao_busca]
            
        if filtro_status != "Todos":
            dados_clientes = dados_clientes[dados_clientes['status'] == filtro_status]
        
        st.markdown("---")
        if dados_clientes.empty:
            st.info("Nenhum veículo encontrado com os filtros aplicados.")
        else:
            for index, row in dados_clientes.iterrows():
                status_atual = row['status']
                cor_status = "🟡" if status_atual == "Aguardando Diagnóstico" else "🔵" if status_atual == "Em Manutenção" else "🟠" if status_atual == "Aguardando Peças" else "🟢"
                
                data_formatada = "Não informada"
                if "data_chegada" in row and pd.notna(row['data_chegada']):
                    try:
                        data_formatada = pd.to_datetime(row['data_chegada']).strftime('%d/%m/%Y')
                    except:
                        data_formatada = str(row['data_chegada'])

                data_prev_formatada = "Não informada"
                if "data_prevista_entrega" in row and pd.notna(row['data_prevista_entrega']):
                    try:
                        data_prev_formatada = pd.to_datetime(row['data_prevista_entrega']).strftime('%d/%m/%Y')
                    except:
                        data_prev_formatada = str(row['data_prevista_entrega'])

                custo_previsto = row.get('custo_previsto_reparo', 0.0)
                if pd.isna(custo_previsto):
                    custo_previsto = 0.0

                # Pega o CPF se ele existir na linha atual
                cpf_exibicao = row.get('cpf', 'Não cadastrado')

                with st.expander(f"{cor_status} {row['veiculo']} — Placa: {row['placa']} ({row['nome_cliente']})", expanded=False):
                    st.markdown(f"**👤 Cliente:** {row['nome_cliente']} | **🆔 CPF:** `{cpf_exibicao}` | **📞 Tel:** {row['telefone']}")
                    st.markdown(f"**📅 Chegada:** `{data_formatada}` | **📅 Prev. Entrega:** `{data_prev_formatada}` | **💰 Custo Previsto:** `R$ {custo_previsto:.2f}`")
                    st.markdown(f"**🛠️ Defeito Relatado:** {row['defeito']}")
                    st.markdown(f"**📌 Status Atual:** `{status_atual}`")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        status_fluxo = ["Aguardando Diagnóstico", "Em Manutenção", "Aguardando Peças", "Pronto / Retirada"]
                        try:
                            index_status_atual = status_fluxo.index(status_atual)
                        except ValueError:
                            index_status_atual = 0
                            
                        novo_status = st.selectbox("Alterar Status para:", status_fluxo, index=index_status_atual, key=f"status_{row['id']}")
                        if st.button("🔄 Atualizar", key=f"btn_status_{row['id']}"):
                            supabase.table("clientes").update({"status": novo_status}).eq("id", row['id']).execute()
                            st.success("Status Atualizado com sucesso!")
                            st.rerun()
                    with c2:
                        st.write("")
                        st.write("")
                        if st.button("❌ Apagar Registro", key=f"btn_del_{row['id']}"):
                            supabase.table("clientes").delete().eq("id", row['id']).execute()
                            st.success("Removido!")
                            st.rerun()
    else:
        st.info("Nenhum veículo no pátio atualmente.")