import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import sys

# ============================================================
# KONFIGURASI
# ============================================================
FILE_PATH        = "src/Dataset_Graph_Surabaya-3.xlsx"
COLUMN_FROM      = "From"
COLUMN_TO        = "To"
COLUMN_DISTANCE  = "Distance_km"
COLUMN_DIRECTION = "Direction" 

# ============================================================
# MEMBACA DATA EXCEL
# ============================================================
print("=" * 60)
print("        SISTEM RUTE TERPENDEK KOTA SURABAYA")
print("=" * 60)

try:
    df = pd.read_excel(FILE_PATH)
except FileNotFoundError:
    print(f"\n✗ File tidak ditemukan: {FILE_PATH}")
    sys.exit(1)

# --- Validasi kolom wajib ---
required_cols = [COLUMN_FROM, COLUMN_TO, COLUMN_DISTANCE, COLUMN_DIRECTION]
missing_cols  = [c for c in required_cols if c not in df.columns]
if missing_cols:
    print(f"\n✗ Kolom berikut tidak ditemukan di Excel: {missing_cols}")
    print(f"  Kolom yang tersedia: {df.columns.tolist()}")
    print(f"\n  Pastikan Excel memiliki kolom: {required_cols}")
    sys.exit(1)

# --- Validasi nilai kolom Direction ---
invalid_dir = df[~df[COLUMN_DIRECTION].isin([1, 2])]
if not invalid_dir.empty:
    print(f"\n✗ Nilai tidak valid pada kolom '{COLUMN_DIRECTION}':")
    print(invalid_dir[[COLUMN_FROM, COLUMN_TO, COLUMN_DIRECTION]].to_string(index=True))
    print("\n  Nilai harus 1 (satu arah) atau 2 (dua arah).")
    sys.exit(1)

# --- Validasi tidak ada nilai kosong ---
null_rows = df[df[required_cols].isnull().any(axis=1)]
if not null_rows.empty:
    print(f"\n✗ Terdapat nilai kosong pada baris: {null_rows.index.tolist()}")
    sys.exit(1)

print("\n[ PREVIEW DATA ]")
print(df.head(10).to_string(index=False))
print(f"\n  Total baris data : {len(df)}")
print(f"  Kolom Direction  : ✓ ditemukan")
print(f"  Baris 1-arah     : {(df[COLUMN_DIRECTION] == 1).sum()}")
print(f"  Baris 2-arah     : {(df[COLUMN_DIRECTION] == 2).sum()}")

# ============================================================
# MEMBUAT DIRECTED GRAPH
# ============================================================
G = nx.DiGraph()

for _, row in df.iterrows():
    asal      = str(row[COLUMN_FROM]).strip()
    tujuan    = str(row[COLUMN_TO]).strip()
    jarak     = float(row[COLUMN_DISTANCE])
    direction = int(row[COLUMN_DIRECTION])

    # Tambah edge A → B (selalu)
    G.add_edge(asal, tujuan, weight=jarak, direction=direction, one_way=(direction == 1))

    # Jika direction=2, tambah edge balik B → A
    if direction == 2:
        G.add_edge(tujuan, asal, weight=jarak, direction=direction, one_way=False)

# ============================================================
# INFORMASI GRAPH
# ============================================================
total_edges   = G.number_of_edges()
one_way_edges = [(u, v) for u, v, d in G.edges(data=True) if d['one_way']]
two_way_edges = [(u, v) for u, v, d in G.edges(data=True) if not d['one_way']]
one_way_count = len(one_way_edges)
two_way_count = len(two_way_edges)

dead_ends = [n for n in G.nodes() if G.out_degree(n) == 0]
no_entry  = [n for n in G.nodes() if G.in_degree(n) == 0]

print("\n" + "=" * 60)
print("[ INFORMASI GRAPH ]")
print("=" * 60)
print(f"  Jumlah Node         : {G.number_of_nodes()}")
print(f"  Jumlah Edge Total   : {total_edges}")
print(f"  ├─ Edge 1 Arah      : {one_way_count}")
print(f"  └─ Edge 2 Arah      : {two_way_count}")

if dead_ends:
    print(f"\n  ⚠ Dead End (tidak ada jalan keluar):")
    for n in dead_ends:
        print(f"      - {n}")

if no_entry:
    print(f"\n  ⚠ Source Only (tidak bisa dicapai dari mana pun):")
    for n in no_entry:
        print(f"      - {n}")

