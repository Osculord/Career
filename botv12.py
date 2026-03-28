import json, os, cv2, time, mss, numpy as np
from ultralytics import YOLO
import tkinter as tk
import win32api, win32con, pydirectinput, keyboard
import gc

CONFIG_FILE = "config.json"
RES = (2560, 1440) 
CX, CY = RES[0] // 2, RES[1] // 2
pydirectinput.PAUSE = 0

# СОСТОЯНИЯ
STATE_SEARCH = "SEARCH"
STATE_MINING = "MINING"

bot_state = STATE_SEARCH
last_bar_seen = 0
last_ore_seen = 0
last_e_press = 0

# ПАМЯТЬ
object_memory = {
    "rock": {"pos": None, "time": 0, "limit": 2.5},
    "ore":  {"pos": None, "time": 0, "limit": 1.5},
    "bar":  {"pos": None, "time": 0, "limit": 1.5}
}

def load_cfg_safe():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return None

def smooth_move(target_x, speed):
    diff_x = target_x - CX
    if abs(diff_x) > 15:
        move_x = int(diff_x * speed)
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, move_x, 0, 0, 0)

def fast_click():
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    time.sleep(0.01)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

def run_engine():
    global bot_state, last_bar_seen, last_ore_seen, last_e_press
    try: 
        model = YOLO("last.pt") 
    except: 
        print("Веса не найдены!"); return

    gc_counter = 0
    w_is_down = False

    root = tk.Tk()
    root.geometry(f"{RES[0]}x{RES[1]}+0+0")
    root.overrideredirect(True)
    root.attributes("-topmost", True, "-transparentcolor", "black")
    root.config(bg='black')
    canvas = tk.Canvas(root, width=RES[0], height=RES[1], bg='black', highlightthickness=0)
    canvas.pack()

    with mss.mss() as sct:
        monitor = {"top": 0, "left": 0, "width": RES[0], "height": RES[1]}
        while True:
            cfg = load_cfg_safe()
            canvas.delete("all")
            now = time.time()

            if keyboard.is_pressed('delete'):
                if cfg:
                    cfg["master"] = not cfg["master"]
                    with open(CONFIG_FILE, "w") as f: json.dump(cfg, f, indent=4)
                    time.sleep(0.3)

            if cfg and cfg.get("master"):
                # --- ОТРИСОВКА ПРИЦЕЛА (ВЕРНУЛ) ---
                ch = cfg.get("crosshair", {})
                if ch.get("enabled"):
                    s = ch.get("size", 10)
                    canvas.create_line(CX-s, CY, CX+s, CY, fill=ch.get("color", "red"), width=ch.get("thick", 2))
                    canvas.create_line(CX, CY-s, CX, CY+s, fill=ch.get("color", "red"), width=ch.get("thick", 2))

                # Выход из режима MINING
                if bot_state == STATE_MINING:
                    if (now - last_bar_seen > 1.8) and (now - last_ore_seen > 1.8):
                        bot_state = STATE_SEARCH

                try:
                    sct_img = sct.grab(monitor)
                    img = np.frombuffer(sct_img.rgb, dtype=np.uint8).reshape((sct_img.height, sct_img.width, 3))
                    frame = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                    results = model.predict(frame, conf=0.25, verbose=False, imgsz=640)[0]

                    current_frame_rock = None
                    max_y = 0

                    for box in results.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        bx, by = (x1 + x2) // 2, (y1 + y2) // 2
                        h_box = y2 - y1
                        
                        # --- КОРРЕКЦИЯ ИНДЕКСОВ ---
                        raw_cls = int(box.cls[0])
                        if raw_cls == 0: name = 'bar'
                        elif raw_cls == 1: name = 'ore'
                        elif raw_cls == 2: name = 'rock'
                        else: name = model.names[raw_cls]
                        
                        prob = float(box.conf[0])
                        if name not in cfg or prob < cfg[name].get("conf", 0.25): continue

                        # ОБНОВЛЯЕМ ПАМЯТЬ
                        object_memory[name]["pos"] = (bx, by, h_box)
                        object_memory[name]["time"] = now

                        # ESP: ЛИНИИ (ВЕРНУЛ)
                        ln = cfg.get("lines", {})
                        if ln.get("enabled"):
                            canvas.create_line(CX, CY, bx, by, fill=ln.get("color", "white"), width=ln.get("thick", 1))

                        # ESP: БОКСЫ
                        if cfg[name]["draw"]:
                            canvas.create_rectangle(x1, y1, x2, y2, outline=cfg[name]["color"], width=cfg[name]["thick"])
                            canvas.create_text(x1, y1-15, text=f"{name.upper()} {int(prob*100)}%", fill=cfg[name]["color"], font=("Arial", 10, "bold"))

                        # ЛОГИКА ROCK (Нажатие E при приближении)
                        if name == 'rock' and cfg[name]["logic"]:
                            if h_box >= cfg["autopilot"]["dist_stop"] and bot_state == STATE_SEARCH:
                                if now - last_e_press > 2.5:
                                    pydirectinput.press('e')
                                    last_e_press = now
                                    bot_state = STATE_MINING

                            if bot_state == STATE_SEARCH and y2 > max_y: 
                                max_y = y2
                                current_frame_rock = (bx, by, h_box)

                        # ЛОГИКА BAR / ORE
                        if cfg[name]["logic"]:
                            if name == 'bar':
                                last_bar_seen = now; bot_state = STATE_MINING
                                fast_click()
                            elif name == 'ore':
                                last_ore_seen = now; bot_state = STATE_MINING
                                win32api.SetCursorPos((bx, by)); fast_click()

                    # --- АВТОПИЛОТ (ТОЛЬКО ДВИЖЕНИЕ) ---
                    if cfg["autopilot"]["enabled"]:
                        target = None
                        if current_frame_rock: target = current_frame_rock
                        elif now - object_memory["rock"]["time"] < 2.0: target = object_memory["rock"]["pos"]

                        if target and bot_state == STATE_SEARCH:
                            tx, ty, th = target
                            smooth_move(tx, cfg["autopilot"]["speed"])
                            
                            if th < cfg["autopilot"]["dist_stop"]:
                                if not w_is_down:
                                    pydirectinput.keyDown('w'); w_is_down = True
                            else:
                                if w_is_down:
                                    pydirectinput.keyUp('w'); w_is_down = False
                        else:
                            if w_is_down:
                                pydirectinput.keyUp('w'); w_is_down = False
                    
                except: pass

            root.update()
            gc_counter += 1
            if gc_counter > 50: gc.collect(); gc_counter = 0
            time.sleep(0.005)

if __name__ == "__main__":
    run_engine()