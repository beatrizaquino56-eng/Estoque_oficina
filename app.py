import streamlit as st
import pandas as pd
import re
from supabase import create_client, Client

# --- 1. CONFIGURAÇÃO DE CONEXÃO COM O SUPABASE ---
SUPABASE_URL = "https://lgpcpnxhkogtvhjtfwya.supabase.co"
SUPABASE_KEY = "sb_publishable_1kunRmsK4SdXCk849paiyg_1OaraKs_"

# Inicializa o cliente do Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("⚙️ Sistema Integrado - Oficina Mecânica")
st.markdown("---")

# --- 2. MENU PRINCIPAL DE NAVEGAÇÃO ---
modulo = st.sidebar.radio("Selecione o Módulo:", ["👥 Clientes & Veículos", "📦 Gerenciar Estoque"])

# Função para formatar o telefone com parênteses no DDD e hífen
def formatar_telefone(num):
    apenas_numeros = re.sub(r'\D', '', num) # Remove letras ou espaços
    if len(apenas_numeros) == 11: # Celular com 9 dígitos + DDD
        return f"({apenas_numeros[:2]}) {apenas_numeros[2:7]}-{apenas_numeros[7:]}"
    elif len(apenas_numeros) == 10: # Fixo com 8 dígitos + DDD
        return f"({apenas_numeros[:2]}) {apenas_numeros[2:6]}-{apenas_numeros[6:]}"
    return num # Retorna o original se não tiver o tamanho padrão

# ==============================================================================
#                      MÓDULO: Clientes & Veículos
# ==============================================================================
if modulo == "👥 Clientes & Veículos":
    st.header("👥 Cadastro de Clientes e Entrada de Veículos")
    
    aba_cad_cliente, aba_ver_clientes = st.tabs(["📝 Cadastrar Cliente/Carro", "📋 Carros no Pátio / OS"])
    
    with aba_cad_cliente:
        st.subheader("📝 Nova Ordem de Entrada")
        
        col1, col2 = st.columns(2)
        with col1:
            nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: João Silva")
            veiculo = st.text_input("Veículo (Modelo/Ano)", placeholder="Ex: Gol G6 2014")
            
            # Ajuste: Letras da placa entram automaticamente em Maiúsculas
            placa_input = st.text_input("Placa do Carro", placeholder="Ex: ABC1234 ou ABC1D23")
            placa = placa_input.upper().strip() 
            
        with col2:
            telefone_input = st.text_input("Número de Telefone (com DDD)", placeholder="Ex: 16999999999")
            # Aplica a máscara automaticamente ao salvar
            telefone = formatar_telefone(telefone_input)
            
            defeito = st.text_area("Defeito Relatado / Sintomas", placeholder="Ex: Barulho na suspensão dianteira...")
            
        if st.button("Gravar Entrada do Veículo", key="btn_cliente"):
            if nome_cliente == "" or veiculo == "":
                st.error("Por favor, preencha pelo menos o Nome do Cliente e o Veículo!")
            else:
                novo_cliente = {
                    "nome_cliente": nome_cliente,
                    "veiculo": veiculo,
                    "placa": placa,
                    "telefone": telefone,
                    "defeito": defeito,
                    "status": "Aguardando Diagnóstico"
                }
                
                supabase.table("clientes").insert(novo_cliente).execute()
                st.success(f"Sucesso! Registro de '{nome_cliente}' gravado com telefone {telefone}!")
                st.rerun()
                
    with aba_ver_clientes:
        st.subheader("📋 Veículos no Pátio")
        
        resposta_clientes = supabase.table("clientes").select("*").order("created_at", desc=True).execute()
        dados_clientes = pd.DataFrame(resposta_clientes.data)
        
        if not dados_clientes.empty:
            busca_pacio = st.text_input("🔍 Buscar por Nome do Cliente ou Placa:", placeholder="Digite para filtrar...")
            if busca_pacio:
                dados_clientes = dados_clientes[
                    dados_clientes['nome_cliente'].str.contains(busca_pacio, case=False, na=False) |
                    dados_clientes['placa'].str.contains(busca_pacio, case=False, na=False)
                ]
            
            st.markdown("---")
            # NOVO LAYOUT: Em vez de tabela pequena, exibe cartões grandes e fáceis de ler
            for index, row in dados_clientes.iterrows():
                # Define uma cor amigável baseada no status
                status_atual = row['status']
                cor_status = "🟡" if status_atual == "Aguardando Diagnóstico" else "🔵" if status_atual == "Em Manutenção" else "🟠" if status_atual == "Aguardando Peças" else "🟢"
                
                with st.expander(f"{cor_status} {row['veiculo']} — Placa: {row['placa']} ({row['nome_cliente']})", expanded=True):
                    st.markdown(f"**👤 Cliente:** {row['nome_cliente']} | **📞 Tel:** {row['telefone']}")
                    st.markdown(f"**🛠️ Defeito Relatado:** {row['defeito']}")
                    st.markdown(f"**📌 Status Atual:** `{status_atual}`")
                    
                    # Ações direto no cartão do veículo
                    c1, c2 = st.columns(2)
                    with c1:
                        novo_status = st.selectbox("Alterar Status para:", ["Aguardando Diagnóstico", "Em Manutenção", "Aguardando Peças", "Pronto / Retirada"], key=f"status_{row['id']}")
                        if st.button("🔄 Atualizar", key=f"btn_status_{row['id']}"):
                            supabase.table("clientes").update({"status": novo_status}).eq("id", row['id']).execute()
                            st.success("Status Atualizado!")
                            st.rerun()
                    with c2:
                        st.write("")
                        if st.button("❌ Apagar Registro", key=f"btn_del_{row['id']}"):
                            supabase.table("clientes").delete().eq("id", row['id']).execute()
                            st.success("Removido!")
                            st.rerun()
        else:
            st.info("Nenhum veículo no pátio atualmente.")

