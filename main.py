import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox

# ─────────────────────────────────────────────
#  WARNA & TEMA
# ─────────────────────────────────────────────
BG_DARK      = "#0f1117"
BG_PANEL     = "#1a1d27"
BG_CARD      = "#22263a"
ACCENT       = "#4f9eff"
ACCENT2      = "#00e5a0"
TEXT_PRIMARY = "#e8eaf0"
TEXT_MUTED   = "#7a7f99"
BORDER       = "#000000"
RED          = "#ff5252"
YELLOW       = "#ffd740"
GREEN        = "#69ff47"

NODE_DEFAULT  = "#3a3f5c"
NODE_PATH     = "#4f9eff"
NODE_START    = "#00d700"
NODE_END      = "#ff5252"
EDGE_DEFAULT  = "#3a3f5c"
EDGE_PATH     = "#4f9eff"
# ─────────────────────────────────────────────
#  LOAD DATA & BUILD GRAPH
# ─────────────────────────────────────────────
FILE_PATH = "src/Dataset_Graph_Surabaya.xlsx"

try:
    df = pd.read_excel(FILE_PATH)
except FileNotFoundError:
    print("error: data excel tidak ditemukan")

G = nx.DiGraph()
for _, row in df.iterrows():
    u, v, w = row['From'], row['To'], row['Distance_km']
    G.add_edge(u, v, weight=w)
    G.add_edge(v, u, weight=w)

NODES = sorted(G.nodes())

# ─────────────────────────────────────────────
#  LAYOUT GRAPH
# ─────────────────────────────────────────────
def repulse_nodes(pos, min_dist=1.8, iterations=300):
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
        if not moved:
            break
    return {n: tuple(pos_arr[n]) for n in nodes}

POS = nx.spring_layout(G, k=3.5, iterations=500, seed=42)
POS = repulse_nodes(POS, min_dist=1.8, iterations=500)

# ─────────────────────────────────────────────
#  DRAW GRAPH
# ─────────────────────────────────────────────
def draw_graph(ax, start=None, end=None, shortest_path=None, shortest_distance=None):
    ax.clear()
    ax.set_facecolor(BG_DARK)

    path_edges = []
    if shortest_path:
        path_edges = list(zip(shortest_path[:-1], shortest_path[1:]))

    other_edges = [(u, v) for u, v in G.edges() if (u, v) not in path_edges]

    # Edge biasa
    nx.draw_networkx_edges(
        G, POS, ax=ax, edgelist=other_edges,
        edge_color=EDGE_DEFAULT, width=1.0,
        arrows=True, arrowsize=8,
        connectionstyle='arc3,rad=0.12',
    )

    # Edge jalur terpendek dengan stroke hitam 
    if path_edges:
        nx.draw_networkx_edges(
            G, POS, ax=ax, edgelist=path_edges,
            edge_color=BORDER, width=3.0,
            arrows=True, arrowsize=18,
            connectionstyle='arc3,rad=0.12',
        )
        # Kedua: edge berwarna di atasnya
        nx.draw_networkx_edges(
            G, POS, ax=ax, edgelist=path_edges,
            edge_color=EDGE_PATH, width=2.0,
            arrows=True, arrowsize=18,
            connectionstyle='arc3,rad=0.12',
        )

    # Warna node
    node_colors = []
    for node in G.nodes():
        if node == start:
            node_colors.append(NODE_START)
        elif node == end:
            node_colors.append(NODE_END)
        elif shortest_path and node in shortest_path:
            node_colors.append(NODE_PATH)
        else:
            node_colors.append(NODE_DEFAULT)

    nx.draw_networkx_nodes(
        G, POS, ax=ax,
        node_color=node_colors, node_size=900, alpha=0.95,
        linewidths=1.5, edgecolors=BORDER,
    )

    nx.draw_networkx_labels(
        G, POS, ax=ax,
        font_size=6, font_weight='bold', font_color=TEXT_PRIMARY,
    )

    # Label bobot (deduplikasi A↔B)
    all_labels = nx.get_edge_attributes(G, 'weight')
    seen, dedup = set(), {}
    for (u, v), w in all_labels.items():
        pair = frozenset([u, v])
        if pair not in seen:
            dedup[(u, v)] = w
            seen.add(pair)

    path_labels = {e: w for e, w in dedup.items() if e in path_edges}

    nx.draw_networkx_edge_labels(
        G, POS, ax=ax, edge_labels=dedup,
        font_size=5, font_color=BG_DARK, label_pos=0.3,
    )
    if path_labels:
        nx.draw_networkx_edge_labels(
            G, POS, ax=ax, edge_labels=path_labels,
            font_size=6, font_color=ACCENT, font_weight='bold', label_pos=0.3,
        )

    # Legend
    legend_items = [mpatches.Patch(color=NODE_DEFAULT, label='Node Biasa')]
    if start:
        legend_items.insert(0, mpatches.Patch(color=NODE_START, label=f'Start: {start}'))
    if end:
        legend_items.insert(1, mpatches.Patch(color=NODE_END,   label=f'End: {end}'))
    if shortest_path:
        legend_items.insert(2, mpatches.Patch(color=NODE_PATH,  label='Jalur Terpendek'))

    ax.legend(
        handles=legend_items, loc='upper left',
        fontsize=8, framealpha=0.85,
        facecolor=BG_PANEL, edgecolor=BORDER,
        labelcolor=TEXT_PRIMARY,
    )

    # Judul
    if shortest_path and shortest_distance is not None:
        title = (f"Dijkstra: {start} → {end}   |   "
                 f"Total: {shortest_distance:.1f} km   |   "
                 f"{len(shortest_path)} titik")
    else:
        title = "Central Surabaya Road Network"

    ax.set_title(title, color=TEXT_PRIMARY, fontsize=10, fontweight='bold', pad=10)
    ax.axis('off')


