import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. CONFIGURAÇÃO DE CONEXÃO COM O SUPABASE ---
SUPABASE_URL = "https://lgpcpnxhkogtvhjtfwya.supabase.co"
SUPABASE_KEY = "sb_publishable_1kunRmsK4SdXCk849paiyg_1OaraKs_"

# Inicializa o cliente do Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# --- 2. CRIAÇÃO DAS ABAS NA INTERFACE ---
st.title("⚙️ Sistema de Estoque - Oficina Mecânica")
st.markdown("---")

# Nova aba "❌ Excluir Item" adicionada aqui
aba_entrada, aba_saida, aba_excluir = st.tabs(["📥 Entradas / Reposição", "📤 Dar Saída de Peça", "❌ Excluir Item"])


# --- ABA 1: ENTRADA E REPOSIÇÃO DE PRODUTOS ---
with aba_entrada:
    st.subheader("📥 Entrada de Mercadorias")
    
    tipo_entrada = st.radio(
        "Selecione o tipo de operação:",
        ["Cadastrar um produto NOVO", "Adicionar quantidade a um produto JÁ CADASTRADO"],
        horizontal=True
    )
    
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
                novo_produto = {
                    "descricao": nome_produto,
                    "codigo_original": codigo_original,
                    "marca": marca,
                    "quantidade": int(quantidade),
                    "ncm": ncm
                }
                
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


# --- ABA 3: EXCLUIR PRODUTO DO BANCO (NOVA!) ---
with aba_excluir:
    st.subheader("❌ Remover Item Definitivamente")
    st.warning("Atenção: Apagar um item excluirá todos os dados dele do banco de dados de forma permanente.")
    
    resposta_excluir = supabase.table("estoque").select("id, descricao, codigo_original").order("descricao").execute()
    dados_produtos_excluir = pd.DataFrame(resposta_excluir.data)
    
    if dados_produtos_excluir.empty:
        st.info("Nenhum produto cadastrado.")
    else:
        # Cria uma lista exibindo o nome e o código original para ter certeza do item
        opcoes_excluir = {f"{row['descricao']} (Cód: {row['codigo_original']})": row['id'] for index, row in dados_produtos_excluir.iterrows()}
        selecao_excluir = st.selectbox("Selecione o produto que deseja APAGAR:", list(opcoes_excluir.keys()), key="sel_excluir")
        id_produto_excluir = opcoes_excluir[selecao_excluir]
        
        # Botão de confirmação
        if st.button("🔥 Apagar Produto do Estoque", key="btn_deletar"):
            # Comando do Supabase para deletar a linha baseado no ID
            supabase.table("estoque").delete().eq("id", id_produto_excluir).execute()
            st.success("O produto foi removido com sucesso do banco de dados!")
            st.rerun()


# --- 4. VISUALIZAÇÃO GERAL DO ESTOQUE COM BUSCA ---
st.markdown("---")
st.subheader("📊 Relatório Atual de Estoque")

# 🔍 BARRA DE BUSCA ADICIONADA AQUI!
busca_codigo = st.text_input("🔍 Buscar por Código Original / Nº Montadora:", placeholder="Digite o código da peça para filtrar...")

# Busca tudo do Supabase para exibir na tabela final
resposta_final = supabase.table("estoque").select("*").order("descricao").execute()
dados_finais = pd.DataFrame(resposta_final.data)

if not dados_finais.empty:
    colunas_ordenadas = ["id", "codigo_original", "ncm", "descricao", "marca", "quantidade", "created_at"]
    colunas_existem = [c for c in colunas_ordenadas if c in dados_finais.columns]
    
    # Se o usuário digitou algo na barra de busca, filtramos o DataFrame
    if busca_codigo:
        # O .str.contains faz uma busca parcial, e o case=False ignora letras maiúsculas/minúsculas
        dados_finais = dados_finais[dados_finais['codigo_original'].str.contains(busca_codigo, case=False, na=False)]
        
    if dados_finais.empty:
        st.info("Nenhuma peça encontrada com esse código original.")
    else:
        st.dataframe(dados_finais[colunas_existem], use_container_width=True)
else:
    st.info("O estoque na nuvem está vazio.")