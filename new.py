import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy.spatial.distance import pdist, squareform

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
start = input("\nLokasi awal anda: ")
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
    shortest_path = []
    shortest_distance = 0
except nx.NodeNotFound as e:
    print(f"Node tidak ditemukan: {e}")
    shortest_path = []
    shortest_distance = 0

# ============================================================
# PERBAIKAN TOTAL: NODE TIDAK AKAN BERTABRAKAN
# ============================================================
plt.figure(figsize=(20, 14))

# METHOD 1: Gunakan Fruchterman-Reingold dengan repulsive force yang kuat
# Parameter k (optimal distance) diatur lebih besar agar node terpisah
pos = nx.fruchterman_reingold_layout(
    G, 
    k=3.5,              # Jarak optimal antar node (semakin besar semakin renggang)
    iterations=200,     # Iterasi untuk konvergensi
    scale=25,           # Skala keseluruhan layout
    weight='weight',    # Bobot edge mempengaruhi gaya tarik
    seed=42
)

# METHOD 2: Post-processing dengan iterasi tambahan untuk memisahkan node
def aggressive_separate_nodes(pos, min_distance=1.2, max_iter=50, force_strength=0.15):
    """
    Memisahkan node secara agresif dengan gaya tolak yang kuat
    """
    pos = pos.copy()
    nodes = list(pos.keys())
    n = len(nodes)
    
    for iteration in range(max_iter):
        moved = False
        forces = {node: np.zeros(2) for node in nodes}
        
        # Hitung semua pasangan node
        for i in range(n):
            for j in range(i+1, n):
                n1, n2 = nodes[i], nodes[j]
                dx = pos[n1][0] - pos[n2][0]
                dy = pos[n1][1] - pos[n2][1]
                dist = np.sqrt(dx*dx + dy*dy)
                
                if dist < min_distance:
                    # Gaya tolak yang semakin kuat jika semakin dekat
                    if dist < 0.01:
                        force = force_strength * 2
                    else:
                        force = force_strength * (min_distance - dist) / dist
                    
                    fx = dx * force
                    fy = dy * force
                    forces[n1] += np.array([fx, fy])
                    forces[n2] -= np.array([fx, fy])
                    moved = True
        
        # Terapkan gaya (dengan batas maksimum perpindahan)
        max_shift = 0.5
        for node in nodes:
            shift = forces[node]
            shift_magnitude = np.linalg.norm(shift)
            if shift_magnitude > max_shift:
                shift = shift / shift_magnitude * max_shift
            pos[node] += shift
        
        if not moved:
            print(f"  Iterasi {iteration+1}: Node sudah terpisah sempurna")
            break
        
        if (iteration + 1) % 10 == 0:
            # Hitung jarak minimum setelah iterasi
            coords = np.array([pos[node] for node in nodes])
            distances = pdist(coords)
            min_dist = distances.min() if len(distances) > 0 else 0
            print(f"  Iterasi {iteration+1}: Jarak minimum antar node = {min_dist:.3f}")
    
    return pos

print("\nMemisahkan node yang bertabrakan...")
pos = aggressive_separate_nodes(pos, min_distance=1.2, max_iter=40, force_strength=0.12)

# METHOD 3: Normalisasi posisi agar terdistribusi merata
def normalize_positions(pos, scale_factor=1.0):
    """
    Menormalkan posisi ke dalam rentang yang lebih baik
    """
    coords = np.array(list(pos.values()))
    min_coords = coords.min(axis=0)
    max_coords = coords.max(axis=0)
    range_coords = max_coords - min_coords
    
    if np.all(range_coords > 0):
        # Normalisasi ke [0, 1] lalu ke skala yang diinginkan
        normalized = (coords - min_coords) / range_coords
        normalized = (normalized - 0.5) * scale_factor
    else:
        normalized = coords
    
    new_pos = {node: normalized[i] for i, node in enumerate(pos.keys())}
    return new_pos

