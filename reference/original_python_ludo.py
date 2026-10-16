import tkinter as tk
import tkinter.font as tkfont
import random
import math
import time


def pxfont(family, pixels, weight="normal"):
    """Tk negative font sizes request pixel-based sizing, avoiding DPI/IME scaling."""
    return (family, -abs(int(pixels)), weight)

class GamePopup(tk.Toplevel):
    """Centered gameplay popup that sizes itself to the message."""
    def __init__(self, parent, title, message, color="#333333", kind="info"):
        super().__init__(parent)
        self.configure(bg="white")
        self.title(title)
        self.transient(parent)
        self.resizable(False, False)
        sw = max(360, int(getattr(parent, "screen_w", parent.winfo_screenwidth())))
        sh = max(640, int(getattr(parent, "screen_h", parent.winfo_screenheight())))
        font_size = max(18, min(26, int(sw * 0.055)))
        font = tkfont.Font(family="Arial", size=-font_size, weight="bold")
        # Use a consistently wider, more readable popup on mobile screens.
        dw = min(sw - 24, max(320, int(sw * 0.90)))
        max_width = max(240, dw - 48)
        lines, line = [], ""
        for word in str(message).split():
            candidate = word if not line else line + " " + word
            if line and font.measure(candidate) > max_width:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        display_message = "\n".join(lines)
        measured = max((font.measure(item) for item in lines), default=200)
        # Keep the popup width generous even for short messages; allow extra
        # vertical space so multi-line results do not feel cramped.
        dw = min(sw - 24, max(dw, int(min(max_width, measured) + 72)))
        dh = min(max(200, 132 + len(lines) * (font_size + 12)), max(200, sh - 60))
        x, y = max(0, (sw - dw) // 2), max(20, (sh - dh) // 2)
        self.geometry(f"{dw}x{dh}+{x}+{y}")
        outer = tk.Frame(self, bg="white", highlightbackground=color, highlightthickness=3)
        outer.pack(fill="both", expand=True, padx=4, pady=4)
        tk.Label(outer, text=title, bg="white", fg=color,
                 font=pxfont("Arial", font_size, "bold"), anchor="center", justify="center").pack(
                     fill="x", padx=14, pady=(14, 8))
        tk.Label(outer, text=display_message, bg="white", fg="#222222",
                 font=pxfont("Arial", font_size, "bold"), anchor="center", justify="center",
                 wraplength=dw - 56).pack(fill="both", expand=True, padx=18, pady=8)
        tk.Button(outer, text="OK", command=self.close,
                  font=pxfont("Arial", max(17, font_size - 2), "bold"), width=8).pack(pady=(6, 14))
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Return>", lambda _e: self.close())
        self.bind("<Escape>", lambda _e: self.close())
        self.grab_set()
        self.after(30, self._raise_popup)
        self.wait_window(self)

    def _raise_popup(self):
        try:
            self.lift()
            self.focus_force()
        except tk.TclError:
            pass

    def close(self):
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()

class TopInputDialog(tk.Toplevel):
    """Fixed-size mobile input dialog.

    It deliberately does not use simpledialog's auto-sized layout.  On some
    mobile Tk builds the requested font metrics can change when the keyboard
    appears, which can make a simpledialog grow outside the screen.  This
    dialog has fixed geometry and is positioned from the stored screen size.
    """
    def __init__(self, parent, title, prompt, kind="string", minvalue=None, maxvalue=None):
        super().__init__(parent)
        self.parent = parent
        self.prompt_text = prompt
        self.kind = kind
        self.minvalue = minvalue
        self.maxvalue = maxvalue
        self.value = None
        self.result = None

        self.configure(bg="white")
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        # Fixed dimensions prevent font/keyboard changes from resizing the dialog.
        sw = max(360, int(getattr(parent, "screen_w", parent.winfo_screenwidth())))
        dw = min(520, max(330, sw - 40))
        dh = 210
        self.geometry(f"{dw}x{dh}+0+40")

        outer = tk.Frame(self, bg="white")
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        self.prompt_label = tk.Label(
            outer, text=self.prompt_text, bg="white", fg="#222222",
            font=pxfont("Arial", 22, "bold"), anchor="center", justify="center", wraplength=0
        )
        self.prompt_label.pack(fill="x", pady=(8, 10))

        self.entry = tk.Entry(
            outer, font=pxfont("Arial", 24, "bold"), justify="center",
            relief="solid", bd=1
        )
        self.entry.pack(fill="x", padx=12, ipady=7)

        # Android Tk/IME can occasionally deliver the same CAPITAL key event
        # twice (especially with Shift/auto-capitalisation).  Suppress only a
        # near-immediate duplicate uppercase letter; normal typing is untouched.
        self._last_key_char = ""
        self._last_key_time = 0.0
        self.entry.bind("<KeyPress>", self._filter_duplicate_capital, add="")

        self.hint = tk.Label(
            outer, text="", bg="white", fg="#D32F2F",
            font=pxfont("Arial", 13, "bold")
        )
        self.hint.pack(pady=(3, 0))

        buttons = tk.Frame(outer, bg="white")
        buttons.pack(fill="x", pady=(8, 0))
        tk.Button(
            buttons, text="OK", command=self.ok,
            font=pxfont("Arial", 18, "bold"), width=8
        ).pack(side="left", expand=True, padx=6)
        tk.Button(
            buttons, text="Cancel", command=self.cancel,
            font=pxfont("Arial", 18, "bold"), width=8
        ).pack(side="right", expand=True, padx=6)

        self.bind("<Return>", lambda e: self.ok())
        self.bind("<Escape>", lambda e: self.cancel())

        # Place once after geometry is known. Do not repeatedly refocus while typing.
        self.after(60, self._show_top_and_focus)
        self.grab_set()
        self.wait_window(self)

    def _filter_duplicate_capital(self, event):
        ch = getattr(event, "char", "") or ""
        now = time.monotonic()
        if len(ch) == 1 and ch.isalpha() and ch.isupper():
            if ch == self._last_key_char and (now - self._last_key_time) < 0.14:
                return "break"
            self._last_key_char = ch
            self._last_key_time = now
        else:
            self._last_key_char = ""
            self._last_key_time = now
        return None

    def _show_top_and_focus(self):
        try:
            self.update_idletasks()
            sw = max(360, int(getattr(self.parent, "screen_w", self.parent.winfo_screenwidth())))
            dw = self.winfo_width()
            x = max(0, (sw - dw) // 2)
            self.geometry(f"{dw}x{self.winfo_height()}+{x}+40")
            self.lift()
            self.entry.focus_set()
            self.entry.icursor("end")
        except tk.TclError:
            pass

    def validate_input(self):
        raw = self.entry.get().strip()
        if self.kind == "int":
            try:
                value = int(raw)
            except ValueError:
                self.hint.configure(text="Enter 2-4")
                return False
            if self.minvalue is not None and value < self.minvalue:
                self.hint.configure(text="Enter 2-4")
                return False
            if self.maxvalue is not None and value > self.maxvalue:
                self.hint.configure(text="Enter 2-4")
                return False
            self.value = value
            return True

        valid_name = (
            1 <= len(raw) <= 12
            and raw.replace(" ", "").isalpha()
            and "  " not in raw
        )
        if not valid_name:
            self.hint.configure(text="Enter 1-12 letters.")
            return False
        self.value = raw
        return True

    def ok(self):
        if not self.validate_input():
            self.entry.focus_set()
            return
        self.result = self.value
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()

    def cancel(self):
        self.value = None
        self.result = None
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()

class LudoGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Ludo Pro - Calsi Version")
        self.root.configure(bg="white")
        # Mobile hard-lock: use the real display size and keep the window at (0,0).
        self.screen_w = max(360, int(self.root.winfo_screenwidth()))
        self.screen_h = max(640, int(self.root.winfo_screenheight()))
        sw, sh = self.screen_w, self.screen_h
        self.root.geometry(f"{sw}x{sh}+0+0")
        self.root.update_idletasks()
        try:
            self.root.overrideredirect(True)
        except tk.TclError:
            pass
        self.root.resizable(False, False)
        self.root.geometry(f"{sw}x{sh}+0+0")
        self.root.update_idletasks()

        # Game State
        self.num_players = 4
        self.current_player_index = 0
        self.dice_value = 0
        self.can_move = False

        # Classic Ludo rule: three consecutive sixes forfeit the turn.
        # Keep a snapshot so the whole turn can be cancelled if the third
        # six is rolled (including moves/captures made after the first two).
        self.six_streak = 0
        self.turn_snapshot = {}
        self.board_size = 650
        self.cell_size = self.board_size // 15
        
        # Animation State
        self.anim_id = None
        self.pulse_radius = 0
        self.pulse_growing = True
        self.rendered_coords = {} 
        self.move_anim_job = None
        self.move_animating = False
        self._last_token_click = 0.0
        self._turn_action_locked = False

        # --- COLORS ---
        self.colors = {
            "Green": "#39D14C",   
            "Blue": "#0084F5",    
            "Red": "#FF574B",     
            "Yellow": "#FFE61A"   
        }
        
        self.token_colors = {
            "Green": "#2ECC40", 
            "Blue": "#0074D9",  
            "Red": "#FF4136",   
            "Yellow": "#FFDC00" 
        }
        
        self.inner_token_colors = {
            "Green": "#1A8A24",
            "Blue": "#004B8C",
            "Red": "#B32E27",
            "Yellow": "#B39E00"
        }

        self.turn_order = ["Green", "Blue", "Red", "Yellow"] 
        self.active_players = []
        self.player_names = {}
        self.finish_order = []
        self.game_over = False
        # A player must capture at least one opponent token before entering home.
        self.players_who_captured = set()
        self.token_positions = {} 
        self.paths = {}
        
        # Safe squares exactly match the four start stars and four globe stars
        # drawn on the board. Keep this list aligned with draw_board_graphics().
        self.safe_spots = [
            (1, 6), (8, 1), (13, 8), (6, 13),
            (2, 8), (6, 2), (12, 6), (8, 12)
        ]

        # IMPORTANT: do not recenter to a fixed desktop size here.
        # The mobile display geometry set above must remain the real window size.
        self.root.after(100, self.setup_game)

    def center_window(self, width, height):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def setup_game(self):
        count_dlg = TopInputDialog(self.root, "New Game", "Players (2-4):", kind="int", minvalue=2, maxvalue=4)
        count = count_dlg.value
        if not count: 
            self.root.destroy()
            return
        
        self.num_players = count
        if count == 2: self.active_players = ["Green", "Red"]
        elif count == 3: self.active_players = ["Green", "Blue", "Red"]
        else: self.active_players = ["Green", "Blue", "Red", "Yellow"]
        
        self.turn_order = [c for c in self.turn_order if c in self.active_players]

        # Ask each active player for a display name (up to 12 characters,
        # with spaces allowed between words). Names are drawn in 3D colour.
        self.player_names = {}
        self.finish_order = []
        self.game_over = False
        self.players_who_captured = set()
        for p in self.active_players:
            while True:
                name_dlg = TopInputDialog(
                    self.root, "Player Name",
                    f"Enter {p}'s name.",
                    kind="string"
                )
                name = name_dlg.value
                if name is None:
                    name = p
                name = name.strip()
                if (1 <= len(name) <= 12 and name.replace(" ", "").isalpha()
                        and "  " not in name):
                    self.player_names[p] = name
                    break
                self.show_game_popup(
                    "Name Not Accepted",
                    "Please enter 1-12 letters.",
                    kind="warning"
                )
        
        for p in self.active_players:
            for i in range(4):
                self.token_positions[f"{p}_{i}"] = -1 

        self.generate_paths()
        self.create_ui()
        self.draw_board_graphics()
        self.draw_tokens()
        self._save_turn_snapshot()
        self.update_turn_indicator()

    def create_ui(self):
        # Four-player layout: every player gets a large personal dice box
        # positioned directly in front of that player's side of the board.
        self.main_frame = tk.Frame(self.root, bg="white")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            self.main_frame, bg="white", highlightthickness=0,
            width=self.board_size, height=self.board_size
        )
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")

        # Large personal dice canvases. Their positions are recalculated
        # whenever the window changes size.
        self.dice_canvases = {}
        self.name_canvases = {}
        for color in ["Green", "Blue", "Red", "Yellow"]:
            dc = tk.Canvas(
                self.main_frame, width=150, height=150,
                bg="white", highlightthickness=0, bd=0
            )
            self.dice_canvases[color] = dc
            dc.bind("<Button-1>", lambda e, c=color: self.roll_dice_click_for(c))

            nc = tk.Canvas(
                self.main_frame, width=150, height=46,
                bg="white", highlightthickness=0, bd=0
            )
            self.name_canvases[color] = nc

        # Responsive centered top title + subtitle.
        self.title_label = tk.Label(
            self.main_frame, text="LUDO FRIENDLY PROFESSIONAL",
            font=pxfont("Arial", 30, "bold"), bg="white", fg="#222222",
            anchor="center", justify="center"
        )
        self.title_label.place(relx=0.5, y=27, anchor="n")

        self.powered_label = tk.Label(
            self.main_frame, text="Powered by Python",
            font=pxfont("Arial", 19, "bold"), bg="white", fg="#555555",
            anchor="center", justify="center"
        )
        self.powered_label.place(relx=0.5, y=72, anchor="n")

        self._layout_job = None
        self._blink_job = None
        self._blink_phase = False
        # Do not bind <Configure>: Android may emit configure events while
        # the keyboard opens/closes, which can temporarily report a bad size.
        self.root.after(80, self.position_player_dice)
        self.root.after(180, self._blink_active_dice)

    def _on_window_configure(self, event=None):
        # Kept for compatibility; layout is intentionally not recalculated
        # during keyboard/window-manager configure events.
        return

    def position_player_dice(self):
        if not hasattr(self, "dice_canvases") or not self.dice_canvases:
            return

        self.main_frame.update_idletasks()
        # Use the physical display dimensions captured at startup.  The Android
        # IME can temporarily change winfo_width/winfo_height; those transient
        # values must never resize the game UI.
        w = self.screen_w
        h = self.screen_h

        # Responsive title: scales with screen width and stays centered.
        title_size = max(28, min(34, int(w * 0.044)))
        subtitle_size = max(17, min(20, int(w * 0.027)))
        if hasattr(self, "title_label"):
            self.title_label.configure(font=pxfont("Arial", title_size, "bold"))
        if hasattr(self, "powered_label"):
            self.powered_label.configure(font=pxfont("Arial", subtitle_size, "bold"))

        # The board is ALWAYS centered horizontally.  Keep generous vertical
        # space for the four personal dice boxes.
        board = min(w - 20, h - 330, 670)
        board = max(300, int(board))
        board_x = w / 2
        board_y = h * 0.52

        # Keep the complete square on-screen.
        board_y = max(board / 2 + 125, min(h - board / 2 - 125, board_y))

        box = min(140, max(120, int(w * 0.2025)))
        gap = max(8, int(w * 0.018))

        top_y = board_y - board / 2 - box / 2 - gap
        bottom_y = board_y + board / 2 + box / 2 + gap
        left_x = w * 0.22
        right_x = w * 0.78

        positions = {
            "Green": (left_x, top_y),
            "Blue": (right_x, top_y),
            "Yellow": (left_x, bottom_y),
            "Red": (right_x, bottom_y),
        }

        # Explicitly set the board size before drawing.  Tk's place manager
        # supports a centered anchor, so the square stays centered as the
        # display changes.
        self.canvas.place(
            relx=0.5, rely=board_y / h, anchor="center",
            width=board, height=board
        )
        self.board_size = board
        self.cell_size = max(1, board // 15)

        # FIRST place every Canvas.  Then force Tk to realize the requested
        # pixel sizes before drawing anything inside them.  On Android/Tk,
        # winfo_width()/winfo_height() can still return 1 immediately after
        # place(); drawing at that moment clips the dice/name to tiny fragments.
        # This was the source of the intermittent broken main-window layout.
        for color, (cx, cy) in positions.items():
            self.dice_canvases[color].place(
                x=cx, y=cy, anchor="center", width=box, height=box
            )

            # Player name sits immediately outside the dice box: above the
            # top pair and below the bottom pair. Inactive/non-playing colours
            # stay text-free.
            name = self.player_names.get(color, "")
            if name:
                if color in ("Green", "Blue"):
                    name_y = cy - box / 2 - 21
                else:
                    name_y = cy + box / 2 + 21
                # Give the name its own generous drawing area.  The old 32%
                # height + 16-21px font made names look tiny on the phone.
                # Wider/taller name canvas lets the font stay genuinely large.
                # The center position remains exactly the same as before.
                name_w = max(200, int(box * 1.48))
                name_h = max(68, int(box * 0.48))
                name_y = max(name_h / 2 + 4, min(h - name_h / 2 - 4, name_y))
                nc = self.name_canvases[color]
                nc.place(x=cx, y=name_y, anchor="center", width=name_w, height=name_h)
            else:
                self.name_canvases[color].place_forget()

        # Commit all place() geometry before querying Canvas dimensions.
        self.main_frame.update_idletasks()

        # Now that every Canvas has its real size, draw all dice and names.
        for color, (cx, cy) in positions.items():
            active = color == self.turn_order[self.current_player_index]
            value = self.dice_value if active and self.dice_value else None
            self.draw_personal_dice(color, value)
            if self.player_names.get(color, ""):
                self.draw_player_name(color)

        self.canvas.delete("all")
        self.draw_board_graphics()
        self.draw_tokens()

    def draw_player_name(self, color):
        """Show the player's name in bold white text on that player's colour."""
        nc = self.name_canvases.get(color)
        name = self.player_names.get(color, "")
        if nc is None or not name:
            return
        nc.delete("all")
        w = max(nc.winfo_width(), 1)
        h = max(nc.winfo_height(), 1)
        cx, cy = w / 2, h / 2

        # Solid player-colour name plate with white lettering for strong contrast.
        name_bg = {
            "Green": "#20B83F",
            "Blue": "#087FE5",
            "Red": "#F0443E",
            # Keep the original bright yellow used by the game board.
            "Yellow": "#FFE61A",
        }.get(color, "#333333")

        # Leave a small margin around the plate. The surrounding layout stays unchanged.
        pad_x = 5
        plate_h = min(h - 4, 43)
        nc.create_rectangle(
            pad_x, (h - plate_h) / 2, w - pad_x, (h + plate_h) / 2,
            fill=name_bg, outline=name_bg, width=1
        )

        # Use a larger bold font, shrinking only enough to keep 12-character names visible.
        font_size = max(22, min(32, int(plate_h * 0.68)))
        available_w = max(50, w - 20)
        while font_size > 20:
            test_font = tkfont.Font(family="Arial", size=-font_size, weight="bold")
            if test_font.measure(name) <= available_w:
                break
            font_size -= 1
        name_font = tkfont.Font(family="Arial", size=-font_size, weight="bold")
        if color == "Yellow":
            # Keep bright original yellow, and give white letters a strong
            # dark outline so they remain readable on the light background.
            outline = "#4A3A00"
            for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2),
                           (-2, -2), (2, -2), (-2, 2), (2, 2),
                           (-3, 0), (3, 0), (0, -3), (0, 3),
                           (-1, 0), (1, 0), (0, -1), (0, 1)]:
                nc.create_text(
                    cx + ox, cy + oy, text=name, font=name_font,
                    fill=outline, anchor="center"
                )
        else:
            # Subtle dark edge also keeps the white names crisp on bright colours.
            for ox, oy in [(-1, 1), (1, 1), (0, 1)]:
                nc.create_text(
                    cx + ox, cy + oy, text=name, font=name_font,
                    fill="#333333", anchor="center"
                )
        nc.create_text(
            cx, cy, text=name, font=name_font, fill="#FFFFFF",
            anchor="center"
        )

    def _round_rect(self, canvas, x1, y1, x2, y2, radius, fill, outline=None, width=1, tags=None):
        """Draw a clean rounded rectangle using Canvas primitives."""
        tags = tags or "dice_ui"
        r = min(radius, (x2-x1)/2, (y2-y1)/2)
        canvas.create_rectangle(x1+r, y1, x2-r, y2, fill=fill, outline="", tags=tags)
        canvas.create_rectangle(x1, y1+r, x2, y2-r, fill=fill, outline="", tags=tags)
        canvas.create_oval(x1, y1, x1+2*r, y1+2*r, fill=fill, outline="", tags=tags)
        canvas.create_oval(x2-2*r, y1, x2, y1+2*r, fill=fill, outline="", tags=tags)
        canvas.create_oval(x1, y2-2*r, x1+2*r, y2, fill=fill, outline="", tags=tags)
        canvas.create_oval(x2-2*r, y2-2*r, x2, y2, fill=fill, outline="", tags=tags)
        if outline:
            canvas.create_line(x1+r, y1, x2-r, y1, fill=outline, width=width, tags=tags)
            canvas.create_line(x2, y1+r, x2, y2-r, fill=outline, width=width, tags=tags)
            canvas.create_line(x2-r, y2, x1+r, y2, fill=outline, width=width, tags=tags)
            canvas.create_line(x1, y2-r, x1, y1+r, fill=outline, width=width, tags=tags)
            canvas.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, style="arc", outline=outline, width=width, tags=tags)
            canvas.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, style="arc", outline=outline, width=width, tags=tags)
            canvas.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, style="arc", outline=outline, width=width, tags=tags)
            canvas.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, style="arc", outline=outline, width=width, tags=tags)

    def _draw_die_face(self, canvas, cx, cy, size, value, pip_color="#222222"):
        """Draw a proper square die face with standard 1-6 pip layouts."""
        shadow = 3
        x1, y1 = cx-size/2, cy-size/2
        x2, y2 = cx+size/2, cy+size/2
        self._round_rect(canvas, x1+shadow, y1+shadow, x2+shadow, y2+shadow,
                         max(6, size*.15), fill="#9ca3af")
        self._round_rect(canvas, x1, y1, x2, y2, max(6, size*.15),
                         fill="#ffffff", outline="#202020", width=2)

        # Before the first roll, show a bold question mark in the player's colour.
        # After rolling, replace it with the actual 1-6 dice pips.
        if value not in (1,2,3,4,5,6):
            qcolor = pip_color
            # Soft 3D shadow + bold coloured question mark.
            canvas.create_text(
                cx + 2, cy + 3, text="?",
                fill="#8a8a8a", font=pxfont("Helvetica", max(48, min(64, int(size*.62))), "bold"),
                anchor="center"
            )
            canvas.create_text(
                cx, cy, text="?",
                fill=qcolor, font=pxfont("Helvetica", max(48, min(64, int(size*.62))), "bold"),
                anchor="center"
            )
            return

        d = size * .25
        points = {
            "tl": (cx-d, cy-d), "tr": (cx+d, cy-d),
            "ml": (cx-d, cy),     "mr": (cx+d, cy),
            "bl": (cx-d, cy+d),   "br": (cx+d, cy+d),
            "c": (cx, cy)
        }
        layouts = {
            1: ["c"],
            2: ["tl", "br"],
            3: ["tl", "c", "br"],
            4: ["tl", "tr", "bl", "br"],
            5: ["tl", "tr", "c", "bl", "br"],
            6: ["tl", "tr", "ml", "mr", "bl", "br"],
        }
        r = max(5, size*.070)
        for key in layouts[value]:
            px, py = points[key]
            # 3D pip: deep coloured shadow, bold main body, tiny highlight.
            canvas.create_oval(
                px-r+2, py-r+3, px+r+2, py+r+3,
                fill="#777777", outline=""
            )
            canvas.create_oval(
                px-r, py-r, px+r, py+r,
                fill=pip_color, outline="#222222", width=max(1, int(size*.012))
            )
            hr = max(2, r*.30)
            canvas.create_oval(
                px-r*.42, py-r*.45,
                px-r*.42+hr, py-r*.45+hr,
                fill="#ffffff", outline=""
            )

    def draw_personal_dice(self, color, val=None):
        dc = self.dice_canvases.get(color)
        if dc is None:
            return
        dc.delete("all")
        w = max(dc.winfo_width(), 1)
        h = max(dc.winfo_height(), 1)
        s = min(w, h)
        active = color == self.turn_order[self.current_player_index]
        player_color = self.colors[color]

        outer = max(2, int(s * .040))
        margin = max(10, int(s * .105))
        x1, y1, x2, y2 = margin, margin, s - margin, s - margin

        # ACTIVE BOX: two clearly separate colours.
        # Inner ring = player's own colour.
        # Outer ring = purple, as requested.
        if active:
            purple = "#8E44AD" if self._blink_phase else "#D8B4FE"
            same = player_color
            self._round_rect(
                dc, x1-outer-6, y1-outer-6, x2+outer+6, y2+outer+6,
                max(13, s*.15), fill="", outline=purple,
                width=max(7, int(s*.055)), tags="active_glow"
            )
            self._round_rect(
                dc, x1-outer, y1-outer, x2+outer, y2+outer,
                max(12, s*.14), fill="", outline=same,
                width=max(6, int(s*.050)), tags="active_glow"
            )

        card_fill = "#ffffff" if active else "#f3f4f6"
        border = player_color if active else "#9ca3af"
        self._round_rect(
            dc, x1, y1, x2, y2, max(10, s*.12),
            fill=card_fill, outline=border,
            width=max(3, int(s*.040))
        )

        # Text-free professional dice box. Only the graphical die is shown.
        # Use more of the available die-card area so the question mark and
        # pip faces are visually balanced with the large personal box.
        die_size = int(s * .72)
        die_y = (y1 + y2) / 2
        shown = val if val in (1,2,3,4,5,6) else None
        self._draw_die_face(
            dc, s/2, die_y, die_size, shown,
            pip_color=self.token_colors[color]
        )

    def _blink_active_dice(self):
        """Continuously blink only the current player's outer dice-box ring."""
        if not hasattr(self, "dice_canvases") or not self.dice_canvases:
            self._blink_job = self.root.after(300, self._blink_active_dice)
            return
        self._blink_phase = not self._blink_phase
        active_color = self.turn_order[self.current_player_index]
        for color in self.dice_canvases:
            dc = self.dice_canvases[color]
            # Redraw only the active box so the glow alternates smoothly.
            if color == active_color:
                value = self.dice_value if self.dice_value in (1,2,3,4,5,6) else None
                self.draw_personal_dice(color, value)
        self._blink_job = self.root.after(420, self._blink_active_dice)

    def draw_dice_button(self, text="", val=None):
        if hasattr(self, "dice_canvases"):
            active_color = self.turn_order[self.current_player_index]
            for color in self.dice_canvases:
                show = val if color == active_color else None
                self.draw_personal_dice(color, show)

    def roll_dice_click_for(self, color):
        # Only the current player's own large personal dice box can roll.
        if color != self.turn_order[self.current_player_index]:
            return
        self.roll_dice_click(None)


    def draw_board_graphics(self):
        # Responsive board size for phone/tablet screens.
        try:
            cw = max(280, int(self.canvas.winfo_width()))
            ch = max(280, int(self.canvas.winfo_height()))
            self.board_size = min(cw, ch)
            self.cell_size = self.board_size // 15
        except Exception:
            pass

        c = self.canvas
        sz = self.cell_size
        
        # Grid Lines
        for i in range(16):
            c.create_line(i*sz, 0, i*sz, 15*sz, fill="black")
            c.create_line(0, i*sz, 15*sz, i*sz, fill="black")

        # Draw Large Home Squares
        self.draw_home_area(0, 0, "Green")
        self.draw_home_area(9, 0, "Blue")
        self.draw_home_area(0, 9, "Yellow")
        self.draw_home_area(9, 9, "Red")

        # --- NEW: Draw Permanent Empty Circles (Sockets) inside Home ---
        # Use the same logic as token placement so they align perfectly
        home_centers = {
            "Green": (3*sz, 3*sz), "Blue": (12*sz, 3*sz),
            "Yellow": (3*sz, 12*sz), "Red": (12*sz, 12*sz)
        }
        offsets = [(-1,-1), (-1,1), (1,-1), (1,1)]
        dist = sz * 1.5 / 1.4 # Same distance logic as token placement

        for color_name, (cx, cy) in home_centers.items():
            for dx, dy in offsets:
                tx, ty = cx + dx*dist, cy + dy*dist
                # Draw white circle socket (radius 20 to be slightly larger than token)
                c.create_oval(tx-20, ty-20, tx+20, ty+20, fill="white", outline="black", width=1)
        # ---------------------------------------------------------------

        # Colored Tracks
        self.fill_rects([(i, 7) for i in range(1,6)], self.colors["Green"]) 
        self.fill_rects([(i, 7) for i in range(9,14)], self.colors["Red"]) 
        self.fill_rects([(7, i) for i in range(1,6)], self.colors["Blue"]) 
        self.fill_rects([(7, i) for i in range(9,14)], self.colors["Yellow"]) 

        # Center Home Triangles
        c.create_polygon(6*sz, 6*sz, 9*sz, 6*sz, 7.5*sz, 7.5*sz, fill=self.colors["Blue"], outline="black")
        c.create_polygon(6*sz, 6*sz, 6*sz, 9*sz, 7.5*sz, 7.5*sz, fill=self.colors["Green"], outline="black")
        c.create_polygon(9*sz, 6*sz, 9*sz, 9*sz, 7.5*sz, 7.5*sz, fill=self.colors["Red"], outline="black")
        c.create_polygon(6*sz, 9*sz, 9*sz, 9*sz, 7.5*sz, 7.5*sz, fill=self.colors["Yellow"], outline="black")

        # Start Spots with Stars
        start_spots = [(1, 6, "Green"), (8, 1, "Blue"), (13, 8, "Red"), (6, 13, "Yellow")]
        for cx, cy, color in start_spots:
            c.create_rectangle(cx*sz, cy*sz, (cx+1)*sz, (cy+1)*sz, fill=self.colors[color], outline="black")
            self.draw_star(cx*sz + sz//2, cy*sz + sz//2, sz//2 - 3, "white")

        # Safe Spots with Globes/Stars
        globe_spots = [(2, 8), (6, 2), (12, 6), (8, 12)]
        for cx, cy in globe_spots:
            c.create_rectangle(cx*sz, cy*sz, (cx+1)*sz, (cy+1)*sz, fill="#d0d0d0", outline="black")
            self.draw_star(cx*sz + sz//2, cy*sz + sz//2, sz//2 - 3, "#555555")

    def draw_home_area(self, c, r, color_name):
        sz = self.cell_size
        self.canvas.create_rectangle(c*sz, r*sz, (c+6)*sz, (r+6)*sz, fill="white", outline="black", width=2)
        padding = 15
        self.canvas.create_oval(c*sz+padding, r*sz+padding, (c+6)*sz-padding, (r+6)*sz-padding, fill=self.colors[color_name], outline="black")

    def draw_star(self, x, y, radius, color):
        points = []
        for i in range(10):
            angle = i * 36 * 3.14159 / 180 
            r = radius if i % 2 == 0 else radius / 2.5
            points.append(x + r * math.cos(angle - 1.57)) 
            points.append(y + r * math.sin(angle - 1.57))
        self.canvas.create_polygon(points, fill=color, outline="black")

    def fill_rects(self, coords, color):
        for c, r in coords:
            x1, y1 = c*self.cell_size, r*self.cell_size
            x2, y2 = x1+self.cell_size, y1+self.cell_size
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")

    def generate_paths(self):
        p = []
        for i in range(1, 6): p.append((i, 6)) 
        for i in range(5, -1, -1): p.append((6, i))
        p.append((7,0)); p.append((8,0))
        for i in range(1, 6): p.append((8, i))
        for i in range(9, 15): p.append((i, 6))
        p.append((14,7)); p.append((14,8))
        for i in range(13, 8, -1): p.append((i, 8))
        for i in range(9, 15): p.append((8, i))
        p.append((7,14)); p.append((6,14))
        for i in range(13, 8, -1): p.append((6, i))
        for i in range(5, -1, -1): p.append((i, 8))
        p.append((0,7))
        # Complete the missing outer-track square beside the home entrance.
        # Without (0,6), the loop jumps diagonally from (0,7) to (1,6),
        # making the token appear to skip the stop square / take an extra step.
        p.append((0,6))
        for i in range(1, 7): p.append((i, 7))
        self.paths["Green"] = p
        def rotate(coords): return [(14-y, x) for x, y in coords]
        self.paths["Blue"] = rotate(self.paths["Green"])   
        self.paths["Red"] = rotate(self.paths["Blue"])     
        self.paths["Yellow"] = rotate(self.paths["Red"])   

    def draw_tokens(self):
        self.canvas.delete("token")
        self.canvas.delete("anim_ring") 
        sz = self.cell_size
        self.rendered_coords.clear() 
        
        home_centers = {
            "Green": (3*sz, 3*sz), "Blue": (12*sz, 3*sz),
            "Yellow": (3*sz, 12*sz), "Red": (12*sz, 12*sz)
        }
        offsets = [(-1,-1), (-1,1), (1,-1), (1,1)]
        rad = sz * 1.5 / 1.4

        # Group board tokens by cell so same-cell tokens remain individually visible/touchable.
        cell_groups = {}
        for pl in self.active_players:
            for ti in range(4):
                ttag = f"{pl}_{ti}"
                tpos = self.token_positions[ttag]
                if tpos >= 0 and tpos < len(self.paths[pl]):
                    cell = self.paths[pl][tpos]
                    cell_groups.setdefault(cell, []).append(ttag)
        stack_offsets = [(-9, -9), (9, -9), (-9, 9), (9, 9)]

        for player in self.active_players:
            for i in range(4):
                pos = self.token_positions[f"{player}_{i}"]
                tag = f"{player}_{i}"
                
                if pos == -1: 
                    cx, cy = home_centers[player]
                    dx, dy = offsets[i]
                    tx, ty = cx + dx*rad, cy + dy*rad
                else: 
                    if pos < len(self.paths[player]):
                        cell = self.paths[player][pos]
                        c, r = cell
                        tx, ty = c*sz + sz//2, r*sz + sz//2
                        group = cell_groups.get(cell, [])
                        if len(group) > 1:
                            ox, oy = stack_offsets[group.index(tag) % len(stack_offsets)]
                            tx += ox
                            ty += oy
                    else:
                        continue 

                self.rendered_coords[tag] = (tx, ty)

                fill_col = self.token_colors[player]
                inner_col = self.inner_token_colors[player]
                
                # Keep stacked tokens distinct so the active one can be selected with one tap.
                stacked = pos >= 0 and len(cell_groups.get(self.paths[player][pos], [])) > 1
                outer_r = 11 if stacked else 15
                mid_r = 9 if stacked else 13
                inner_r = 6 if stacked else 8
                ring_r = 4 if stacked else 6
                self.canvas.create_oval(tx-outer_r, ty-outer_r, tx+outer_r, ty+outer_r, fill="black", outline="black", tags=("token", tag), width=1)
                self.canvas.create_oval(tx-mid_r, ty-mid_r, tx+mid_r, ty+mid_r, fill=fill_col, outline=fill_col, tags=("token", tag))
                self.canvas.create_oval(tx-inner_r, ty-inner_r, tx+inner_r, ty+inner_r, fill=inner_col, outline=inner_col, tags=("token", tag))
                self.canvas.create_oval(tx-ring_r, ty-ring_r, tx+ring_r, ty+ring_r, outline="white", width=1, tags=("token", tag))

                self.canvas.tag_bind(tag, "<Button-1>", lambda e, t=tag: self.move_token(t))

        # Always display the current player's token above opponents when they
        # share a square. This also handles stacks of more than four tokens,
        # where stack offsets intentionally repeat and tokens overlap.
        active_player = self.turn_order[self.current_player_index]
        for cell, tags_at_cell in cell_groups.items():
            if len(tags_at_cell) < 2:
                continue
            active_tags = [t for t in tags_at_cell if t.startswith(active_player + "_")]
            for active_tag in active_tags:
                self.canvas.tag_raise(active_tag)

    def _block_owner_at(self, coords):
        """Return the owner of a same-colour double-token block on a normal square."""
        if coords in self.safe_spots:
            return None
        counts = {}
        for token_tag, token_pos in self.token_positions.items():
            if token_pos < 0:
                continue
            token_player, _ = token_tag.split("_")
            if token_pos >= len(self.paths.get(token_player, [])):
                continue
            if self.paths[token_player][token_pos] == coords:
                counts[token_player] = counts.get(token_player, 0) + 1
        for owner, count in counts.items():
            if count >= 2:
                return owner
        return None

    def _move_path_is_clear(self, player, start_pos, final_pos):
        """Stacks protect tokens but never block another player's path."""
        return 0 <= final_pos < len(self.paths.get(player, []))

    def _calculate_move_route(self, player, current_pos, dice_value):
        """Return the exact cells travelled, without an extra step at home entry.

        The path stores the 46-cell outer route followed by six home-lane cells.
        Players who have not captured an opponent loop from the last outer cell
        directly to outer position 0; that transition consumes exactly one die
        step. Players who have captured can continue into their own home lane.
        """
        path = self.paths[player]
        outer_count = len(path) - 6
        last_pos = len(path) - 1
        captured = player in self.players_who_captured
        pos = current_pos
        visited = []

        for _ in range(int(dice_value)):
            if pos < 0 or pos > last_pos:
                return None

            next_pos = pos + 1
            # Position 50 is the visible stop beside the home-lane entrance.
            # From that square, one die step must go either into the home lane
            # (if this player has captured) or to the missing outer-loop corner
            # at position 51 (if not). The extra outer corner then loops to 0.
            # Home-lane cells begin at index 52.
            if pos == 50:
                next_pos = 52 if captured else 51
            elif pos == outer_count - 1:
                next_pos = 0
            elif next_pos > last_pos:
                return None  # exact finish required; do not overshoot

            pos = next_pos
            visited.append(pos)

        return pos, visited, (pos == last_pos and captured)

    def get_movable_tokens(self):
        movable = []
        if getattr(self, "game_over", False):
            return movable
        player = self.turn_order[self.current_player_index]
        for i in range(4):
            tag = f"{player}_{i}"
            pos = self.token_positions[tag]
            if pos == -1:
                if self.dice_value == 6:
                    movable.append(tag)
            elif self._calculate_move_route(player, pos, self.dice_value) is not None:
                movable.append(tag)
        return movable

    def _save_turn_snapshot(self):
        """Save the complete state at the start of the current turn."""
        self.turn_snapshot = dict(self.token_positions)
        self.six_streak = 0

    def _restore_turn_snapshot(self):
        """Undo everything earned during the current turn."""
        if self.turn_snapshot:
            self.token_positions = dict(self.turn_snapshot)
        self.six_streak = 0
        self.dice_value = 0
        self.can_move = False
        self.stop_pulsing()
        self.canvas.delete("anim_ring")
        self.draw_tokens()

    def roll_dice_click(self, event):
        if (getattr(self, "game_over", False) or self.can_move or self.move_animating
                or getattr(self, "_turn_action_locked", False)):
            return

        # House rule: 6 has a 35% chance; 1-5 share the remaining 65%.
        self.dice_value = 6 if random.random() < 0.35 else random.randint(1, 5)

        if self.dice_value == 6:
            self.six_streak += 1
        else:
            self.six_streak = 0

        self.draw_dice_button(val=self.dice_value)
        self.root.update_idletasks()

        # CLASSIC RULE: the third consecutive six cancels the whole turn.
        # No token selection and no fourth roll are allowed.
        if self.six_streak >= 3:
            self.can_move = False
            self.stop_pulsing()
            self.canvas.delete("anim_ring")

            # Forfeit the entire turn, including gains from the first two sixes.
            self._restore_turn_snapshot()

            # Show the third six briefly, then pass directly to the next player.
            self.dice_value = 6
            self.draw_dice_button(val=6)
            self.root.after(650, self.switch_turn)
            return

        self.check_moves()

    def check_moves(self):
        movable = self.get_movable_tokens()
        if movable:
            self.can_move = True
            self.start_pulsing() 
        else:
            self.root.after(800, lambda: self.end_move_sequence(killed=False, home_run=False))

    def start_pulsing(self):
        self.stop_pulsing()
        self.canvas.delete("anim_ring")
        self.pulse_radius = 0
        self.pulse_growing = True
        self.animate_movable_tokens()

    def stop_pulsing(self):
        if self.anim_id:
            self.root.after_cancel(self.anim_id)
            self.anim_id = None
        self.canvas.delete("anim_ring")

    def animate_movable_tokens(self):
        if not self.can_move: return
        
        self.canvas.delete("anim_ring")
        
        if self.pulse_growing:
            self.pulse_radius += 1
            if self.pulse_radius > 6: self.pulse_growing = False
        else:
            self.pulse_radius -= 1
            if self.pulse_radius < 0: self.pulse_growing = True
            
        movable = self.get_movable_tokens()
        
        for tag in movable:
            if tag in self.rendered_coords:
                tx, ty = self.rendered_coords[tag]
                r = 17 + self.pulse_radius 
                # Keep the move indicator separate from the token drawing order.
                # It must sit above every token so it remains visible in crowded stacks.
                self.canvas.create_oval(tx-r, ty-r, tx+r, ty+r,
                                      outline="black", width=3, dash=(4, 3),
                                      tags=("anim_ring", "indicator_" + tag))

        self.canvas.tag_raise("anim_ring")
        self.anim_id = self.root.after(60, self.animate_movable_tokens)

    def _path_pixel(self, player, pos):
        c, r = self.paths[player][pos]
        return c * self.cell_size + self.cell_size // 2, r * self.cell_size + self.cell_size // 2

    def _ease_in_out(self, t):
        # Smooth cubic easing: gentle start/end, faster in the middle.
        return 3 * t * t - 2 * t * t * t

    def show_game_popup(self, title, message, player=None, kind="info"):
        color = self.colors.get(player, "#333333") if player else "#333333"
        GamePopup(self.root, title, message, color=color, kind=kind)

    def _finish_token_animation(self, tag, final_pos, reached_home):
        self.move_anim_job = None
        self.move_animating = False
        p, _ = tag.split("_")
        self.token_positions[tag] = final_pos

        killed_someone = self.check_kill(tag)
        self.draw_tokens()

        if reached_home:
            player_name = self.player_names.get(p, p)
            self.show_game_popup("Token Home", f"{player_name}'s token has reached home.", player=p)

        # Record finishing place once all four tokens reach the final home cell.
        player_finished = all(
            self.token_positions.get(f"{p}_{i}", -1) == len(self.paths[p]) - 1
            for i in range(4)
        )
        if player_finished and p not in self.finish_order:
            self.finish_order.append(p)
            place = len(self.finish_order)
            player_name = self.player_names.get(p, p)
            place_words = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}

            # In a multiplayer race, once all but one player finish, announce
            # the complete result immediately and mark the remaining player(s) as losers.
            if len(self.finish_order) >= max(1, len(self.active_players) - 1):
                self.game_over = True
                self.can_move = False
                self.move_animating = False
                self.stop_pulsing()
                self.canvas.delete("anim_ring")
                lines = ["FINAL RESULTS", ""]
                for rank, finished_color in enumerate(self.finish_order, start=1):
                    finished_name = self.player_names.get(finished_color, finished_color)
                    if rank == 1:
                        lines.append(f"1st Place — {finished_name} (Winner)")
                    else:
                        lines.append(f"{place_words.get(rank, str(rank) + 'th')} Place — {finished_name}")
                remaining = [c for c in self.active_players if c not in self.finish_order]
                for c in remaining:
                    lines.append(f"Did not finish — {self.player_names.get(c, c)}")
                self.show_game_popup("GAME OVER", "\n".join(lines), player=p)
            elif place == 1:
                self.show_game_popup(
                    "GAME COMPLETE",
                    f"{player_name} is the winner!\n\nExcellent play!",
                    player=p
                )
            else:
                self.show_game_popup(
                    "GAME UPDATE",
                    f"{player_name} finished in {place_words.get(place, str(place) + 'th')} place.\n\nWell played!",
                    player=p
                )

        self.end_move_sequence(killed=killed_someone, home_run=reached_home)

    def _animate_token_path(self, tag, player, points, point_index=0, frame=0, start_xy=None, final_pos=0, reached_home=False):
        if not points:
            self._finish_token_animation(tag, final_pos, reached_home)
            return

        if start_xy is None:
            start_xy = self.rendered_coords.get(tag)
            if start_xy is None:
                self.draw_tokens()
                start_xy = self.rendered_coords.get(tag)
            if start_xy is None:
                self._finish_token_animation(tag, final_pos, reached_home)
                return

        # 6 small frames per square give a noticeably smoother touch movement.
        frames_per_cell = 6
        target_xy = points[point_index]
        t = min(1.0, (frame + 1) / frames_per_cell)
        e = self._ease_in_out(t)
        x = start_xy[0] + (target_xy[0] - start_xy[0]) * e
        y = start_xy[1] + (target_xy[1] - start_xy[1]) * e

        dx = x - self._anim_last_xy[0]
        dy = y - self._anim_last_xy[1]
        self.canvas.move(tag, dx, dy)
        # Keep the currently moving token above every other token on shared cells.
        # Canvas items are stacked by display-list order; raise the whole token tag
        # after every animation frame so it cannot disappear underneath another goti.
        self.canvas.tag_raise(tag)
        self._anim_last_xy = (x, y)

        if frame + 1 < frames_per_cell:
            self.move_anim_job = self.root.after(24, lambda: self._animate_token_path(
                tag, player, points, point_index, frame + 1, start_xy, final_pos, reached_home
            ))
            return

        # Arrived at this square. Continue to the next square from its exact centre.
        if point_index + 1 < len(points):
            next_start = target_xy
            self._anim_last_xy = next_start
            self.move_anim_job = self.root.after(18, lambda: self._animate_token_path(
                tag, player, points, point_index + 1, 0, next_start, final_pos, reached_home
            ))
        else:
            self._finish_token_animation(tag, final_pos, reached_home)

    def move_token(self, tag):
        now = time.monotonic()
        # Ignore rapid duplicate touch events (common on mobile screens).
        if now - getattr(self, "_last_token_click", 0.0) < 0.22:
            return
        self._last_token_click = now
        if getattr(self, "game_over", False) or not self.can_move or self.move_animating or getattr(self, "_turn_action_locked", False):
            return
        p, idx = tag.split("_")
        if p != self.turn_order[self.current_player_index]:
            return

        if tag not in self.get_movable_tokens():
            player_name = self.player_names.get(p, p)
            self.show_game_popup("Choose Another Token", f"{player_name}, please select a token that can move.", player=p, kind="warning")
            return

        self.stop_pulsing()
        self.move_animating = True
        self.can_move = False
        self._turn_action_locked = True

        cur = self.token_positions[tag]
        reached_home = False
        points = []

        if cur == -1:
            # Entering the board: animate yard -> starting square.
            final_pos = 0
            points = [self._path_pixel(p, 0)]
        else:
            route = self._calculate_move_route(p, cur, self.dice_value)
            if route is None:
                self.move_animating = False
                self.can_move = True
                self._turn_action_locked = False
                self.start_pulsing()
                return
            final_pos, visited_positions, reached_home = route
            # Animate every actual cell in order. Uncaptured tokens wrap from
            # the home-lane entrance back to outer-track position 0; captured
            # tokens proceed into their own coloured lane instead.
            points = [self._path_pixel(p, pos) for pos in visited_positions]

        start_xy = self.rendered_coords.get(tag)
        if start_xy is None:
            self.draw_tokens()
            start_xy = self.rendered_coords.get(tag)

        if start_xy is None:
            self.move_animating = False
            self.can_move = True
            return

        self._anim_last_xy = start_xy
        self._animate_token_path(tag, p, points, 0, 0, start_xy, final_pos, reached_home)

    def check_kill(self, current_tag):
        current_player, _ = current_tag.split("_")
        cur_idx = self.token_positions[current_tag]
        kill_happened = False
        
        if cur_idx == -1: return False 
        
        cur_coords = self.paths[current_player][cur_idx]

        # A same-colour pair on a normal square forms a protected block.
        # Safety is also checked here defensively, even if movement validation changes.
        if cur_coords in self.safe_spots:
            return False
        if self._block_owner_at(cur_coords) not in (None, current_player):
            return False

        for other_tag, other_idx in self.token_positions.items():
            if other_tag == current_tag: continue 
            other_player, _ = other_tag.split("_")
            if other_player == current_player: continue 
            if other_idx == -1: continue 
            if other_idx >= len(self.paths[other_player]): continue 
            
            other_coords = self.paths[other_player][other_idx]
            if cur_coords == other_coords:
                self.token_positions[other_tag] = -1 
                current_name = self.player_names.get(current_player, current_player)
                other_name = self.player_names.get(other_player, other_player)
                self.show_game_popup("Token Captured", f"{current_name} captured {other_name}'s token. It returns to the starting area.", player=current_player)
                kill_happened = True
                self.players_who_captured.add(current_player)
        
        return kill_happened

    def end_move_sequence(self, killed=False, home_run=False):
        if getattr(self, "game_over", False):
            self.can_move = False
            return
        self.can_move = False
        self.stop_pulsing()
        self.draw_tokens()

        # A third six is handled immediately in roll_dice_click(), so it can
        # never reach this branch and accidentally grant another roll.
        if self.dice_value != 6 and not killed and not home_run:
            self.switch_turn()
        else:
            self._turn_action_locked = False
            self.update_turn_indicator()

    def switch_turn(self):
        if getattr(self, "game_over", False):
            return
        self.can_move = False
        self.stop_pulsing()
        self.canvas.delete("anim_ring")
        # Skip players who have already finished all four tokens.
        if len(self.active_players) <= 1:
            self.game_over = True
            return
        for _ in range(len(self.active_players)):
            self.current_player_index = (self.current_player_index + 1) % len(self.active_players)
            candidate = self.turn_order[self.current_player_index]
            if candidate not in self.finish_order:
                break
        self._turn_action_locked = False
        self.dice_value = 0
        self.draw_tokens()
        self.draw_dice_button()
        self._save_turn_snapshot()
        self.update_turn_indicator()

    def update_turn_indicator(self):
        # No textual turn indicator: active player is identified only by the
        # coloured border around that player's personal dice box.
        self.draw_dice_button(val=self.dice_value if self.dice_value else None)

if __name__ == "__main__":
    root = tk.Tk()
    game = LudoGame(root)
    root.mainloop()
    