import streamlit as st
import pandas as pd
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

# ==============================================================================
#                      MÓDULO: CLIENTES & VEÍCULOS
# ==============================================================================
if modulo == "👥 Clientes & Veículos":
    st.header("👥 Cadastro de Clientes e Entrada de Veículos")
    
    aba_cad_cliente, aba_ver_clientes = st.tabs(["📝 Cadastrar Cliente/Carro", "📋 Carros no Pátio / Relatório"])
    
    with aba_cad_cliente:
        st.subheader("📝 Nova Ordem de Entrada")
        
        col1, col2 = st.columns(2)
        with col1:
            nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: João Silva")
            veiculo = st.text_input("Veículo (Modelo/Ano)", placeholder="Ex: Gol G6 2014")
            placa = st.text_input("Placa do Carro", placeholder="Ex: ABC-1234").upper() # Força letras maiúsculas
        with col2:
            telefone = st.text_input("Número de Telefone", placeholder="Ex: (16) 99999-9999")
            defeito = st.text_area("Defeito Relatado / Sintomas", placeholder="Ex: Barulho na suspensão dianteira ao passar em ondulações.")
            
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
                st.success(f"Sucesso! O cliente '{nome_cliente}' e o veículo '{veiculo}' foram registrados!")
                st.rerun()
                
    with aba_ver_clientes:
        st.subheader("📋 Veículos Registrados e Status")
        
        # Busca os clientes cadastrados na nuvem
        resposta_clientes = supabase.table("clientes").select("*").order("created_at", desc=True).execute()
        dados_clientes = pd.DataFrame(resposta_clientes.data)
        
        if not dados_clientes.empty:
            # Filtro de busca por Placa ou Nome
            busca_pacio = st.text_input("🔍 Buscar veículo por Nome ou Placa:", placeholder="Digite para filtrar...")
            if busca_pacio:
                dados_clientes = dados_clientes[
                    dados_clientes['nome_cliente'].str.contains(busca_pacio, case=False, na=False) |
                    dados_clientes['placa'].str.contains(busca_pacio, case=False, na=False)
                ]
            
            # Formata a exibição das colunas
            colunas_clientes = ["id", "nome_cliente", "veiculo", "placa", "telefone", "defeito", "status", "created_at"]
            st.dataframe(dados_clientes[colunas_clientes], use_container_width=True)
            
            st.markdown("---")
            st.subheader("⚙️ Atualizar Status ou Remover Registro")
            
            # Opções para atualizar status ou apagar
            opcoes_clientes = {f"{row['nome_cliente']} - {row['veiculo']} ({row['placa']})": row['id'] for index, row in dados_clientes.iterrows()}
            selecao_cli = st.selectbox("Selecione a Ordem/Cliente para modificar:", list(opcoes_clientes.keys()))
            id_cli_selecionado = opcoes_clientes[selecao_cli]
            
            c1, c2 = st.columns(2)
            with c1:
                novo_status = st.selectbox("Mudar Status para:", ["Aguardando Diagnóstico", "Em Manutenção", "Aguardando Peças", "Pronto / Retirada"])
                if st.button("🔄 Atualizar Status"):
                    supabase.table("clientes").update({"status": novo_status}).eq("id", id_cli_selecionado).execute()
                    st.success("Status atualizado com sucesso!")
                    st.rerun()
            with c2:
                st.write("Excluir histórico:")
                if st.button("❌ Apagar Registro Definitivamente"):
                    supabase.table("clientes").delete().eq("id", id_cli_selecionado).execute()
                    st.success("Registro removido do sistema!")
                    st.rerun()
        else:
            st.info("Nenhum veículo no pátio atualmente.")

# ==============================================================================
#                      MÓDULO: GERENCIAR ESTOQUE
# ==============================================================================
elif modulo == "📦 Gerenciar Estoque":
    st.header("📦 Gerenciamento de Peças e Estoque")
    
    aba_entrada, aba_saida, aba_excluir = st.tabs(["📥 Entradas / Reposição", "📤 Dar Saída de Peça", "❌ Excluir Item"])

    # --- ABA 1: ENTRADA E REPOSIÇÃO DE PRODUTOS ---
    with aba_entrada:
        st.subheader("📥 Entrada de Mercadorias")
        tipo_entrada = st.radio("Selecione o tipo de operação:", ["Cadastrar um produto NOVO", "Adicionar quantidade a um produto JÁ CADASTRADO"], horizontal=True)
        st.markdown("---")
        
        if tipo_entrada == "Cadastrar um produto NOVO":
            st.write("### 📝 Preencha os dados do novo item:")
            col1, col2 = st.columns(2)
            with col1:
                nome_produto = st.text_input("Descrição do Produto", placeholder="Ex: Kit de Embreagem", key="add_nome")
                codigo_original = st.text_input("Código Original / Nº Montadora", placeholder="Ex: 5Z0141025", key="add_cod_orig")
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
                st.info("Nenhum produto cadastrado para receber reposição.")
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

    # --- ABA 2: SAÍDA DE PRODUTOS ---
    with aba_saida:
        st.subheader("🛠️ Dar Baixa em Peça Utilizada")
        resposta_saida = supabase.table("estoque").select("id, descricao, quantidade").order("descricao").execute()
        dados_produtos_saida = pd.DataFrame(resposta_saida.data)
        
        if dados_produtos_saida.empty:
            st.info("Nenhum produto cadastrado no estoque para dar saída.")
        else:
            opcoes_produtos = {f"{row['descricao']} - (Disponível: {row['quantidade']})": row['id'] for index, row in dados_produtos_saida.iterrows()}
            selecao = st.selectbox("Selecione o Produto que vai sair:", list(opcoes_produtos.keys()), key="sel_saida")
            produto_id_selecionado = opcoes_produtos[selecao]
            
            qtd_atual = dados_produtos_saida[dados_produtos_saida['id'] == produto_id_selecionado]['quantidade'].values[0]
            qtd_saida = st.number_input("Quantidade de Saída", min_value=1, max_value=int(qtd_atual) if qtd_atual > 0 else 1, step=1, key="qtd_saida")
            
            if st.button("Confirmar Saída / Dar Baixa", key="btn_saida"):
                if qtd_atual <= 0:
                    st.error("Não é possível dar saída! Este produto está com estoque zerado.")
                else:
                    nova_quantidade_saida = int(qtd_atual - qtd_saida)
                    supabase.table("estoque").update({"quantidade": nova_quantidade_saida}).eq("id", produto_id_selecionado).execute()
                    st.success("Baixa realizada com sucesso!")
                    st.rerun()

    # --- ABA 3: EXCLUIR PRODUTO ---
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
                st.success("O produto foi removido com sucesso!")
                st.rerun()

    # --- RELATÓRIO DO ESTOQUE ---
    st.markdown("---")
    st.subheader("📊 Relatório Atual de Estoque")
    busca_codigo = st.text_input("🔍 Buscar por Código Original / Nº Montadora:", placeholder="Digite o código da peça...")
    
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