import customtkinter as ctk
import json, os, keyboard
from tkinter import colorchooser

CONFIG_FILE = "config.json"
ctk.set_appearance_mode("dark")

class MidnightReborn(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MIDNIGHT.MINER v15.9")
        self.geometry("850x700")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        self.cfg = {
            "master": True,
            "menu_alpha": 0.95,
            "main_color": "#a34cff",
            "autopilot": {"enabled": False, "speed": 0.12, "dist_stop": 180},
            "ore":  {"conf": 0.45, "logic": True, "draw": True, "color": "#00FF7F", "thick": 2, "name": True, "alpha": 1.0},
            "bar":  {"conf": 0.40, "logic": True, "draw": True, "color": "#FFD700", "thick": 2, "name": True, "alpha": 1.0},
            "rock": {"conf": 0.35, "logic": True, "draw": True, "color": "#ffffff", "thick": 2, "name": True, "alpha": 1.0},
            "crosshair": {"enabled": True, "color": "#ff0000", "thick": 2, "size": 10, "alpha": 1.0},
            "lines": {"enabled": True, "color": "#ffffff", "thick": 1, "alpha": 0.6}
        }
        self.load_from_file()
        self.main_neon = self.cfg.get("main_color", "#a34cff")
        self.attributes("-alpha", self.cfg["menu_alpha"])

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.nav_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#0e0e0e", border_width=1, border_color="#1f1f1f")
        self.nav_frame.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.nav_frame, text="PIZDAVIZN", font=("Arial Black", 24), text_color=self.main_neon).grid(row=0, column=0, padx=20, pady=30)

        self.create_nav_btn("ГЛАВНАЯ", self.show_core, 1)
        self.create_nav_btn("ВИЗУАЛ", lambda: self.show_visuals("ORE"), 2)
        self.create_nav_btn("АВТОПИЛОТ", self.show_autopilot_settings, 3)
        self.create_nav_btn("СИСТЕМА", self.show_settings, 4)

        self.container = ctk.CTkFrame(self, fg_color="#0b0b0b", corner_radius=0)
        self.container.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        
        self.is_visible = True
        keyboard.add_hotkey('insert', self.toggle_visibility, suppress=True)
        self.show_core()

    def create_nav_btn(self, text, command, row):
        btn = ctk.CTkButton(self.nav_frame, text=text, fg_color="transparent", text_color="gray", hover_color="#161616", anchor="w", font=("Arial", 12, "bold"), command=command)
        btn.grid(row=row, column=0, sticky="ew", padx=10, pady=2)

    def toggle_visibility(self):
        if self.is_visible: self.withdraw()
        else: self.deiconify(); self.focus_force()
        self.is_visible = not self.is_visible

    def clear_container(self):
        for w in self.container.winfo_children(): w.destroy()

    def show_core(self):
        self.clear_container()
        ctk.CTkLabel(self.container, text="ОСНОВНАЯ ЛОГИКА", font=("Arial", 22, "bold")).pack(anchor="w", pady=(0,20))
        self.master_sw = ctk.CTkSwitch(self.container, text="MASTER SWITCH (DEL)", progress_color=self.main_neon, command=self.save_to_file)
        if self.cfg["master"]: self.master_sw.select()
        self.master_sw.pack(pady=15, anchor="w")

        self.logic_switches = {}
        for name in ["ore", "bar", "rock"]:
            f = ctk.CTkFrame(self.container, fg_color="#161616", corner_radius=8); f.pack(fill="x", pady=5, padx=5)
            ctk.CTkLabel(f, text=f"Активировать логику {name.upper()}", font=("Arial", 13)).pack(side="left", padx=15, pady=10)
            sw = ctk.CTkSwitch(f, text="", progress_color=self.main_neon, command=self.save_to_file)
            if self.cfg[name]["logic"]: sw.select()
            sw.pack(side="right", padx=15); self.logic_switches[name] = sw

    def show_visuals(self, current_tab="ORE"):
        self.clear_container()
        tabview = ctk.CTkTabview(self.container, segmented_button_selected_color=self.main_neon)
        tabview.pack(fill="both", expand=True)
        self.esp_widgets = {}

        for item in ["ore", "bar", "rock", "crosshair", "lines"]:
            tab = tabview.add(item.upper()); self.esp_widgets[item] = {}
            if item in ["crosshair", "lines"]:
                en_sw = ctk.CTkSwitch(tab, text="Включить", progress_color=self.main_neon, command=self.save_to_file)
                if self.cfg[item]["enabled"]: en_sw.select()
                en_sw.pack(pady=10, anchor="w"); self.esp_widgets[item]["enabled"] = en_sw
            else:
                d_sw = ctk.CTkSwitch(tab, text="Рисовать Бокс", progress_color=self.main_neon, command=self.save_to_file)
                if self.cfg[item]["draw"]: d_sw.select()
                d_sw.pack(pady=5, anchor="w"); self.esp_widgets[item]["draw"] = d_sw
                ctk.CTkLabel(tab, text="Confidence (Порог):").pack(anchor="w", pady=(10,0))
                c_lbl = ctk.CTkLabel(tab, text=f"{int(self.cfg[item]['conf']*100)}%", text_color=self.main_neon); c_lbl.pack(anchor="e")
                c_sl = ctk.CTkSlider(tab, from_=0.05, to=0.95, command=lambda v, l=c_lbl: [l.configure(text=f"{int(v*100)}%"), self.save_to_file()])
                c_sl.set(self.cfg[item]["conf"]); c_sl.pack(fill="x"); self.esp_widgets[item]["conf"] = c_sl

            ctk.CTkLabel(tab, text="Толщина линий:").pack(anchor="w", pady=(10,0))
            t_sl = ctk.CTkSlider(tab, from_=1, to=10, number_of_steps=9, command=lambda v: self.save_to_file())
            t_sl.set(self.cfg[item]["thick"]); t_sl.pack(fill="x"); self.esp_widgets[item]["thick"] = t_sl
            ctk.CTkLabel(tab, text="Прозрачность:").pack(anchor="w", pady=(10,0))
            a_sl = ctk.CTkSlider(tab, from_=0.1, to=1.0, command=lambda v: self.save_to_file())
            a_sl.set(self.cfg[item]["alpha"]); a_sl.pack(fill="x"); self.esp_widgets[item]["alpha"] = a_sl
            ctk.CTkButton(tab, text="Выбрать цвет", fg_color=self.cfg[item]["color"], command=lambda n=item: self.pick_color(n)).pack(pady=20, fill="x")
        tabview.set(current_tab.upper())

    def show_autopilot_settings(self):
        self.clear_container()
        ctk.CTkLabel(self.container, text="АВТОПИЛОТ", font=("Arial", 22, "bold"), text_color="#ff4c4c").pack(anchor="w", pady=(0,20))
        self.auto_sw = ctk.CTkSwitch(self.container, text="Включить авто-движение", progress_color="#ff4c4c", command=self.save_to_file)
        if self.cfg["autopilot"]["enabled"]: self.auto_sw.select()
        self.auto_sw.pack(pady=10, anchor="w")
        ctk.CTkLabel(self.container, text="Скорость доводки:").pack(anchor="w", pady=(10,0))
        self.auto_speed_sl = ctk.CTkSlider(self.container, from_=0.01, to=0.5, command=lambda v: self.save_to_file())
        self.auto_speed_sl.set(self.cfg["autopilot"]["speed"]); self.auto_speed_sl.pack(fill="x")
        ctk.CTkLabel(self.container, text="Дистанция остановки (размер камня):").pack(anchor="w", pady=(10,0))
        self.auto_dist_sl = ctk.CTkSlider(self.container, from_=50, to=400, command=lambda v: self.save_to_file())
        self.auto_dist_sl.set(self.cfg["autopilot"]["dist_stop"]); self.auto_dist_sl.pack(fill="x")

    def show_settings(self):
        self.clear_container()
        ctk.CTkLabel(self.container, text="СИСТЕМА", font=("Arial", 22, "bold")).pack(anchor="w", pady=(0,20))
        ctk.CTkLabel(self.container, text="Прозрачность меню:").pack(anchor="w")
        self.m_alpha_sl = ctk.CTkSlider(self.container, from_=0.3, to=1.0, command=self.update_menu_alpha)
        self.m_alpha_sl.set(self.cfg["menu_alpha"]); self.m_alpha_sl.pack(fill="x", pady=10)
        ctk.CTkButton(self.container, text="ЦВЕТ ИНТЕРФЕЙСА", fg_color=self.main_neon, command=self.pick_ui_color).pack(fill="x", pady=10)
        faq_box = ctk.CTkTextbox(self.container, height=150); faq_box.pack(fill="both", expand=True)
        faq_box.insert("0.0", "INSERT - Меню\nDEL - Вкл/Выкл бота\nAUTOPILOT - Идет к Rock на 'W'\nБот игнорирует камни пока не докопает Bar и Ore.")
        faq_box.configure(state="disabled")

    def update_menu_alpha(self, v): self.attributes("-alpha", v); self.cfg["menu_alpha"] = v; self.save_to_file()
    def pick_ui_color(self):
        color = colorchooser.askcolor(initialcolor=self.main_neon)[1]
        if color: self.main_neon = color; self.cfg["main_color"] = color; self.save_to_file(); self.show_settings()
    def pick_color(self, name):
        color = colorchooser.askcolor(initialcolor=self.cfg[name]["color"])[1]
        if color: self.cfg[name]["color"] = color; self.save_to_file(); self.show_visuals(name)
    def save_to_file(self):
        self.cfg["master"] = bool(self.master_sw.get())
        if hasattr(self, 'logic_switches'):
            for n in ["ore", "bar", "rock"]: self.cfg[n]["logic"] = bool(self.logic_switches[n].get())
        if hasattr(self, 'auto_sw'):
            self.cfg["autopilot"]["enabled"] = bool(self.auto_sw.get())
            self.cfg["autopilot"]["speed"] = round(self.auto_speed_sl.get(), 2)
            self.cfg["autopilot"]["dist_stop"] = int(self.auto_dist_sl.get())
        if hasattr(self, 'esp_widgets'):
            for n, w in self.esp_widgets.items():
                if "draw" in w: self.cfg[n]["draw"] = bool(w["draw"].get())
                if "enabled" in w: self.cfg[n]["enabled"] = bool(w["enabled"].get())
                if "conf" in w: self.cfg[n]["conf"] = round(w["conf"].get(), 2)
                self.cfg[n]["thick"] = int(w["thick"].get()); self.cfg[n]["alpha"] = round(w["alpha"].get(), 2)
        with open(CONFIG_FILE, "w") as f: json.dump(self.cfg, f, indent=4)
    def load_from_file(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f: self.cfg.update(json.load(f))
            except: pass

if __name__ == "__main__":
    MidnightReborn().mainloop()