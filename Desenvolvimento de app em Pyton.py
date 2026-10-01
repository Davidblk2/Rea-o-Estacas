import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io 

# ==========================================
# MOTOR DE CÁLCULO (BACK-END)
# ==========================================
def calcular_esforcos(nk, mx, my, peso_bloco, df_estacas):
    # O peso do bloco agora vem pronto do front-end
    n_total = nk + peso_bloco
    
    x = df_estacas["Posição X (m)"].values
    y = df_estacas["Posição Y (m)"].values
    n_estacas = len(x)
    
    sum_x2 = np.sum(x**2) if np.sum(x**2) != 0 else 1.0
    sum_y2 = np.sum(y**2) if np.sum(y**2) != 0 else 1.0
    
    esforcos = []
    for i in range(n_estacas):
        parcela_n = n_total / n_estacas
        parcela_mx = (mx * y[i]) / sum_y2
        parcela_my = (my * x[i]) / sum_x2
        esforco_final = parcela_n + parcela_mx + parcela_my
        esforcos.append(esforco_final)
        
    return n_total, esforcos

# ==========================================
# INTERFACE DO USUÁRIO (FRONT-END)
# ==========================================
st.set_page_config(page_title="Dimensionamento de Estacas", layout="wide")
st.title("🏗️ Cálculo de Esforços em Estacas")
st.write("Aplicativo para calcular a distribuição de cargas usando a Hipótese do Bloco Rígido / Schiel.")
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.header("1. Esforços do Pilar")
    nk = st.number_input("Esforço Vertical Nk (kN):", value=1500.0, step=10.0)
    mx = st.number_input("Momento em X - Mx (kN.m):", value=120.0, step=5.0)
    my = st.number_input("Momento em Y - My (kN.m):", value=50.0, step=5.0)

with col2:
    st.header("2. Propriedades do Bloco")
    
    peso_direto = st.checkbox("Inserir peso do bloco diretamente (ignorar dimensões)")
    
    if peso_direto:
        peso_bloco = st.number_input("Peso do Bloco (kN):", value=100.0, step=10.0)
        formato = "Personalizado"
        # Valores padrão apenas para o gráfico não quebrar
        largura, comprimento, altura = 2.0, 2.0, 1.0
    else:
        formato = st.selectbox("Formato do Bloco", ["Retangular", "Triangular"])
        largura = st.number_input("Largura em X (m):", value=1.8, step=0.1)
        comprimento = st.number_input("Comprimento em Y (m):", value=1.8, step=0.1)
        altura = st.number_input("Altura Z (m):", value=0.8, step=0.1)
        
        peso_especifico = 25.0 # kN/m³
        if formato == "Retangular":
            peso_bloco = largura * comprimento * altura * peso_especifico
        elif formato == "Triangular":
            peso_bloco = (largura * comprimento / 2.0) * altura * peso_especifico

st.divider()
st.header("3. Coordenadas das Estacas (m)")
st.write("Edite a tabela abaixo. Pressione no '+' para adicionar mais estacas se quiser testar!")

dados_iniciais = pd.DataFrame({
    "Identificação": ["Estaca 1", "Estaca 2", "Estaca 3", "Estaca 4"],
    "Posição X (m)": [-0.6, 0.6, -0.6, 0.6],
    "Posição Y (m)": [0.6, 0.6, -0.6, -0.6]
})

tabela_estacas = st.data_editor(dados_iniciais, num_rows="dynamic", use_container_width=True)

