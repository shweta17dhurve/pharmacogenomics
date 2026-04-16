from flask import Flask, render_template, request, send_file
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx

app = Flask(__name__)


def load_data():
import os

file_path = os.path.join("data", "dataset.xlsx")
df = pd.read_excel(file_path, engine="openpyxl")


@app.route("/")
def home():
    data = load_data()

    return render_template(
        "index.html",
        total_genes=data["Target Gene"].nunique(),
        total_drugs=data["Drug Name"].nunique(),
        total_interactions=len(data)
    )


@app.route("/search", methods=["POST"])
def search():
    data = load_data()
    query = request.form["query"].strip()

    # Search by exact drug first
    drug_data = data[data["Drug Name"].astype(str).str.lower() == query.lower()]

    # If no exact drug match, do broader search
    if drug_data.empty:
        drug_data = data[
            data.apply(
                lambda row: row.astype(str).str.contains(query, case=False, na=False).any(),
                axis=1
            )
        ]

    if drug_data.empty:
        return render_template(
            "index.html",
            total_genes=data["Target Gene"].nunique(),
            total_drugs=data["Drug Name"].nunique(),
            total_interactions=len(data),
            message="No result found for your search."
        )

    row = drug_data.iloc[0]

    # Bar graph
    fig_bar = px.bar(
        drug_data,
        x="Target Gene",
        y="Drug Name",
        color="Disease",
        title="Gene–Drug Interaction Visualization"
    )
    fig_bar.update_layout(height=420)
    bar_graph = fig_bar.to_html(full_html=False)

    # Network graph
    G = nx.from_pandas_edgelist(drug_data, "Target Gene", "Drug Name")
    pos = nx.spring_layout(G, seed=42)

    edge_x = []
    edge_y = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(width=1),
        hoverinfo="none"
    )

    node_x = []
    node_y = []
    text = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        text.append(node)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=text,
        textposition="top center",
        hoverinfo="text",
        marker=dict(size=16)
    )

    fig_network = go.Figure(data=[edge_trace, node_trace])
    fig_network.update_layout(
        title="Gene–Drug Interaction Network",
        showlegend=False,
        height=460,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    network_graph = fig_network.to_html(full_html=False)

    # Related genes from result
    related_genes = drug_data["Target Gene"].dropna().astype(str).unique().tolist()

    return render_template(
        "drug.html",
        drug=row.get("Drug Name", ""),
        disease=row.get("Disease", ""),
        drug_class=row.get("Drug Class", ""),
        gene=row.get("Target Gene", ""),
        gene_full=row.get("Gene Full Name", ""),
        clinical=row.get("Clinical Significance", ""),
        response=row.get("Drug Response", ""),
        mechanism=row.get("Mechanism of Action", ""),
        reference=row.get("Reference_Paper", ""),
        related_genes=related_genes,
        bar_graph=bar_graph,
        network_graph=network_graph,
        recommendation=None
    )


@app.route("/calculate-dose", methods=["POST"])
def calculate_dose():
    data = load_data()

    drug = request.form["drug"]
    genotype = request.form["genotype"]
    age = int(request.form["age"])
    weight = int(request.form["weight"])

    # reload matching drug rows
    drug_data = data[data["Drug Name"].astype(str).str.lower() == drug.lower()]

    if drug_data.empty:
        return render_template(
            "index.html",
            total_genes=data["Target Gene"].nunique(),
            total_drugs=data["Drug Name"].nunique(),
            total_interactions=len(data),
            message="Drug not found for dose calculation."
        )

    row = drug_data.iloc[0]

    recommendation = ""

    if genotype == "poor":
        recommendation = "Low dose recommended due to poor metabolizer genotype."
    elif genotype == "intermediate":
        recommendation = "Moderate dose recommended due to intermediate metabolizer status."
    else:
        recommendation = "Standard dose recommended for normal metabolizer status."

    if age > 65:
        recommendation += " Elderly patients may require additional dose reduction."

    if weight < 60:
        recommendation += " Lower body weight suggests a safer lower dose."

    # rebuild graphs
    fig_bar = px.bar(
        drug_data,
        x="Target Gene",
        y="Drug Name",
        color="Disease",
        title="Gene–Drug Interaction Visualization"
    )
    fig_bar.update_layout(height=420)
    bar_graph = fig_bar.to_html(full_html=False)

    G = nx.from_pandas_edgelist(drug_data, "Target Gene", "Drug Name")
    pos = nx.spring_layout(G, seed=42)

    edge_x = []
    edge_y = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(width=1),
        hoverinfo="none"
    )

    node_x = []
    node_y = []
    text = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        text.append(node)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=text,
        textposition="top center",
        hoverinfo="text",
        marker=dict(size=16)
    )

    fig_network = go.Figure(data=[edge_trace, node_trace])
    fig_network.update_layout(
        title="Gene–Drug Interaction Network",
        showlegend=False,
        height=460,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    network_graph = fig_network.to_html(full_html=False)

    related_genes = drug_data["Target Gene"].dropna().astype(str).unique().tolist()

    return render_template(
        "drug.html",
        drug=row.get("Drug Name", ""),
        disease=row.get("Disease", ""),
        drug_class=row.get("Drug Class", ""),
        gene=row.get("Target Gene", ""),
        gene_full=row.get("Gene Full Name", ""),
        clinical=row.get("Clinical Significance", ""),
        response=row.get("Drug Response", ""),
        mechanism=row.get("Mechanism of Action", ""),
        reference=row.get("Reference_Paper", ""),
        related_genes=related_genes,
        bar_graph=bar_graph,
        network_graph=network_graph,
        recommendation=recommendation
    )


@app.route("/genes")
def genes():
    data = load_data()
    gene_list = sorted(data["Target Gene"].dropna().astype(str).unique().tolist())
    return render_template("genes.html", genes=gene_list)


@app.route("/drugs")
def drugs():
    data = load_data()
    drug_list = sorted(data["Drug Name"].dropna().astype(str).unique().tolist())
    return render_template("drugs.html", drugs=drug_list)


@app.route("/dashboard")
def dashboard():
    data = load_data()
    return render_template(
        "dashboard.html",
        total_genes=data["Target Gene"].nunique(),
        total_drugs=data["Drug Name"].nunique(),
        total_interactions=len(data)
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/guide")
def guide():
    return render_template("guide.html")


@app.route("/download")
def download():
    return send_file("data/dataset.xlsx", as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
