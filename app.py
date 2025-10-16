from flask import Flask, render_template, request
import pandas as pd
import plotly.express as px
import plotly.io as pio

app = Flask(__name__)

def carregar_dados(path="USP_Completa.xlsx"):
    df = pd.read_excel(path)
    df["Nascimento"] = pd.to_datetime(df["Nascimento"], errors='coerce')
    df["Início da contagem de prazo"] = pd.to_datetime(df["Início da contagem de prazo"], errors='coerce')

    referencia = df["Início da contagem de prazo"].fillna(pd.Timestamp.today())
    df["Idade"] = ((referencia - df["Nascimento"]).dt.days // 365).astype("float")
    df.loc[df["Nascimento"].isna(), "Idade"] = pd.NA

    bins = [0, 25, 30, 35, 40, 45, 50, 60, 200]
    labels = ['<25', '25-29', '30-34', '35-39', '40-44', '45-49', '50-59', '60+']
    df["Faixa Etária"] = pd.cut(df["Idade"].astype(float), bins=bins, labels=labels, right=False)
    df["Faixa Etária"] = pd.Categorical(df["Faixa Etária"], categories=labels, ordered=True)
    return df, labels

@app.route('/', methods=['GET', 'POST'])
def index():
    df, labels = carregar_dados()
    df = df[df["Curso"].isin(["Mestrado", "Doutorado"])]

    cursos = ["Todos"] + sorted(df["Curso"].dropna().unique().tolist())
    faixas = ["Todas"] + labels
    anos = ["Todos"] + sorted(df["Início da contagem de prazo"].dropna().dt.year.unique().tolist())

    form_id = request.form.get("form_id", None)

    # === GRÁFICO 1 ===
    curso1 = request.form.get("curso1", "Todos")
    faixa1 = request.form.get("faixa1", "Todas")
    df1 = df.copy()
    if curso1 != "Todos":
        df1 = df1[df1["Curso"] == curso1]
    if faixa1 != "Todas":
        df1 = df1[df1["Faixa Etária"] == faixa1]

    if df1.empty:
        fig1 = px.bar(title="Nenhum dado encontrado (Gráfico 1)")
    else:
        fig1 = px.histogram(
            df1,
            x="Faixa Etária",
            color="Curso",
            category_orders={"Faixa Etária": labels},
            barmode="group",
            title="Distribuição de Faixa Etária por Curso",
            text_auto=True,
        )
    plot_div1 = pio.to_html(fig1, full_html=False, include_plotlyjs='cdn')

    # === GRÁFICO 2 ===
    curso2 = request.form.get("curso2", "Todos")
    ano2 = request.form.get("ano2", "Todos")
    df["Ano Início"] = df["Início da contagem de prazo"].dt.year
    df2 = df.copy()
    if curso2 != "Todos":
        df2 = df2[df2["Curso"] == curso2]
    if ano2 != "Todos":
        df2 = df2[df2["Ano Início"] == int(ano2)]

    dados_ano = df2.groupby(["Ano Início", "Faixa Etária"]).size().reset_index(name="Quantidade")

    if not dados_ano.empty:
        fig2 = px.bar(
            dados_ano,
            x="Ano Início",
            y="Quantidade",
            color="Faixa Etária",
            category_orders={"Faixa Etária": labels},
            barmode="stack",
            title="Faixa Etária x Ano de Início",
        )
    else:
        fig2 = px.bar(title="Nenhum dado encontrado (Gráfico 2)")
    plot_div2 = pio.to_html(fig2, full_html=False, include_plotlyjs=False)

    return render_template(
        "index.html",
        plot_div1=plot_div1,
        plot_div2=plot_div2,
        cursos=cursos,
        faixas=faixas,
        anos=anos,
        selected_curso1=curso1,
        selected_faixa1=faixa1,
        selected_curso2=curso2,
        selected_ano2=ano2,
    )


if __name__ == '__main__':
    app.run(debug=True)
