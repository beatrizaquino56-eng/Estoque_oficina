import streamlit as st
import pandas as pd
from supabase import create_client

# 🔍 LINHA DE DIAGNÓSTICO TEMPORÁRIA (Adicione esta linha aqui):
st.write("Chaves que o Streamlit encontrou:", list(st.secrets.keys()))

# 1️⃣ CONEXÃO COM O SUPABASE (Puxando do seu secrets.toml)
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase = create_client(url, key)

# Importa a função de validação que está no seu arquivo validacoes.py
from validacoes import validar_valores

st.header("📦 Gerenciamento de Estoque")

# 2️⃣ CRIAÇÃO DAS ABAS DA PÁGINA
aba_entrada, aba_saida = st.tabs(["📥 Entrada / Reposição", "📤 Dar Baixa em Peça"])

# ==========================================
# ABA 1: ENTRADA E CADASTRO DE PRODUTOS
# ==========================================
with aba_entrada:
    st.write("### 📝 Preencha os dados do novo item:")
    
    col1, col2 = st.columns(2)

    with col1:
        nome_produto = st.text_input("Descrição do Produto", placeholder="Ex: Kit de Embreagem", key="add_nome").strip()
        codigo_original = st.text_input("Código Original / Nº Montadora", placeholder="Ex: 5Z0141025", key="add_cod_orig").upper().strip()
        marca = st.text_input("Marca/Fabricante", placeholder="Ex: LUK", key="add_marca").strip()
        quantidade = st.number_input("Quantidade Inicial", min_value=0, value=0, step=1, key="add_qtd")
        preco_custo = st.number_input("Preço de Custo (R$)", min_value=0.0, value=0.0, step=0.50, key="add_custo")

    with col2:
        ncm = st.text_input("Código NCM (8 dígitos)", max_chars=8, placeholder="Ex: 87082999", key="add_ncm").strip()
        cest = st.text_input("Código CEST", max_chars=9, placeholder="Ex: 16.001.00", key="add_cest").strip()
        csosn = st.text_input("Código CSOSN", max_chars=3, placeholder="Ex: 500", key="add_csosn").strip()
        origem = st.selectbox("Origem da Mercadoria", ["0 - Nacional", "1 - Estrangeira", "2 - Adquirida no Mercado Interno"], key="add_origem").strip()
        peso = st.number_input("Peso do Produto (Kg)", min_value=0.000, value=0.000, step=0.050, format="%.3f", key="add_peso")

    st.markdown("---")

    # Botão de Gravação com o Escudo de Erros ativado
    if st.button("Gravar Novo Produto", key="btn_gravar"):
        if nome_produto == "":
            st.error("⚠️ O nome do produto é obrigatório!")
        else:
            # Roda as validações customizadas do seu projeto
            valores_ok, msg_erro = validar_valores(quantidade, preco_custo)
            if not valores_ok:
                st.error(f"❌ {msg_erro}")
                st.stop()
            
            dados_produto = {
                "item": nome_produto,
                "codigo_original": codigo_original,
                "marca": marca,
                "quantidade": quantidade,
                "preco_custo": preco_custo,
                "ncm": ncm,
                "cest": cest,
                "csosn": csosn,
                "origem": origem,
                "peso": peso
            }
            
            # 🛡️ Escudo Corrigido para a tabela "estoque"
            try:
                supabase.table("estoque").insert(dados_produto).execute()
                st.success("🎉 Produto validado e cadastrado com sucesso!")
                st.rerun()
            except Exception as erro:
                print(f"--- ERRO CRÍTICO NO CADASTRO --- \n{erro}")
                st.error("⚠️ Não foi possível salvar o produto. Verifique se o nome dos campos bate com o Supabase.")

    st.markdown("---")

with st.expander("🔄 Reposição de Estoque Existente", expanded=True):
    st.write("### 🔄 Adicionar Peças ao Estoque:")
    
    # 🌟 Linhas internas avançadas corretamente (4 espaços)
    resposta_entrada = supabase.table("estoque").select("id, descricao, quantidade").order("descricao").execute()
    dados_produtos = pd.DataFrame(resposta_entrada.data)

    if dados_produtos.empty:
        st.info("Nenhum produto cadastrado para reposição.")
    else:
        # 🌟 Linhas internas do bloco else avançadas (8 espaços)
        opcoes_entrada = {f"{row['descricao']} - Ult: {row['quantidade']}": row['id'] for index, row in dados_produtos.iterrows()}
        selecao_entrada = st.selectbox("Escolha o produto que chegou:", list(opcoes_entrada.keys()), key="sel_reposicao")
        
        id_produto_reposicao = opcoes_entrada[selecao_entrada]
        qtd_atual_banco = dados_produtos[dados_produtos['id'] == id_produto_reposicao]['quantidade'].values[0]
        qtd_novas_pecas = st.number_input("Quantidade de peças:", min_value=1, value=1, step=1, key="qtd_reposicao")
        
        if st.button("Confirmar Entrada", key="btn_reposicao"):
            nova_quantidade = int(qtd_atual_banco + qtd_novas_pecas)
            
            try:
                supabase.table("estoque").update({"quantidade": nova_quantidade}).eq("id", id_produto_reposicao).execute()
                st.success("✅ Estoque Atualizado com sucesso!")
                st.rerun()
            except Exception as erro:
                print(f"--- ERRO CRÍTICO NA REPOSIÇÃO --- \n{erro}")
                st.error("⚠️ Falha ao atualizar o estoque no servidor.")
# ==========================================
# ABA 2: SAÍDA / BAIXA DE PRODUTOS
# ==========================================
with aba_saida:
    st.subheader("🛠️ Dar Baixa em Peça Utilizada")
    
    resposta_saida = supabase.table("estoque").select("id", "descricao", "quantidade").order("descricao").execute()
    dados_saida = pd.DataFrame(resposta_saida.data)
    
    if dados_saida.empty:
        st.info("Nenhum produto encontrado no estoque para dar baixa.")
    else:
        opcoes_saida = {f"{row['descricao']} - Atual: {row['quantidade']}": row['id'] for index, row in dados_saida.iterrows()}
        selecao_saida = st.selectbox("Escolha o produto retirado:", list(opcoes_saida.keys()), key="sel_baixa")
        
        id_produto_saida = opcoes_saida[selecao_saida]
        qtd_atual_saida_banco = dados_saida[dados_saida['id'] == id_produto_saida]['quantidade'].values[0]
        qtd_retirada = st.number_input("Quantidade retirada:", min_value=1, value=1, step=1, key="qtd_baixa")
        
        if st.button("Confirmar Baixa", key="btn_baixa"):
            if qtd_retirada > qtd_atual_saida_banco:
                st.error("❌ Erro: Quantidade retirada é maior do que o saldo atual do estoque!")
            else:
                nova_qtd_saida = int(qtd_atual_saida_banco - qtd_retirada)
                
                try:
                    supabase.table("estoque").update({"quantidade": nova_qtd_saida}).eq("id", id_produto_saida).execute()
                    st.success("📉 Baixa registrada com sucesso!")
                    st.rerun()
                except Exception as erro:
                    print(f"--- ERRO CRÍTICO NA BAIXA --- \n{erro}")
                    st.error("⚠️ Falha ao registrar a baixa do estoque no servidor.")