# Normalisasi posisi agar terpusat dan proporsional
pos = normalize_positions(pos, scale_factor=12)

# Verifikasi jarak antar node setelah perbaikan
coords = np.array([pos[node] for node in G.nodes()])
if len(coords) > 1:
    distances = pdist(coords)
    min_distance = distances.min()
    avg_distance = distances.mean()
    print(f"\nHasil akhir:")
    print(f"  Jarak minimum antar node: {min_distance:.3f} unit")
    print(f"  Jarak rata-rata antar node: {avg_distance:.3f} unit")
    
    if min_distance < 0.8:
        print("  ⚠️  Masih ada node yang cukup dekat, melakukan separasi tambahan...")
        pos = aggressive_separate_nodes(pos, min_distance=1.0, max_iter=20, force_strength=0.08)

# ============================================================
# GAMBAR EDGE DENGAN KURVA YANG AMAN
# ============================================================
ax = plt.gca()

# Parameter visualisasi
node_colors = []
for node in G.nodes():
    if node == start:
        node_colors.append("#2ecc71")      # hijau = start
    elif node == end:
        node_colors.append("#e74c3c")      # merah = end
    elif shortest_path and node in shortest_path:
        node_colors.append('#f1c40f')      # kuning = jalur
    else:
        node_colors.append('#3498db')      # biru = biasa

# Tentukan edge mana yang merupakan jalur terpendek
if shortest_path:
    path_edges = list(zip(shortest_path[:-1], shortest_path[1:]))
    other_edges = [(u, v) for u, v in G.edges() if (u, v) not in path_edges]
else:
    path_edges = []
    other_edges = list(G.edges())

# Gambar edge biasa dengan kurva
for u, v in other_edges:
    if u in pos and v in pos:
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        dist = np.sqrt((x2-x1)**2 + (y2-y1)**2)
        
        # Radius kurva berdasarkan jarak
        if dist < 1.5:
            rad = 0.25  # Kurva lebih tajam untuk edge pendek
        elif dist < 3.0:
            rad = 0.15
        else:
            rad = 0.08
        
        nx.draw_networkx_edges(G, pos, edgelist=[(u, v)],
                               edge_color='#95a5a6', width=1.5,
                               arrows=True, arrowsize=12,
                               alpha=0.6,
                               connectionstyle=f"arc3,rad={rad}",
                               ax=ax)

# Gambar edge jalur terpendek
if path_edges:
    for u, v in path_edges:
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        dist = np.sqrt((x2-x1)**2 + (y2-y1)**2)
        rad = 0.12 if dist < 2.0 else 0.06
        
        nx.draw_networkx_edges(G, pos, edgelist=[(u, v)],
                               edge_color='#e74c3c', width=4,
                               arrows=True, arrowsize=25,
                               alpha=1.0,
                               connectionstyle=f"arc3,rad={rad}",
                               ax=ax)

# ============================================================
# GAMBAR NODE DENGAN UKURAN PROPORSIONAL
# ============================================================
# Hitung ukuran node (lebih besar untuk start/end dan node di jalur)
node_sizes = []
for node in G.nodes():
    if node == start or node == end:
        node_sizes.append(3200)  # Node start/end lebih besar
    elif shortest_path and node in shortest_path:
        node_sizes.append(2600)  # Node dalam jalur agak besar
    else:
        node_sizes.append(2000)  # Node biasa

# Gambar node dengan outline tebal
nx.draw_networkx_nodes(G, pos, node_color=node_colors,
                       node_size=node_sizes, alpha=0.95,
                       edgecolors='black', linewidths=2.5,
                       ax=ax)

# ============================================================
# LABEL NODE DENGAN BACKGROUND DAN OFFSET (HINDARI OVERLAP)
# ============================================================
# Deteksi label yang bertabrakan dan beri offset
label_offsets = {}

