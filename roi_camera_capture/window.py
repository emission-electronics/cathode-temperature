import cv2
import numpy as np
import os
from datetime import datetime
from PIL import Image

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QComboBox
)
from PyQt6.QtCore import pyqtSlot, Qt

from threads import VideoThread
from views import ZoomableImageView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Анализ яркости нити")
        self.showFullScreen()
                
        self.camera_tab = QWidget()
        self.setCentralWidget(self.camera_tab)
        camera_layout = QHBoxLayout(self.camera_tab)
        
        # Верхняя панель с видео и выбором камеры
        top_panel = QWidget()
        top_layout = QVBoxLayout(top_panel)
                
        # Виджет для отображения видео с возможностью зума
        self.video_view = ZoomableImageView()
        self.video_view.setMinimumSize(800, 600)
        top_layout.addWidget(self.video_view)
        
        # Добавляем подсказку по использованию
        help_label = QLabel("Колесико мыши для масштабирования, ЛКМ для выделения области, ПКМ для перемещения")
        help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(help_label)
    
        # Панель с кнопками
        button_panel = QWidget()
        button_layout = QHBoxLayout(button_panel)

        # Добавляем выпадающий список камер
        self.camera_combo = QComboBox()
        
        self.available_cameras = self.get_available_cameras()
        if not self.available_cameras:
            raise Exception("No cameras found")
        for i, camera_name in enumerate(self.available_cameras):
            self.camera_combo.addItem(f"{i}: {camera_name}")
        
        self.camera_combo.currentIndexChanged.connect(self.camera_changed)
        button_layout.addWidget(self.camera_combo)
                
        # Кнопка для сохранения всех изображений
        self.save_all_button = QPushButton("Сохранить все изображения")
        self.save_all_button.clicked.connect(self.save_all_images)
        button_layout.addWidget(self.save_all_button)
        
        top_layout.addWidget(button_panel)
        camera_layout.addWidget(top_panel)

        # Нижняя панель для ROI, маски и анализа
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        
        # ROI виджет с возможностью зума
        self.roi_view = ZoomableImageView()
        self.roi_view.setMinimumSize(320, 240)
        bottom_layout.addWidget(self.roi_view)

        self.average_roi_view = ZoomableImageView()
        self.average_roi_view.setMinimumSize(320, 240)
        bottom_layout.addWidget(self.average_roi_view)

        camera_layout.addWidget(bottom_panel)
                        
        # Статус бар
        self.status_bar = self.statusBar()
        if self.status_bar is not None:
            self.status_bar.showMessage("Готов")
        
        # Создаем поток для обработки видео с выбранной камерой
        self.video_thread = VideoThread(-1)
        
        # Соединяем сигналы мыши
        self.video_view.mouse_pressed.connect(self.on_mouse_pressed)
        self.video_view.mouse_moved.connect(self.on_mouse_moved)
        self.video_view.mouse_released.connect(self.on_mouse_released)
        
        # Запускаем потоки
        self.camera_changed(0)
    
    def get_available_cameras(self):
        """Получает список доступных камер"""
        camera_names = []
        
        # Проверяем до 5 возможных камер
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # Пытаемся получить имя устройства (не всегда доступно)
                # В некоторых системах можно использовать cap.get(cv2.CAP_PROP_DEVICE_NAME)
                camera_names.append(f"Камера {i}")
                cap.release()
            else:
                break
        
        # Если не найдено ни одной камеры, добавляем заглушку
        if not camera_names:
            camera_names.append("Камера не найдена")
        
        return camera_names
    
    def camera_changed(self, index: int):
        """Обработчик изменения выбранной камеры"""
        if index < 0 or index >= len(self.available_cameras):
            return
        
        self.current_camera_index = index
        
        if self.video_thread is None:
            self.video_thread = VideoThread(self.current_camera_index)
        elif self.video_thread.isRunning():
            self.video_thread.stop()
        
        # Создаем и запускаем новый поток с выбранной камерой
        self.video_thread = VideoThread(self.current_camera_index)
        self.video_thread.change_pixmap_signal.connect(self.update_video)
        self.video_thread.roi_signal.connect(self.update_roi)
        self.video_thread.average_roi_signal.connect(self.update_average_roi)
        self.video_thread.start()
        if self.status_bar is not None:
            self.status_bar.showMessage(f"Переключение на камеру {index}: {self.available_cameras[index]}")
    
    @pyqtSlot(np.ndarray)
    def update_video(self, cv_img: np.ndarray):
        """Обновляем изображение с камеры"""
        self.video_view.setImage(cv_img)
    
    @pyqtSlot(np.ndarray, np.ndarray)
    def update_roi(self, roi: np.ndarray, xyl: np.ndarray):
        """Обновляем ROI и отправляем данные для анализа"""
        self.roi_view.setImage(roi)
        if self.status_bar is not None:
            self.status_bar.showMessage(f"Выделена область: x={xyl[0]}:{xyl[2]}, y={xyl[1]}:{xyl[3]}")
    
    @pyqtSlot(np.ndarray)
    def update_average_roi(self, roi: np.ndarray):
        """Обновляем ROI и отправляем данные для анализа"""
        self.average_roi_view.setImage(roi)

    def save_all_images(self):
        """Сохранить все изображения с одним базовым именем"""
        if (self.video_thread.original_frame is None or 
            self.video_thread.roi is None or 
            self.video_thread.average_roi is None):
            if self.status_bar is not None:
                self.status_bar.showMessage(f"Нет изображений для сохранения", 5000)
            return
            
        timestamp = datetime.now().strftime(r"%Y-%m-%d_%H-%M-%S")
        directory = "out"
        if not os.path.exists(directory):
            os.makedirs(directory)
        default_name = os.path.join(directory, f"image_{timestamp}")
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Задайте базовое имя файла", default_name, 
            "Все файлы (*)"
        )
        
        if filename:
            Image.fromarray(cv2.cvtColor(
                self.video_thread.original_frame, cv2.COLOR_BGR2RGB
            )).save(f"{filename}_orig.png")
            Image.fromarray(cv2.cvtColor(
                self.video_thread.roi, cv2.COLOR_BGR2RGB
            )).save(f"{filename}_roi.png")
            Image.fromarray(cv2.cvtColor(
                self.video_thread.average_roi, cv2.COLOR_BGR2RGB
            )).save(f"{filename}_av_roi.png")

            if self.status_bar is not None:
                self.status_bar.showMessage(f"Все изображения сохранены с базовым именем {filename}", 5000)
    
    def on_mouse_pressed(self, x, y):
        """Обработчик нажатия кнопки мыши на видео"""
        self.video_thread.handle_mouse_event("press", x, y)
    
    def on_mouse_moved(self, x, y):
        """Обработчик движения мыши на видео"""
        self.video_thread.handle_mouse_event("move", x, y)
    
    def on_mouse_released(self, x, y):
        """Обработчик отпускания кнопки мыши на видео"""
        self.video_thread.handle_mouse_event("release", x, y)
    
    def keyPressEvent(self, a0):
        if a0 is None:
            return
        if a0.key() == Qt.Key.Key_Escape:
            self.close()
    
    def closeEvent(self, a0):
        if a0 is None:
            return
        self.video_thread.stop()
        a0.accept()
