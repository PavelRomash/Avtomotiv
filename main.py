import sys
import psutil
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QWidget, QSlider, QHBoxLayout, QPushButton
from PyQt5.QtCore import QTimer, Qt, QTime

class SystemMonitor(QMainWindow):
    
    def __init__(self):
        
        """
        Конструктор класса SystemMonitor.
        Настраивает главное окно, виджеты для отображения показателей производительности, ползунок регулировки частоты обновления,
        кнопки запуска и остановки записи, а также метка для отображения времени записи.
        Также инициализирует QTimer для обновления показателей производительности и QTimer для обновления времени записи.
        Инициализирует соединение с базой данных и создает таблицу, если она не существует.
        """
        
        super().__init__()
        self.setWindowTitle("Мониторинг производительности системы")
        self.setGeometry(200, 200, 400, 350)

        """метки для отображения производительности"""
        self.cpu_label = QLabel("ЦП: ", self)
        self.ram_label = QLabel("ОЗУ: ", self)
        self.disk_label = QLabel("ПЗУ: ", self)
    
        """Интервал обновления в миллисекундах"""
        self.timer_interval = 1000
        
        """Слайдер для установки интервала обновления"""
        self.slider_label = QLabel("Обновление интервала: 1 секунда", self)  # Обновляемая метка с текущим значением
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)  # Минимальное значение в секундах
        self.slider.setMaximum(10)  # Максимальное значение в секундах
        self.slider.setValue(1)  # Начальное значение (1 секунда)
        self.slider.setTickInterval(1)  # Шаг отметок (1 секунда)
        self.slider.setTickPosition(QSlider.TicksBelow)  # Отображение отметок
        self.slider.valueChanged.connect(self.change_interval)
        
        """Кнопка записи"""
        self.record_button = QPushButton("Начать запись", self)
        self.record_button.clicked.connect(self.start_recording)

        """Кнопка остановки"""
        self.stop_button = QPushButton("Остановить", self)
        self.stop_button.setVisible(False)
        self.stop_button.clicked.connect(self.stop_recording)
        
        """Таймер записи"""
        self.timer_label = QLabel("Время записи: 00:00:00", self)
        self.timer_label.setVisible(False)

        layout = QVBoxLayout()
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.ram_label)
        layout.addWidget(self.disk_label)

        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.slider_label)
        slider_layout.addWidget(self.slider)
        layout.addLayout(slider_layout)
        layout.addWidget(self.record_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.timer_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(self.timer_interval)  

        self.record_timer = QTimer(self)
        self.record_timer.timeout.connect(self.update_recording_time)

        self.record_time = QTime(0, 0, 0)

        """Инициализация БД"""
        self.db_connection = sqlite3.connect("system_monitor.db")
        self.db_cursor = self.db_connection.cursor()
        self.create_table()
        self.recording = False

    def create_table(self):
        self.db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpu_load REAL,
                ram_usage REAL,
                disk_usage REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db_connection.commit()

    """Обновление метрик"""
    def update_stats(self):
        cpu_load = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        ram_usage = ram.percent
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent

        self.cpu_label.setText(f"ЦП: {cpu_load}%")
        self.ram_label.setText(f"ОЗУ: {ram_usage}%")
        self.disk_label.setText(f"ПЗУ: {disk_usage}%")

        """Запись в базу если кнопка активна"""
        if self.recording:
            self.db_cursor.execute(
                "INSERT INTO system_stats (cpu_load, ram_usage, disk_usage) VALUES (?, ?, ?)",
                (cpu_load, ram_usage, disk_usage)
            )
            self.db_connection.commit()

    """Изменение интервала"""
    def change_interval(self):
        seconds = self.slider.value()
        self.timer_interval = seconds * 1000  
        self.timer.setInterval(self.timer_interval)
        self.slider_label.setText(f"Обновить интервал: {seconds} секунд{'а' if seconds == 1  else 'ы'}")

    """Начало записи"""
    def start_recording(self):
        self.recording = True
        self.record_button.setVisible(False)
        self.stop_button.setVisible(True)
        self.timer_label.setVisible(True)
        self.record_time = QTime(0, 0, 0)
        self.timer_label.setText("Время записи: 00:00:00")
        self.record_timer.start(1000)

    """Остановка записи"""
    def stop_recording(self):
        self.recording = False
        self.record_button.setVisible(True)
        self.stop_button.setVisible(False)
        self.timer_label.setVisible(False)
        self.record_timer.stop()

    """Обновление времени записи"""
    def update_recording_time(self):
        self.record_time = self.record_time.addSecs(1)
        self.timer_label.setText(f"Время записи: {self.record_time.toString('hh:mm:ss')}")

    """Закрытие программы"""
    def closeEvent(self, event):
        self.db_connection.close()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    monitor = SystemMonitor()
    monitor.show()
    sys.exit(app.exec_())