print("\n  Daftar Lokasi:")
all_nodes = sorted(G.nodes())
for i, node in enumerate(all_nodes, 1):
    out_d = G.out_degree(node)
    in_d  = G.in_degree(node)
    flag  = " ⚠ dead end"    if out_d == 0 else \
            " ⚠ source only" if in_d  == 0 else ""
    print(f"    {i:2}. {node}{flag}")

# ============================================================
# INPUT PENGGUNA
# ============================================================
print()
start = input("Lokasi awal anda  : ").strip()
end   = input("Tujuan anda       : ").strip()

# Validasi input ada di graph
for label, node in [("Lokasi awal", start), ("Tujuan", end)]:
    if node not in G.nodes():
        close = [n for n in G.nodes() if node.lower() in n.lower()]
        print(f"\n✗ {label} '{node}' tidak ditemukan.")
        if close:
            print(f"  Maksud anda mungkin: {close}")
        sys.exit(1)

print("\n" + "=" * 60)
print(f"  RUTE TERPENDEK: {start} → {end}")
print("=" * 60)

# ============================================================
# DIJKSTRA SHORTEST PATH
# ============================================================
shortest_path     = None
shortest_distance = None
path_edges        = []

try:
    shortest_path     = nx.dijkstra_path(G, start, end, weight='weight')
    shortest_distance = nx.dijkstra_path_length(G, start, end, weight='weight')
    path_edges        = list(zip(shortest_path[:-1], shortest_path[1:]))

    print("  Rute:")
    for i, node in enumerate(shortest_path):
        if i < len(shortest_path) - 1:
            nxt      = shortest_path[i + 1]
            w        = G[node][nxt]['weight']
            is_1way  = G[node][nxt]['one_way']
            arah_tag = "[1 ARAH]" if is_1way else "[2 ARAH]"
            print(f"    {node:<22} --( {w:4.1f} km | {arah_tag} )-->")
        else:
            print(f"    {node}")

    print(f"\n  Total Jarak  : {shortest_distance:.1f} km")
    print(f"  Jumlah Titik : {len(shortest_path)}")

except nx.NetworkXNoPath:
    print("  ✗ Tidak ada jalur yang tersedia.")
    print(f"\n  Catatan: {one_way_count} edge bersifat 1 arah.")
    print("  Jalur 1 arah hanya bisa dilalui searah sesuai data Excel.")

    # Cek rute terbalik
    try:
        rev_path = nx.dijkstra_path(G, end, start, weight='weight')
        rev_dist = nx.dijkstra_path_length(G, end, start, weight='weight')
        print(f"\n  ℹ Rute TERBALIK ({end} → {start}) tersedia: {rev_dist:.1f} km")
        print(f"    Jalur: {' → '.join(rev_path)}")
    except nx.NetworkXNoPath:
        print(f"  ℹ Rute terbalik ({end} → {start}) juga tidak tersedia.")

# ============================================================
# FUNGSI REPULSE NODE
# ============================================================
def repulse_nodes(pos, min_dist=1.8, iterations=300):
    nodes   = list(pos.keys())
    pos_arr = {n: np.array(pos[n], dtype=float) for n in nodes}

    for _ in range(iterations):
        moved = False
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                a, b   = nodes[i], nodes[j]
                delta  = pos_arr[a] - pos_arr[b]
                d      = np.linalg.norm(delta)
                if d < min_dist:
                    push      = (min_dist - d) / 2 + 0.01
                    direction = delta / (d + 1e-9)
                    pos_arr[a] += direction * push
                    pos_arr[b] -= direction * push
                    moved = True
        if not moved:
            break

    return {n: tuple(pos_arr[n]) for n in nodes}

# ============================================================
# VISUALISASI GRAPH
# ============================================================
plt.figure(figsize=(22, 15))
ax = plt.gca()
ax.set_facecolor("#f8f9fa")
plt.gcf().patch.set_facecolor("#f8f9fa")

pos = nx.spring_layout(G, k=3.5, iterations=200, seed=42)
pos = repulse_nodes(pos, min_dist=1.8, iterations=300)

# --- Warna Node ---
node_colors = []
for node in G.nodes():
    if node == start and shortest_path:
        node_colors.append("#2ecc71")   # hijau  = start
    elif node == end and shortest_path:
        node_colors.append("#e74c3c")   # merah  = end
    elif shortest_path and node in shortest_path:
        node_colors.append("#f1c40f")   # kuning = jalur
    elif G.out_degree(node) == 0:
        node_colors.append("#fd79a8")   # pink   = dead end
    elif G.in_degree(node) == 0:
        node_colors.append("#a29bfe")   # ungu   = source only
    else:
        node_colors.append("#dfe6e9")   # abu    = biasa

