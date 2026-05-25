import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# =========================
# MEMBACA DATA EXCEL
# =========================
file_path = "src/Dataset_Graph_Surabaya-3.xlsx"

# Ganti sesuai nama sheet di Excel
df = pd.read_excel(file_path)

print(df.head())

# =========================
# MEMBUAT DIRECTED GRAPH
# =========================
G = nx.DiGraph()

# Misal kolom:
# From | To | Distance_km

for index, row in df.iterrows():
    asal = row['From']
    tujuan = row['To']
    jarak = row['Distance_km']

    G.add_edge(asal, tujuan, weight=jarak)

# =========================
# INFORMASI GRAPH
# =========================
print("Jumlah Node :", G.number_of_nodes())
print("Jumlah Edge :", G.number_of_edges())

# =========================
# MENAMPILKAN SEMUA NODE
# =========================
print("\nDaftar Lokasi:")
for node in G.nodes():
    print("-", node)

# =========================
# DIJKSTRA SHORTEST PATH
# =========================
start = input("Masukkan lokasi awal: ")
end = input("Masukkan lokasi tujuan: ")

try:
    shortest_path = nx.dijkstra_path(G, start, end, weight='weight')
    shortest_distance = nx.dijkstra_path_length(G, start, end, weight='weight')

    print("\nRute Terpendek:")
    print(" -> ".join(shortest_path))

    print(f"\nTotal Jarak: {shortest_distance} km")

except nx.NetworkXNoPath:
    print("Tidak ada jalur yang tersedia.")

except nx.NodeNotFound:
    print("Node tidak ditemukan.")

# =========================
# VISUALISASI GRAPH
# =========================
plt.figure(figsize=(14,10))

pos = nx.spring_layout(G, k=2.0, iterations=100)

nx.draw(
    G,
    pos,
    with_labels=True,
    node_color='lightblue',
    node_size=1200,
    font_size=8,
    arrows=True
)

edge_labels = nx.get_edge_attributes(G, 'weight')

nx.draw_networkx_edge_labels(
    G,
    pos,
    edge_labels=edge_labels,
    font_size=7
)

plt.title("Directed Graph Rute Surabaya")
plt.show()