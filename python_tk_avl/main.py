import tkinter as tk
from tkinter import ttk
from avl import create_tree


class AVLApp:
    def __init__(self, root):
        self.tree = create_tree()
        self.root = root
        root.title("AVL Tree Visualizer (Tkinter)")

        # Top: stats
        stats = ttk.Frame(root)
        stats.pack(fill="x", padx=8, pady=6)
        ttk.Label(stats, text="Nodes:").pack(side="left")
        self.node_count = ttk.Label(stats, text="0")
        self.node_count.pack(side="left", padx=(4, 16))
        ttk.Label(stats, text="Height:").pack(side="left")
        self.tree_height = ttk.Label(stats, text="0")
        self.tree_height.pack(side="left", padx=(4, 16))
        ttk.Label(stats, text="Last action:").pack(side="left")
        self.last_action = ttk.Label(stats, text="Ready")
        self.last_action.pack(side="left", padx=(4, 16))

        # Controls
        controls = ttk.Frame(root)
        controls.pack(fill="x", padx=8, pady=6)
        self.value_var = tk.StringVar()
        ttk.Entry(controls, textvariable=self.value_var, width=40).pack(side="left")
        ttk.Button(controls, text="Insert", command=self.perform_insert).pack(side="left", padx=4)
        ttk.Button(controls, text="Find", command=self.perform_find).pack(side="left", padx=4)
        ttk.Button(controls, text="Delete", command=self.perform_delete).pack(side="left", padx=4)
        ttk.Button(controls, text="Reset", command=self.perform_reset).pack(side="left", padx=4)

        # Playback controls
        playback = ttk.Frame(root)
        playback.pack(fill="x", padx=8, pady=6)
        ttk.Button(playback, text="<<", command=lambda: self.go_to_frame(0)).pack(side="left")
        ttk.Button(playback, text="<", command=lambda: self.step_timeline(-1)).pack(side="left")
        self.play_btn = ttk.Button(playback, text="Play", command=self.toggle_play)
        self.play_btn.pack(side="left", padx=4)
        ttk.Button(playback, text=">", command=lambda: self.step_timeline(1)).pack(side="left")
        ttk.Button(playback, text=">>", command=lambda: self.go_to_frame(len(self.timeline) - 1)).pack(side="left")
        self.repeat_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(playback, text="Repeat", variable=self.repeat_var).pack(side="left", padx=8)
        ttk.Label(playback, text="Speed (ms):").pack(side="left", padx=(12, 4))
        self.speed_var = tk.IntVar(value=650)
        ttk.Scale(playback, from_=150, to=2000, orient="horizontal", variable=self.speed_var).pack(side="left")

        # Status
        self.status_label = ttk.Label(root, text="Loading tree...")
        self.status_label.pack(fill="x", padx=8, pady=(0, 6))

        # Canvas for tree
        self.canvas = tk.Canvas(root, bg="white", width=1200, height=620)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Legend (overlay in corner) - does not affect canvas layout
        self.legend = ttk.Frame(root)
        self.legend.place(relx=1.0, rely=0.0, x=-12, y=12, anchor="ne")
        self._create_legend_entry(self.legend, "Node", "#ffffff", "#333333")
        self._create_legend_entry(self.legend, "Search result", "#e9f7ec", "#2ecc71")
        self._create_legend_entry(self.legend, "Traversal path", "#fff7e6", "#f5a623")

        # Timeline and playback state
        self.timeline = []
        self.timeline_index = 0
        self.is_playing = False
        self.play_job = None

        # Init
        self.load_tree()

    def set_status(self, text):
        self.status_label.config(text=text)
        self.last_action.config(text=text)

    def _create_legend_entry(self, parent, text, fill, outline):
        row = ttk.Frame(parent)
        sw = tk.Canvas(row, width=18, height=18, highlightthickness=0)
        sw.create_oval(2, 2, 16, 16, fill=fill, outline=outline, width=2)
        sw.pack(side="left")
        ttk.Label(row, text=text).pack(side="left", padx=(6, 0))
        row.pack(anchor="e", pady=2)

    def snapshot(self):
        return self.tree.snapshot()

    def perform_insert(self):
        value = self.value_var.get().strip()
        if not value:
            self.set_status("Please enter a non-empty value.")
            return
        before = self.snapshot()
        after = self.tree.insert(value)
        frames = self.build_operation_timeline(before, after, f'insert "{value}"')
        self.append_timeline(frames)

    def perform_find(self):
        value = self.value_var.get().strip()
        if not value:
            self.set_status("Please enter a non-empty value.")
            return
        before = self.snapshot()
        after = self.tree.find(value)
        frames = self.build_operation_timeline(before, after, f'find "{value}"')
        self.append_timeline(frames)

    def perform_delete(self):
        value = self.value_var.get().strip()
        if not value:
            self.set_status("Please enter a non-empty value.")
            return
        before = self.snapshot()
        after = self.tree.delete(value)
        frames = self.build_operation_timeline(before, after, f'delete "{value}"')
        self.append_timeline(frames)

    def perform_reset(self):
        before = self.snapshot()
        after = self.tree.reset()
        frames = [self.create_frame(before, message='Before reset.'), self.create_frame(after)]
        self.append_timeline(frames)
        self.go_to_frame(len(self.timeline) - 1)

    # Timeline helpers
    def create_frame(self, snapshot, overrides=None, message=None):
        overrides = overrides or {}
        frame = {
            "root": overrides.get("root", snapshot.get("root")),
            "count": overrides.get("count", snapshot.get("count")),
            "height": overrides.get("height", snapshot.get("height")),
            "message": message or snapshot.get("message"),
            "path": overrides.get("path", snapshot.get("path", [])),
            "found": overrides.get("found", snapshot.get("found", False)),
            "foundValue": overrides.get("foundValue", None),
        }
        if frame["found"] and frame["path"]:
            frame["foundValue"] = frame["path"][-1]
        return frame

    def create_traversal_frames(self, snapshot, path, label):
        frames = []
        for i in range(1, len(path) + 1):
            prefix = path[:i]
            frames.append(self.create_frame(snapshot, overrides={"path": prefix}, message=f'{label} {" -> ".join(prefix)}'))
        return frames

    def build_operation_timeline(self, before_snapshot, after_snapshot, action_label):
        frames = [self.create_frame(before_snapshot, message=f'Before {action_label}.')]
        path = after_snapshot.get("path", [])
        if path:
            frames += self.create_traversal_frames(before_snapshot, path, "Visiting")
        frames.append(self.create_frame(after_snapshot))
        return frames

    def append_timeline(self, frames, autoplay=True):
        if not frames:
            return
        start = len(self.timeline)
        self.timeline += frames
        self.timeline_index = start
        self.apply_frame(self.timeline[self.timeline_index])
        if autoplay and len(frames) > 1:
            self.play_timeline()

    def apply_frame(self, frame):
        self.render_frame(frame)
        self.update_playback_ui()

    def update_playback_ui(self):
        total = len(self.timeline)
        current = 0 if total == 0 else self.timeline_index + 1
        self.root.title(f"AVL Tree Visualizer (Tkinter) — Frame {current}/{total}")
        self.play_btn.config(text="Pause" if self.is_playing else "Play")

    def play_timeline(self):
        if len(self.timeline) <= 1:
            self.is_playing = False
            self.update_playback_ui()
            return
        self.is_playing = True
        self.update_playback_ui()
        self.schedule_play()

    def schedule_play(self):
        if self.play_job:
            self.root.after_cancel(self.play_job)
            self.play_job = None
        if not self.is_playing:
            return
        ms = self.speed_var.get()
        self.play_job = self.root.after(ms, lambda: self.step_timeline(1))

    def pause_timeline(self):
        self.is_playing = False
        if self.play_job:
            self.root.after_cancel(self.play_job)
            self.play_job = None
        self.update_playback_ui()

    def toggle_play(self):
        if self.is_playing:
            self.pause_timeline()
        else:
            self.play_timeline()

    def step_timeline(self, direction):
        if not self.timeline:
            return
        last = len(self.timeline) - 1
        next_idx = self.timeline_index + direction
        if next_idx > last:
            if self.repeat_var.get():
                next_idx = 0
            else:
                self.pause_timeline()
                next_idx = last
        if next_idx < 0:
            if self.repeat_var.get():
                next_idx = last
            else:
                next_idx = 0
        self.timeline_index = next_idx
        self.apply_frame(self.timeline[self.timeline_index])
        if self.is_playing:
            self.schedule_play()

    def go_to_frame(self, index):
        if not self.timeline:
            return
        index = max(0, min(index, len(self.timeline) - 1))
        self.pause_timeline()
        self.timeline_index = index
        self.apply_frame(self.timeline[self.timeline_index])

    # Rendering
    def render_frame(self, frame):
        root_node = frame.get("root")
        self.node_count.config(text=str(frame.get("count", 0)))
        self.tree_height.config(text=str(frame.get("height", 0)))
        self.set_status(frame.get("message", ""))
        self.canvas.delete("all")
        if not root_node:
            self.canvas.create_text(600, 310, text="Tree is empty", font=("Arial", 20))
            return
        items = []
        self.assign_positions(root_node, 0, 80, 1120, items)
        width = max(1200, max((it[1] for it in items), default=1200) + 80)
        height = max(620, max((it[2] for it in items), default=620) + 90)
        self.canvas.config(scrollregion=(0, 0, width, height))
        # Draw edges
        for node, x, y in items:
            if node.get("left"):
                child = next(it for it in items if it[0] is node.get("left"))
                self.canvas.create_line(x, y + 24, child[1], child[2] - 24)
            if node.get("right"):
                child = next(it for it in items if it[0] is node.get("right"))
                self.canvas.create_line(x, y + 24, child[1], child[2] - 24)
        # Draw nodes
        highlight = set(frame.get("path", []))
        found = frame.get("foundValue")
        for node, x, y in items:
            val = node.get("value")
            # Default visuals
            fill = "#ffffff"
            outline = "#333333"
            # Traversal path highlight
            if val in highlight:
                fill = "#fff7e6"  # light orange
                outline = "#f5a623"
            # Found takes precedence
            if found is not None and val == found:
                fill = "#e9f7ec"  # light green
                outline = "#2ecc71"
            self.canvas.create_oval(x - 24, y - 24, x + 24, y + 24, fill=fill, outline=outline, width=3)
            self.canvas.create_text(x, y - 2, text=str(val))
            self.canvas.create_text(x, y + 18, text=f"h:{node.get('height')}", font=("Arial", 9))

    def assign_positions(self, node, depth=0, x_min=80, x_max=1120, items=None):
        if items is None:
            items = []
        if not node:
            return items
        x = (x_min + x_max) / 2
        y = 90 + depth * 92
        items.append((node, x, y))
        if node.get("left"):
            self.assign_positions(node.get("left"), depth + 1, x_min, x, items)
        if node.get("right"):
            self.assign_positions(node.get("right"), depth + 1, x, x_max, items)
        return items

    def load_tree(self):
        self.tree.reset()
        snap = self.snapshot()
        self.timeline = [self.create_frame(snap)]
        self.timeline_index = 0
        self.apply_frame(self.timeline[0])


if __name__ == "__main__":
    root = tk.Tk()
    app = AVLApp(root)
    root.mainloop()