# ─────────────────────────────────────────────
#  TKINTER APP
# ─────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Shortest Path Dijkstra Algorithm - Central Surabaya Road Network")
        self.configure(bg=BG_DARK)
        self.state('zoomed')   # mulai maximized

        self._shortest_path     = None
        self._shortest_distance = None
        self._start             = None
        self._end               = None

        self._build_ui()
        self._initial_draw()

    # ── UI Layout ──────────────────────────────
    def _build_ui(self):
        # ── Root grid
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # ── Panel Kiri
        panel = tk.Frame(self, bg=BG_PANEL, width=300)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_propagate(False)
        panel.columnconfigure(0, weight=1)

        # Judul panel
        tk.Label(
            panel, text="🗺 Panel Navigasi", bg=BG_PANEL, fg=ACCENT,
            font=("Courier New", 10, "bold"), pady=18,
        ).grid(row=0, column=0, sticky="ew")

        self._divider(panel, 1)

        # Info graph
        info_card = tk.Frame(panel, bg=BG_CARD, padx=14, pady=10)
        info_card.grid(row=2, column=0, sticky="ew", padx=14, pady=(10, 4))
        info_card.columnconfigure(1, weight=1)

        tk.Label(info_card, text="Node", bg=BG_CARD, fg=TEXT_MUTED,
                 font=("Courier New", 8)).grid(row=0, column=0, sticky="w")
        tk.Label(info_card, text=str(G.number_of_nodes()), bg=BG_CARD, fg=ACCENT2,
                 font=("Courier New", 8, "bold")).grid(row=0, column=1, sticky="e")

        tk.Label(info_card, text="Edge", bg=BG_CARD, fg=TEXT_MUTED,
                 font=("Courier New", 8)).grid(row=1, column=0, sticky="w")
        tk.Label(info_card, text=str(G.number_of_edges()), bg=BG_CARD, fg=ACCENT2,
                 font=("Courier New", 8, "bold")).grid(row=1, column=1, sticky="e")

        # Lokasi awal
        self._label(panel, 3, "Lokasi Awal")
        self.cb_start = self._combobox(panel, 4)

        # Lokasi tujuan
        self._label(panel, 5, "Tujuan")
        self.cb_end = self._combobox(panel, 6)

        # Tombol cari
        btn_find = tk.Button(
            panel, text="CARI RUTE TERPENDEK",
            bg=ACCENT, fg=BG_DARK, font=("Courier New", 10, "bold"),
            activebackground="#3a8aee", activeforeground=BG_DARK,
            relief="flat", cursor="hand2", pady=10,
            command=self._find_route,
        )
        btn_find.grid(row=7, column=0, sticky="ew", padx=14, pady=(16, 6))

        # Tombol reset
        btn_reset = tk.Button(
            panel, text="RESET",
            bg=BG_CARD, fg=TEXT_MUTED, font=("Courier New", 9),
            activebackground=BORDER, activeforeground=TEXT_PRIMARY,
            relief="flat", cursor="hand2", pady=7,
            command=self._reset,
        )
        btn_reset.grid(row=8, column=0, sticky="ew", padx=14, pady=(0, 12))

        self._divider(panel, 9)

        # Hasil rute
        tk.Label(
            panel, text="HASIL RUTE", bg=BG_PANEL, fg=ACCENT,
            font=("Courier New", 10, "bold"), pady=10,
        ).grid(row=10, column=0, sticky="w", padx=14)

        result_frame = tk.Frame(panel, bg=BG_CARD, padx=10, pady=10)
        result_frame.grid(row=11, column=0, sticky="nsew", padx=14, pady=(0, 14))
        result_frame.columnconfigure(0, weight=1)
        panel.rowconfigure(11, weight=1)

        self.txt_result = tk.Text(
            result_frame, bg=BG_CARD, fg=TEXT_PRIMARY,
            font=("Courier New", 8), relief="flat",
            wrap="word", state="disabled",
            insertbackground=ACCENT, selectbackground=ACCENT,
        )
        self.txt_result.grid(row=0, column=0, sticky="nsew")
        result_frame.rowconfigure(0, weight=1)

        sb = tk.Scrollbar(result_frame, command=self.txt_result.yview,
                          bg=BG_PANEL, troughcolor=BG_CARD, width=8)
        sb.grid(row=0, column=1, sticky="ns")
        self.txt_result.configure(yscrollcommand=sb.set)

        # Tombol simpan
        btn_save = tk.Button(
            panel, text="SIMPAN GAMBAR",
            bg=BG_CARD, fg=ACCENT2, font=("Courier New", 9),
            activebackground=BORDER, activeforeground=ACCENT2,
            relief="flat", cursor="hand2", pady=7,
            command=self._save_image,
        )
        btn_save.grid(row=12, column=0, sticky="ew", padx=14, pady=(0, 16))

        # ── Canvas Kanan
        canvas_frame = tk.Frame(self, bg=BG_DARK, padx=8, pady=8)
        canvas_frame.grid(row=0, column=1, sticky="nsew")
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        self.fig, self.ax = plt.subplots(figsize=(14, 9))
        self.fig.patch.set_facecolor(BG_DARK)

        self.mpl_canvas = FigureCanvasTkAgg(self.fig, master=canvas_frame)
        self.mpl_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    def _label(self, parent, row, text):
        tk.Label(
            parent, text=text, bg=BG_PANEL, fg=TEXT_MUTED,
            font=("Courier New", 8, "bold"), anchor="w", padx=14
        ).grid(row=row, column=0, sticky="ew", pady=(10, 2))

    def _combobox(self, parent, row):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Dark.TCombobox",
            fieldbackground=BG_CARD, background=BG_CARD,
            foreground=BG_DARK, bordercolor=BORDER,
            arrowcolor=ACCENT, selectbackground=BG_CARD,
            selectforeground=TEXT_PRIMARY,
        )
        cb = ttk.Combobox(
            parent, values=NODES, state="readonly",
            style="Dark.TCombobox", font=("Courier New", 9),
        )
        cb.grid(row=row, column=0, sticky="ew", padx=14, pady=2)
        return cb

    def _divider(self, parent, row):
        tk.Frame(parent, bg=BORDER, height=1).grid(
            row=row, column=0, sticky="ew", padx=14, pady=4,
        )

    # ── Logika ────────────────────────────────
    def _initial_draw(self):
        draw_graph(self.ax)
        self.mpl_canvas.draw()

    def _find_route(self):
        start = self.cb_start.get()
        end   = self.cb_end.get()

        if not start or not end:
            messagebox.showwarning("Input Kosong", "Pilih lokasi awal dan tujuan terlebih dahulu.")
            return
        if start == end:
            messagebox.showwarning("Sama", "Lokasi awal dan tujuan tidak boleh sama.")
            return

        # Algoritma Dijkstra
        try:
            sp = nx.dijkstra_path(G, start, end, weight='weight')
            sd = nx.dijkstra_path_length(G, start, end, weight='weight')
            self._shortest_path     = sp
            self._shortest_distance = sd
            self._start             = start
            self._end               = end
            self._update_result_text(sp, sd)
        except nx.NetworkXNoPath:
            messagebox.showerror("Tidak Ada Jalur", f"Tidak ada jalur dari {start} ke {end}.")
            return
        except nx.NodeNotFound as e:
            messagebox.showerror("Node Tidak Ditemukan", str(e))
            return

        draw_graph(self.ax, start, end, self._shortest_path, self._shortest_distance)
        self.mpl_canvas.draw()

    def _reset(self):
        self._shortest_path     = None
        self._shortest_distance = None
        self._start             = None
        self._end               = None
        self.cb_start.set('')
        self.cb_end.set('')
        self._clear_result_text()
        draw_graph(self.ax)
        self.mpl_canvas.draw()

    def _update_result_text(self, sp, sd):
        self.txt_result.configure(state="normal")
        self.txt_result.delete("1.0", "end")

        lines = []
        lines.append(f"{'─'*32}")
        lines.append(f"  RUTE: {sp[0]} → {sp[-1]}")
        lines.append(f"{'─'*32}")
        for i, node in enumerate(sp):
            if i < len(sp) - 1:
                w = G[sp[i]][sp[i+1]]['weight']
                lines.append(f"  {node}")
                lines.append(f"    └─ {w:.1f} km ─▶")
            else:
                lines.append(f"  {node}")
        lines.append(f"{'─'*32}")
        lines.append(f"  Total : {sd:.1f} km")
        lines.append(f"  Titik : {len(sp)}")
        lines.append(f"{'─'*32}")

        self.txt_result.insert("end", "\n".join(lines))
        self.txt_result.configure(state="disabled")

    def _clear_result_text(self):
        self.txt_result.configure(state="normal")
        self.txt_result.delete("1.0", "end")
        self.txt_result.configure(state="disabled")

    def _save_image(self):
        self.fig.savefig("output.png", dpi=150, facecolor=BG_DARK)
        messagebox.showinfo("Tersimpan", "Gambar disimpan sebagai output.png")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()