# --- Pisahkan Edge ---
edges_1way_npath = [(u, v) for u, v, d in G.edges(data=True)
                    if d['one_way'] and (u, v) not in path_edges]
edges_2way_npath = [(u, v) for u, v, d in G.edges(data=True)
                    if not d['one_way'] and (u, v) not in path_edges]

# Gambar edge 2 arah (abu, solid)
nx.draw_networkx_edges(G, pos, edgelist=edges_2way_npath,
                       edge_color='#95a5a6', width=1.2,
                       arrows=True, arrowsize=12,
                       connectionstyle='arc3,rad=0.08')

# Gambar edge 1 arah (oranye, putus-putus)
nx.draw_networkx_edges(G, pos, edgelist=edges_1way_npath,
                       edge_color='#e67e22', width=1.3,
                       arrows=True, arrowsize=14,
                       style='dashed',
                       connectionstyle='arc3,rad=0.08')

# Gambar edge jalur terpendek (biru tebal)
if path_edges:
    nx.draw_networkx_edges(G, pos, edgelist=path_edges,
                           edge_color='#2980b9', width=4.0,
                           arrows=True, arrowsize=32,
                           connectionstyle='arc3,rad=0.08')

# Gambar node
nx.draw_networkx_nodes(G, pos, node_color=node_colors,
                       node_size=1500, alpha=0.95,
                       linewidths=1.5, edgecolors='#636e72')

# Label node
nx.draw_networkx_labels(G, pos, font_size=6.5,
                        font_weight='bold', font_color='#2d3436')

# Label bobot semua edge
all_edge_labels = nx.get_edge_attributes(G, 'weight')
nx.draw_networkx_edge_labels(G, pos, edge_labels=all_edge_labels,
                              font_size=5.5, font_color='#636e72',
                              label_pos=0.35, bbox=dict(alpha=0))

# Label bobot jalur terpendek (lebih besar, biru)
if path_edges:
    path_edge_labels = {e: v for e, v in all_edge_labels.items() if e in path_edges}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=path_edge_labels,
                                  font_size=7.5, font_color='#1a5276',
                                  font_weight='bold', label_pos=0.35,
                                  bbox=dict(boxstyle='round,pad=0.2',
                                            facecolor='#d6eaf8', alpha=0.8))

# --- Legend ---
legend_elements = [
    mpatches.Patch(color='#2ecc71', label=f'Start : {start}'),
    mpatches.Patch(color='#e74c3c', label=f'End   : {end}'),
    mpatches.Patch(color='#f1c40f', label='Node Jalur Terpendek'),
    mpatches.Patch(color='#dfe6e9', label='Node Biasa',
                   linewidth=1, edgecolor='#636e72'),
    mpatches.Patch(color='#fd79a8', label='Node Dead End'),
    mpatches.Patch(color='#a29bfe', label='Node Source Only'),
    mpatches.Patch(color='#2980b9', label='Edge Jalur Terpendek'),
    mpatches.Patch(color='#e67e22', label='Edge 1 Arah (putus-putus)'),
    mpatches.Patch(color='#95a5a6', label='Edge 2 Arah (solid)'),
]
plt.legend(handles=legend_elements, loc='upper left',
           fontsize=9, framealpha=0.93,
           edgecolor='#b2bec3', fancybox=True)

# --- Judul ---
if shortest_path:
    title = (
        f"Directed Graph Rute Surabaya\n"
        f"Dijkstra: {start} → {end}  |  "
        f"Jarak: {shortest_distance:.1f} km  |  "
        f"{len(shortest_path)} titik  |  "
        f"1-arah: {one_way_count}  2-arah: {two_way_count}"
    )
else:
    title = (
        f"Directed Graph Rute Surabaya\n"
        f"Rute tidak ditemukan: {start} → {end}  |  "
        f"1-arah: {one_way_count}  2-arah: {two_way_count}"
    )

plt.title(title, fontsize=13, fontweight='bold', pad=20,
          color='#2d3436', loc='center')
plt.axis('off')
plt.tight_layout()
plt.savefig('output.png', dpi=150, bbox_inches='tight',
            facecolor='#f8f9fa')
print("\n  Visualisasi disimpan ke: output.png")
plt.show()