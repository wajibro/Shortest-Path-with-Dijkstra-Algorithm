import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import shutil

# =========================
# MEMBACA DATA EXCEL
# =========================
file_path = "/mnt/user-data/uploads/Dataset_Graph_Surabaya-3.xlsx"
df = pd.read_excel(file_path)

print("=" * 50)
print("PREVIEW DATA")
print("=" * 50)
print(df.head(10).to_string(index=False))

# =========================
# MEMBUAT DIRECTED GRAPH
# =========================
G = nx.DiGraph()

for _, row in df.iterrows():
    asal  = row['From']
    tujuan = row['To']
    jarak  = row['Distance_km']
    G.add_edge(asal, tujuan, weight=jarak)

# =========================
# INFORMASI GRAPH
# =========================
print("\n" + "=" * 50)
print("INFORMASI GRAPH")
print("=" * 50)
print(f"Jumlah Node : {G.number_of_nodes()}")
print(f"Jumlah Edge : {G.number_of_edges()}")

print("\nDaftar Lokasi:")
for i, node in enumerate(sorted(G.nodes()), 1):
    print(f"  {i:2}. {node}")

# =========================
# DIJKSTRA SHORTEST PATH
# =========================
start = "Tunjungan"
end   = "Terminal Bungurasih"

print("\n" + "=" * 50)
print(f"RUTE TERPENDEK: {start} → {end}")
print("=" * 50)

try:
    shortest_path     = nx.dijkstra_path(G, start, end, weight='weight')
    shortest_distance = nx.dijkstra_path_length(G, start, end, weight='weight')

    print("Rute:")
    for i, node in enumerate(shortest_path):
        if i < len(shortest_path) - 1:
            w = G[shortest_path[i]][shortest_path[i+1]]['weight']
            print(f"  {node}  --({w} km)-->")
        else:
            print(f"  {node}")

    print(f"\nTotal Jarak: {shortest_distance:.1f} km")

except nx.NetworkXNoPath:
    print("Tidak ada jalur yang tersedia.")
except nx.NodeNotFound as e:
    print(f"Node tidak ditemukan: {e}")

# =========================
# VISUALISASI GRAPH
# =========================
plt.figure(figsize=(20, 14))

# Layout
pos = nx.spring_layout(G, k=3.5, iterations=200, seed=42)

# Warnai node jalur terpendek
node_colors = []
for node in G.nodes():
    if node == start:
        node_colors.append('#e74c3c')      # merah = start
    elif node == end:
        node_colors.append('#2ecc71')      # hijau = end
    elif node in shortest_path:
        node_colors.append('#f39c12')      # oranye = jalur
    else:
        node_colors.append('#aed6f1')      # biru muda = biasa

# Warnai edge jalur terpendek
path_edges = list(zip(shortest_path[:-1], shortest_path[1:]))
edge_colors = ['#e74c3c' if (u, v) in path_edges else '#b0b0b0' for u, v in G.edges()]
edge_widths = [3.5 if (u, v) in path_edges else 1.0 for u, v in G.edges()]

# Gambar edge biasa
other_edges = [(u, v) for u, v in G.edges() if (u, v) not in path_edges]
nx.draw_networkx_edges(G, pos, edgelist=other_edges,
                       edge_color='#b0b0b0', width=1.0,
                       arrows=True, arrowsize=12,
                       connectionstyle='arc3,rad=0.08')

# Gambar edge jalur terpendek
nx.draw_networkx_edges(G, pos, edgelist=path_edges,
                       edge_color='#e74c3c', width=3.5,
                       arrows=True, arrowsize=20,
                       connectionstyle='arc3,rad=0.08')

# Gambar node
nx.draw_networkx_nodes(G, pos, node_color=node_colors,
                       node_size=1400, alpha=0.95)

# Label node
nx.draw_networkx_labels(G, pos, font_size=7, font_weight='bold', font_color='#1a1a2e')

# Label bobot edge (hanya jalur terpendek + semua edge)
all_edge_labels = nx.get_edge_attributes(G, 'weight')
path_edge_labels = {e: v for e, v in all_edge_labels.items() if e in path_edges}

nx.draw_networkx_edge_labels(G, pos, edge_labels=all_edge_labels,
                              font_size=6, font_color='#555555',
                              label_pos=0.3)

nx.draw_networkx_edge_labels(G, pos, edge_labels=path_edge_labels,
                              font_size=7, font_color='#c0392b',
                              font_weight='bold', label_pos=0.3)

# Legend
legend_elements = [
    mpatches.Patch(color='#e74c3c', label=f'Start: {start}'),
    mpatches.Patch(color='#2ecc71', label=f'End: {end}'),
    mpatches.Patch(color='#f39c12', label='Jalur Terpendek'),
    mpatches.Patch(color='#aed6f1', label='Node Lainnya'),
]
plt.legend(handles=legend_elements, loc='upper left', fontsize=10,
           framealpha=0.9, edgecolor='gray')

plt.title(
    f"Directed Graph Rute Surabaya\n"
    f"Dijkstra: {start} → {end}  |  Total: {shortest_distance:.1f} km  |  "
    f"{len(shortest_path)} titik",
    fontsize=14, fontweight='bold', pad=15
)

plt.axis('off')
plt.tight_layout()
plt.savefig('/home/claude/graph_surabaya.png', dpi=150, bbox_inches='tight')
print("\nGambar tersimpan.")