# ==========================================
# AÇÃO DO BOTÃO E GERAÇÃO DA IMAGEM
# ==========================================
if st.button("Calcular Esforços", type="primary"):
    carga_total, resultados = calcular_esforcos(nk, mx, my, peso_bloco, tabela_estacas)
    
    st.divider()
    st.header("📊 Resultados do Dimensionamento")
    
    fig = plt.figure(figsize=(12, 6))
    
    # --- PARTE 1: O GRÁFICO (Lado Esquerdo) ---
    ax1 = fig.add_subplot(1, 2, 1)
    
    # Renderização condicional da geometria no gráfico
    if formato == "Triangular":
        pontos = [[-largura/2, -comprimento/2], [largura/2, -comprimento/2], [0, comprimento/2]]
        forma = patches.Polygon(pontos, linewidth=2, edgecolor='black', facecolor='lightgray', alpha=0.5)
    elif formato == "Personalizado" and peso_direto:
        # Se for peso direto, desenha um retângulo tracejado genérico
        forma = patches.Rectangle((-largura/2, -comprimento/2), largura, comprimento, 
                                  linewidth=2, edgecolor='gray', facecolor='none', linestyle='--', alpha=0.5)
    else:
        forma = patches.Rectangle((-largura/2, -comprimento/2), largura, comprimento, 
                                  linewidth=2, edgecolor='black', facecolor='lightgray', alpha=0.5)
        
    ax1.add_patch(forma)
    ax1.plot(0, 0, marker='+', color='black', markersize=20, markeredgewidth=2)
    
    for i in range(len(tabela_estacas)):
        px = tabela_estacas["Posição X (m)"].iloc[i]
        py = tabela_estacas["Posição Y (m)"].iloc[i]
        esforco = resultados[i]
        cor = '#2ecc71' if esforco >= 0 else '#e74c3c'
        
        circulo = patches.Circle((px, py), radius=0.15, edgecolor='black', facecolor=cor, alpha=0.9)
        ax1.add_patch(circulo)
        
        alinhamento = 'right' if px < 0 else 'left' if px > 0 else 'center'
        deslocamento_x = -0.2 if px < 0 else 0.2 if px > 0 else 0
        
        ax1.text(px + deslocamento_x, py + 0.1, f"E{i+1}: {esforco:.1f}kN", 
                 fontsize=10, color='black', fontweight='bold', ha=alinhamento, va='bottom')

    # Ajusta os limites do gráfico dinamicamente com base nas estacas ou no bloco
    limite_x = max(largura, max(abs(tabela_estacas["Posição X (m)"])) * 1.5) if len(tabela_estacas) > 0 else largura
    limite_y = max(comprimento, max(abs(tabela_estacas["Posição Y (m)"])) * 1.5) if len(tabela_estacas) > 0 else comprimento
    
    ax1.set_xlim(-limite_x, limite_x)
    ax1.set_ylim(-limite_y, limite_y)
    ax1.set_xlabel("Distância em X (m)")
    ax1.set_ylabel("Distância em Y (m)")
    ax1.set_aspect('equal', 'box')
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.axhline(0, color='black', linestyle='-', linewidth=0.5)
    ax1.axvline(0, color='black', linestyle='-', linewidth=0.5)
    ax1.set_title("Arranjo em Planta", fontsize=14, fontweight='bold', family='Arial')

    # --- PARTE 2: O RESUMO EM TEXTO (Lado Direito) ---
    ax2 = fig.add_subplot(1, 2, 2)
    ax2.axis('off')
    
    y = 0.95
    linha = 0.06
    
    def texto(x, y_pos, txt, negrito=False, cor='black'):
        peso = 'bold' if negrito else 'normal'
        ax2.text(x, y_pos, txt, fontsize=12, family='Arial', weight=peso, color=cor, transform=ax2.transAxes)

    texto(0.05, y, "MEMÓRIA DE CÁLCULO - RESUMO", negrito=True)
    y -= linha * 1.5
    
    texto(0.05, y, "[1] ESFORÇOS APLICADOS", negrito=True)
    y -= linha
    texto(0.05, y, "Força Vertical (Nk):"); texto(0.55, y, f"{nk:.2f} kN")
    y -= linha
    texto(0.05, y, "Momento em X (Mx):"); texto(0.55, y, f"{mx:.2f} kN.m")
    y -= linha
    texto(0.05, y, "Momento em Y (My):"); texto(0.55, y, f"{my:.2f} kN.m")
    y -= linha * 1.5
    
    texto(0.05, y, "[2] PROPRIEDADES DO BLOCO", negrito=True)
    y -= linha
    if peso_direto:
        texto(0.05, y, "Formato:"); texto(0.55, y, "Inserção Direta de Carga")
    else:
        texto(0.05, y, "Formato:"); texto(0.55, y, f"{formato}")
        y -= linha
        texto(0.05, y, "Dimensões:"); texto(0.55, y, f"B={largura}m, L={comprimento}m, h={altura}m")
        
    y -= linha
    texto(0.05, y, "Peso do Bloco:"); texto(0.55, y, f"{peso_bloco:.2f} kN")
    y -= linha
    texto(0.05, y, "Carga Vertical Total:"); texto(0.55, y, f"{carga_total:.2f} kN")
    y -= linha * 1.5
    
    texto(0.05, y, "[3] REAÇÕES NAS ESTACAS", negrito=True)
    y -= linha
    for i, esf in enumerate(resultados):
        texto(0.05, y, f"Estaca {i+1}:"); texto(0.55, y, f"{esf:.2f} kN")
        y -= linha
        
    y -= linha * 0.5
    if any(e < 0 for e in resultados):
        texto(0.05, y, "ATENÇÃO: Há estacas tracionadas!", negrito=True, cor='red')
    else:
        texto(0.05, y, "VERIFICAÇÃO OK: Apenas compressão.", negrito=True, cor='green')
    
    st.pyplot(fig)
    
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=300) 
    buf.seek(0)
    
    st.download_button(
        label="💾 Baixar Resumo em Imagem (PNG)",
        data=buf,
        file_name="resumo_calculo_estacas.png",
        mime="image/png"
    )
