import streamlit as st
import sqlite3
import pandas as pd

# --- 1. CONFIGURAÇÃO DO BANCO DE DADOS (SQLite) ---
conn = sqlite3.connect("estoque_oficina.db")
cursor = conn.cursor()

# Atualizado: Criando a tabela já prevendo a coluna 'codigo_original'
cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    codigo_original TEXT,
    marca TEXT,
    quantidade INTEGER,
    preco_custo REAL,
    ncm TEXT,
    cest TEXT,
    csosn TEXT,
    origem TEXT,
    peso REAL
)
""")
conn.commit()


# --- 2. CRIAÇÃO DAS ABAS NA INTERFACE ---
st.title("⚙️ Sistema de Estoque - Oficina Mecânica")
st.markdown("---")

aba_entrada, aba_saida = st.tabs(["📥 Entradas / Reposição", "📤 Dar Saída de Peça"])


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
            # NOVO CAMPO ADICIONADO AQUI!
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
                # Atualizado para incluir o codigo_original no INSERT
                cursor.execute("""
                INSERT INTO produtos (nome, codigo_original, marca, quantidade, preco_custo, ncm, cest, csosn, origem, peso)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (nome_produto, codigo_original, marca, quantidade, preco_custo, ncm, cest, csosn, origem, peso))
                conn.commit()
                st.success(f"Sucesso! O produto '{nome_produto}' foi salvo no banco de dados!")
                st.rerun()
                
    else:
        st.write("### 🔄 Reposição de Estoque Existente:")
        
        dados_produtos = pd.read_sql_query("SELECT id, nome, quantidade FROM produtos ORDER BY nome ASC", conn)
        
        if dados_produtos.empty:
            st.info("Nenhum produto cadastrado para receber reposição.")
        else:
            opcoes_entrada = {f"{row['nome']} - Atual: {row['quantidade']}": row['id'] for index, row in dados_produtos.iterrows()}
            selecao_entrada = st.selectbox("Escolha o produto que chegou na oficina:", list(opcoes_entrada.keys()), key="sel_reposicao")
            id_produto_reposicao = opcoes_entrada[selecao_entrada]
            
            qtd_novas_pecas = st.number_input("Quantidade de peças que chegaram:", min_value=1, value=1, step=1, key="qtd_reposicao")
            
            if st.button("Confirmar Entrada / Somar ao Estoque", key="btn_reposicao"):
                cursor.execute("""
                UPDATE produtos 
                SET quantidade = quantidade + ? 
                WHERE id = ?
                """, (qtd_novas_pecas, id_produto_reposicao))
                conn.commit()
                
                st.success("Estoque atualizado! As novas unidades foram somadas com sucesso.")
                st.rerun()


# --- ABA 2: SAÍDA DE PRODUTOS ---
with aba_saida:
    st.subheader("🛠️ Dar Baixa em Peça Utilizada")
    
    dados_produtos_saida = pd.read_sql_query("SELECT id, nome, quantidade FROM produtos ORDER BY nome ASC", conn)
    
    if dados_produtos_saida.empty:
        st.info("Nenhum produto cadastrado no estoque para dar saída.")
    else:
        opcoes_produtos = {f"{row['nome']} - (Disponível: {row['quantidade']})": row['id'] for index, row in dados_produtos_saida.iterrows()}
        
        selecao = st.selectbox("Selecione o Produto que vai sair:", list(opcoes_produtos.keys()), key="sel_saida")
        produto_id_selecionado = opcoes_produtos[selecao]
        
        qtd_atual = dados_produtos_saida[dados_produtos_saida['id'] == produto_id_selecionado]['quantidade'].values[0]
        
        qtd_saida = st.number_input("Quantidade de Saída", min_value=1, max_value=int(qtd_atual) if qtd_atual > 0 else 1, step=1, key="qtd_saida")
        
        if st.button("Confirmar Saída / Dar Baixa", key="btn_saida"):
            if qtd_atual <= 0:
                st.error("Não é possível dar saída! Este produto está com estoque zerado.")
            else:
                cursor.execute("""
                UPDATE produtos 
                SET quantidade = quantidade - ? 
                WHERE id = ?
                """, (qtd_saida, produto_id_selecionado))
                conn.commit()
                
                st.success("Baixa realizada com sucesso! O estoque foi atualizado.")
                st.rerun()


# --- 4. VISUALIZAÇÃO GERAL DO ESTOQUE ---
st.markdown("---")
st.subheader("📊 Relatório Atual de Estoque")

dados_finais = pd.read_sql_query("SELECT * FROM produtos ORDER BY nome ASC", conn)
if not dados_finais.empty:
    st.dataframe(dados_finais)
else:
    st.info("O estoque está vazio.")

conn.close()