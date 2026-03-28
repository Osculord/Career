import subprocess
import sys
import time
import os

def start_bot():
    print("--- [PIZDAVIZN LOADER] ---")
    
    # Пути к твоим скриптам
    menu_script = "menuv12.py"
    engine_script = "botv12.py"

    # Запускаем Меню
    print("Запуск интерфейса...")
    menu_proc = subprocess.Popen([sys.executable, menu_script])

    # Запускаем Движок
    print("Запуск нейросети...")
    engine_proc = subprocess.Popen([sys.executable, engine_script])

    print("Все системы запущены! Нажми INSERT для управления.")

    try:
        # Держим загрузчик активным, пока работают процессы
        while True:
            if menu_proc.poll() is not None or engine_proc.poll() is not None:
                print("Один из процессов был закрыт. Завершение работы...")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("Принудительное завершение...")
    finally:
        menu_proc.terminate()
        engine_proc.terminate()
if __name__ == "__main__":
    start_bot()