# ==============================================================================
#                      MÓDULO: GERENCIAR ESTOQUE
# ==============================================================================
elif modulo == "📦 Gerenciar Estoque":
    st.header("📦 Gerenciamento de Peças e Estoque")
    
    aba_entrada, aba_saida, aba_excluir = st.tabs(["📥 Entradas / Reposição", "📤 Dar Saída de Peça", "❌ Excluir Item"])

    with aba_entrada:
        st.subheader("📥 Entrada de Mercadorias")
        tipo_entrada = st.radio("Selecione o tipo de operação:", ["Cadastrar um produto NOVO", "Adicionar quantidade a um produto JÁ CADASTRADO"], horizontal=True)
        st.markdown("---")
        
        if tipo_entrada == "Cadastrar um produto NOVO":
            st.write("### 📝 Preencha os dados do novo item:")
            col1, col2 = st.columns(2)
            with col1:
                nome_produto = st.text_input("Descrição do Produto", placeholder="Ex: Kit de Embreagem", key="add_nome")
                codigo_original = st.text_input("Código Original / Nº Montadora", placeholder="Ex: 5Z0141025", key="add_cod_orig").upper()
                marca = st.text_input("Marca/Fabricante", placeholder="Ex: LUK", key="add_marca")
                quantidade = st.number_input("Quantidade Inicial", min_value=0, value=0, step=1, key="add_qtd")
                preco_custo = st.number_input("Preço de Custo (R$)", min_value=0.0, value=0.0, step=0.50, key="add_custo")
            with col2:
                ncm = st.text_input("Código NCM (8 dígitos)", max_chars=8, placeholder="Ex: 87082999", key="add_ncm")
                cest = st.text_input("Código CEST", max_chars=9, placeholder="Ex: 16.001.00", key="add_cest")
                csosn = st.text_input("Código CSOSN", max_chars=3, placeholder="Ex: 500", key="add_csosn")
                origem = st.selectbox("Origem da Mercadoria", ["0 - Nacional", "1 - Estrangeira", "2 - Adquirida no Mercado Interno"], key="add_origem")
                peso = st.number_input("Peso do Produto (Kg)", min_value=0.000, value=0.000, step=0.050, format="%.3f", key="add_peso")

            if st.button("Gravar Novo Produto", key="btn_gravar"):
                if nome_produto == "":
                    st.error("Por favor, digite o nome do produto antes de salvar!")
                else:
                    novo_produto = {"descricao": nome_produto, "codigo_original": codigo_original, "marca": marca, "quantidade": int(quantidade), "ncm": ncm}
                    supabase.table("estoque").insert(novo_produto).execute()
                    st.success(f"Sucesso! O produto '{nome_produto}' foi salvo na Nuvem!")
                    st.rerun()
                    
        else:
            st.write("### 🔄 Reposição de Estoque Existente:")
            resposta_entrada = supabase.table("estoque").select("id, descricao, quantidade").order("descricao").execute()
            dados_produtos = pd.DataFrame(resposta_entrada.data)
            
            if dados_produtos.empty:
                st.info("Nenhum produto cadastrado.")
            else:
                opcoes_entrada = {f"{row['descricao']} - Atual: {row['quantidade']}": row['id'] for index, row in dados_produtos.iterrows()}
                selecao_entrada = st.selectbox("Escolha o produto que chegou na oficina:", list(opcoes_entrada.keys()), key="sel_reposicao")
                id_produto_reposicao = opcoes_entrada[selecao_entrada]
                
                qtd_atual_banco = dados_produtos[dados_produtos['id'] == id_produto_reposicao]['quantidade'].values[0]
                qtd_novas_pecas = st.number_input("Quantidade de peças que chegaram:", min_value=1, value=1, step=1, key="qtd_reposicao")
                
                if st.button("Confirmar Entrada / Somar ao Estoque", key="btn_reposicao"):
                    nova_quantidade = int(qtd_atual_banco + qtd_novas_pecas)
                    supabase.table("estoque").update({"quantidade": nova_quantidade}).eq("id", id_produto_reposicao).execute()
                    st.success("Estoque atualizado na Nuvem!")
                    st.rerun()

    with aba_saida:
        st.subheader("🛠️ Dar Baixa em Peça Utilizada")
        resposta_saida = supabase.table("estoque").select("id, descricao, quantidade").order("descricao").execute()
        dados_produtos_saida = pd.DataFrame(resposta_saida.data)
        
        if dados_produtos_saida.empty:
            st.info("Nenhum produto cadastrado no estoque.")
        else:
            opcoes_produtos = {f"{row['descricao']} - (Disponível: {row['quantidade']})": row['id'] for index, row in dados_produtos_saida.iterrows()}
            selecao = st.selectbox("Selecione o Produto que vai sair:", list(opcoes_produtos.keys()), key="sel_saida")
            produto_id_selecionado = opcoes_produtos[selecao]
            
            qtd_atual = dados_produtos_saida[dados_produtos_saida['id'] == produto_id_selecionado]['quantidade'].values[0]
            qtd_saida = st.number_input("Quantidade de Saída", min_value=1, max_value=int(qtd_atual) if qtd_atual > 0 else 1, step=1, key="qtd_saida")
            
            if st.button("Confirmar Saída / Dar Baixa", key="btn_saida"):
                if qtd_atual <= 0:
                    st.error("Não é possível dar saída! Estoque zerado.")
                else:
                    nova_quantidade_saida = int(qtd_atual - qtd_saida)
                    supabase.table("estoque").update({"quantidade": nova_quantidade_saida}).eq("id", produto_id_selecionado).execute()
                    st.success("Baixa realizada com sucesso!")
                    st.rerun()

    with aba_excluir:
        st.subheader("❌ Remover Item Definitivamente")
        resposta_excluir = supabase.table("estoque").select("id, descricao, codigo_original").order("descricao").execute()
        dados_produtos_excluir = pd.DataFrame(resposta_excluir.data)
        
        if dados_produtos_excluir.empty:
            st.info("Nenhum produto cadastrado.")
        else:
            opcoes_excluir = {f"{row['descricao']} (Cód: {row['codigo_original']})": row['id'] for index, row in dados_produtos_excluir.iterrows()}
            selecao_excluir = st.selectbox("Selecione o produto que deseja APAGAR:", list(opcoes_excluir.keys()), key="sel_excluir")
            id_produto_excluir = opcoes_excluir[selecao_excluir]
            
            if st.button("🔥 Apagar Produto do Estoque", key="btn_deletar"):
                supabase.table("estoque").delete().eq("id", id_produto_excluir).execute()
                st.success("O produto foi removido!")
                st.rerun()

    st.markdown("---")
    st.subheader("📊 Relatório Atual de Estoque")
    busca_codigo = st.text_input("🔍 Buscar por Código Original:", placeholder="Digite o código da peça...")
    
    resposta_final = supabase.table("estoque").select("*").order("descricao").execute()
    dados_finais = pd.DataFrame(resposta_final.data)
    
    if not dados_finais.empty:
        colunas_ordenadas = ["id", "codigo_original", "ncm", "descricao", "marca", "quantidade", "created_at"]
        colunas_existem = [c for c in colunas_ordenadas if c in dados_finais.columns]
        if busca_codigo:
            dados_finais = dados_finais[dados_finais['codigo_original'].str.contains(busca_codigo, case=False, na=False)]
        if dados_finais.empty:
            st.info("Nenhuma peça encontrada.")
        else:
            st.dataframe(dados_finais[colunas_existem], use_container_width=True)
    else:
        st.info("O estoque na nuvem está vazio.")