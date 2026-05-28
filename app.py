import streamlit as st

st.title("⚙️ Sistema de Estoque - Oficina Mecânica")
st.markdown("---")
st.subheader("📦 Cadastro de Novo Produto")

col1, col2 = st.columns(2)

with col1:
    nome_produto = st.text_input("Descrição do Produto", placeholder="Ex: Kit de Embreagem")
    marca = st.text_input("Marca/Fabricante", placeholder="Ex: LUK")
    quantidade = st.number_input("Quantidade Inicial", min_value=0, value=0, step=1)
    preco_custo = st.number_input("Preço de Custo (R$)", min_value=0.0, value=0.0, step=0.50)

with col2:
    cest = st.text_input("Código CEST", max_chars=9, placeholder="Ex: 16.001.00")
    csosn = st.text_input("Código CSOSN", max_chars=3, placeholder="Ex: 500")
    origem = st.selectbox("Origem da Mercadoria", ["0 - Nacional", "1 - Estrangeira", "2 - Adquirida no Mercado Interno"])
    peso = st.number_input("Peso do Produto (Kg)", min_value=0.000, value=0.000, step=0.050, format="%.3f")

if st.button("Gravar Produto no Estoque"):
    st.success(f"Sucesso! O produto '{nome_produto}' foi registrado.")