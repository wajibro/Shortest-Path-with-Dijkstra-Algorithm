import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# MEMBACA DATA EXCEL
file_path = "src/Dataset_Graph_Surabaya-3.xlsx"
df = pd.read_excel(file_path)

print("=" * 50)
print("PREVIEW DATA")
print("=" * 50)
print(df.head(10).to_string(index=False))

# MEMBUAT DIRECTED GRAPH
G = nx.DiGraph()

for _, row in df.iterrows():
    asal  = row['From']
    tujuan = row['To']
    jarak  = row['Distance_km']
    G.add_edge(asal, tujuan, weight=jarak)

# INFORMASI GRAPH
print("\n" + "=" * 50)
print("INFORMASI GRAPH")
print("=" * 50)
print(f"Jumlah Node : {G.number_of_nodes()}")
print(f"Jumlah Edge : {G.number_of_edges()}")

print("\nDaftar Lokasi:")
for i, node in enumerate(sorted(G.nodes()), 1):
    print(f"  {i:2}. {node}")

# DIJKSTRA SHORTEST PATH
start = input("Lokasi awal anda: ")
end   = input("Tujuan anda: ")

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

def repulse_nodes(pos, min_dist=1.8, iterations=300):
    """
    Iteratif mendorong pasangan node yang jaraknya < min_dist
    sehingga semua node memiliki jarak minimal min_dist satu sama lain.
    """
    nodes   = list(pos.keys())
    pos_arr = {n: np.array(pos[n], dtype=float) for n in nodes}
 
    for _ in range(iterations):
        moved = False
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                a, b  = nodes[i], nodes[j]
                delta = pos_arr[a] - pos_arr[b]
                d     = np.linalg.norm(delta)
                if d < min_dist:
                    push      = (min_dist - d) / 2 + 0.01
                    direction = delta / (d + 1e-9)
                    pos_arr[a] += direction * push
                    pos_arr[b] -= direction * push
                    moved = True
        if not moved:        # sudah tidak ada yang bertabrakan
            break
 
    return {n: tuple(pos_arr[n]) for n in nodes}

# VISUALISASI GRAPH
plt.figure(figsize=(20, 14))

# Layout
pos = nx.spring_layout(G, k=3.5, iterations=200, seed=42)
pos = repulse_nodes(pos, min_dist=1.8, iterations=300)

# Warnai node jalur terpendek
node_colors = []
for node in G.nodes():
    if node == start:
        node_colors.append("#00ff00")      # merah = start
    elif node == end:
        node_colors.append("#ff0000")      # hijau = end
    elif node in shortest_path:
        node_colors.append('#f0ff00')      # oranye = jalur
    else:
        node_colors.append('#e3e3e3')      # biru muda = biasa

# Warnai edge jalur terpendek
path_edges = list(zip(shortest_path[:-1], shortest_path[1:]))
edge_colors = ['#e74c3c' if (u, v) in path_edges else '#b0b0b0' for u, v in G.edges()]
edge_widths = [3.5 if (u, v) in path_edges else 1.0 for u, v in G.edges()]

# Gambar edge biasa
other_edges = [(u, v) for u, v in G.edges() if (u, v) not in path_edges]
nx.draw_networkx_edges(G, pos, edgelist=other_edges,
                       edge_color='#b0b0b0', width=1.0,
                       arrows=True, arrowsize=12)

# Gambar edge jalur terpendek
nx.draw_networkx_edges(G, pos, edgelist=path_edges,
                       edge_color='#0000ff', width=2,
                       arrows=True, arrowsize=30)

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
    mpatches.Patch(color='#00ff00', label=f'Start: {start}'),
    mpatches.Patch(color='#ff0000', label=f'End: {end}'),
    mpatches.Patch(color='#f0ff00', label='Jalur Terpendek'),
    mpatches.Patch(color='#e3e3e3', label='Node Lainnya'),
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
plt.savefig('output.png')
plt.show()