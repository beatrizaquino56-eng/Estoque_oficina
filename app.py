import streamlit as st

# Configuração da página (deve ser sempre a primeira coisa do Streamlit)
st.set_page_config(layout="wide")

# 1. CONTROLE DE ACESSO (TELA DE LOGIN)
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

def tela_login():
    st.title("🔒 Acesso Restrito - Sistema Integrado")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if usuario == "admin" and senha == "oficina123":
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos!")

# 2. GERENCIAMENTO DE NAVEGAÇÃO
if not st.session_state["autenticado"]:
    # Se NÃO está logado, mostra apenas a tela de login e esconde o menu lateral
    pagina_login = st.Page(tela_login, title="Login", icon="🔒")
    st.navigation([pagina_login], position="hidden").run()
else:
    # Se ESTÁ logado, cria os links para os arquivos da sua pasta 'paginas'
    pg_clientes = st.Page("paginas/clientes.py", title="Painel de Clientes", icon="👥")
    pg_estoque = st.Page("paginas/estoque.py", title="Controle de Estoque", icon="📦")
    pg_orcamentos = st.Page("paginas/orcamentos.py", title="Orçamentos", icon="📄")
    
    # Executa o menu de navegação lateral automaticamente
    menu = st.navigation([pg_clientes, pg_estoque, pg_orcamentos])
    menu.run()