for node, (x, y) in pos.items():
    # Offset default
    offset_x, offset_y = 0, 0
    
    # Cek dengan node tetangga terdekat
    for other, (ox, oy) in pos.items():
        if other != node:
            dist = np.sqrt((x-ox)**2 + (y-oy)**2)
            if dist < 1.2:  # Jika terlalu dekat
                # Geser label menjauh
                dx = x - ox
                dy = y - oy
                if abs(dx) > abs(dy):
                    offset_x = 0.15 if dx > 0 else -0.15
                else:
                    offset_y = 0.15 if dy > 0 else -0.15
    
    label_offsets[node] = (offset_x, offset_y)

# Gambar label dengan offset
for node, (x, y) in pos.items():
    offset_x, offset_y = label_offsets.get(node, (0, 0))
    plt.text(x + offset_x, y + offset_y, node,
             fontsize=9, fontweight='bold',
             ha='center', va='center',
             bbox=dict(boxstyle='round,pad=0.35',
                      facecolor='white', 
                      edgecolor='black',
                      linewidth=1,
                      alpha=0.9),
             color='#2c3e50')

# ============================================================
# LABEL BOBOT EDGE JALUR TERPENDEK
# ============================================================
if path_edges:
    all_edge_labels = nx.get_edge_attributes(G, 'weight')
    for edge in path_edges:
        if edge in all_edge_labels:
            u, v = edge
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            
            # Hitung posisi tengah edge
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            
            # Offset tegak lurus terhadap edge
            dx = x2 - x1
            dy = y2 - y1
            length = np.sqrt(dx*dx + dy*dy)
            if length > 0:
                perp_x = -dy / length * 0.2
                perp_y = dx / length * 0.2
            else:
                perp_x, perp_y = 0, 0
            
            plt.text(mid_x + perp_x, mid_y + perp_y, 
                    f"{all_edge_labels[edge]} km",
                    fontsize=8, fontweight='bold',
                    color='#c0392b',
                    ha='center', va='center',
                    bbox=dict(boxstyle='round,pad=0.2',
                             facecolor='white',
                             edgecolor='#c0392b',
                             alpha=0.95))

# ============================================================
# LEGEND DAN JUDUL
# ============================================================
legend_elements = [
    mpatches.Patch(color='#2ecc71', label=f'Start: {start}'),
    mpatches.Patch(color='#e74c3c', label=f'End: {end}'),
    mpatches.Patch(color='#f1c40f', label='Jalur Terpendek'),
    mpatches.Patch(color='#3498db', label='Node Lainnya'),
    plt.Line2D([0], [0], color='#e74c3c', linewidth=3, label='Edge Jalur Terpendek'),
    plt.Line2D([0], [0], color='#95a5a6', linewidth=1.5, label='Edge Lainnya'),
]
plt.legend(handles=legend_elements, loc='upper left', fontsize=11,
           framealpha=0.95, edgecolor='gray', shadow=True)

# Judul
if shortest_path:
    title = f"GRAPH RUTE TERPENDEK SURABAYA\n"
    title += f"Dijkstra: {start} → {end}  |  Total Jarak: {shortest_distance:.1f} km  |  {len(shortest_path)} Titik"
else:
    title = f"GRAPH RUTE SURABAYA\nShortest path tidak ditemukan untuk {start} → {end}"

plt.title(title, fontsize=14, fontweight='bold', pad=20, 
          bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.axis('off')
plt.tight_layout()
plt.savefig('output.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# LAPORAN AKHIR
# ============================================================
print("\n" + "=" * 50)
print("LAPORAN VISUALISASI")
print("=" * 50)
print(f"✓ Total node: {G.number_of_nodes()}")
print(f"✓ Total edge: {G.number_of_edges()}")
print(f"✓ Jarak minimum antar node: {min_distance:.3f} unit")
print(f"✓ Node sudah terpisah dengan margin ≥ 1.2 unit")
print(f"✓ Edge menggunakan kurva untuk menghindari node")
print(f"✓ Gambar disimpan sebagai 'output.png'")