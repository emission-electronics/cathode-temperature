import cv2
import numpy as np
from typing import Tuple, Optional
from collections import deque

from PyQt6.QtCore import QThread, pyqtSignal

from scipy.interpolate import splprep, splev
import heapq

class VideoThread(QThread):
    """
    Поток для захвата и обработки видео с камеры.
    
    Сигналы:
        change_pixmap_signal: Передает кадр видео
        roi_signal: Передает ROI
    """
    change_pixmap_signal = pyqtSignal(np.ndarray)
    roi_signal = pyqtSignal(np.ndarray)
    average_roi_signal = pyqtSignal(np.ndarray)
    
    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.running = True
        self.drawing = False
        self.start_x, self.start_y = -1, -1
        self.end_x, self.end_y = -1, -1
        self.roi_selected = False
        self.original_frame = None
        self.roi = None
        self.average_roi = None
        self.roi_buffer = deque(np.array([]), maxlen=20)
    
    def run(self):
        """Основной цикл захвата и обработки видео"""
        cap = cv2.VideoCapture(self.camera_index)
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Сохраняем оригинальный кадр для вырезания ROI
            self.original_frame = frame.copy()
            
            # Отправляем кадр для отображения
            self.change_pixmap_signal.emit(frame)
            
            # Если область выделена, обрабатываем её
            if self.roi_selected and self.original_frame is not None:
                self._process_roi()
            
            # Небольшая задержка, чтобы не перегружать CPU
            self.msleep(30)
        
        cap.release()

    def _process_roi(self):
        """Обработка выделенной области интереса (ROI)"""
        # Определяем координаты прямоугольника в правильном порядке
        x1, y1 = min(self.start_x, self.end_x), min(self.start_y, self.end_y)
        x2, y2 = max(self.start_x, self.end_x), max(self.start_y, self.end_y)
        
        if self.original_frame is None:
            return

        # Проверяем границы изображения
        h, w = self.original_frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        # Проверяем, что область имеет размер
        if x1 < x2 and y1 < y2:
            # Выделяем выбранную область
            roi = self.original_frame[y1:y2, x1:x2]
            
            # Проверяем, что ROI не пустой
            if roi.size > 0:
                # Обработка ROI
                self.roi_buffer.append(roi.copy())
                roi_float = [img.astype(np.float32) for img in self.roi_buffer]
                average_roi = np.array(sum(roi_float) / len(roi_float)).astype(np.uint8)
                
                self.roi = roi.copy()
                self.average_roi = average_roi.copy()
                
                # Отправляем сигнал с ROI
                self.roi_signal.emit(roi)
                self.average_roi_signal.emit(average_roi)

    def handle_mouse_event(self, event_type: str, x: int, y: int) -> None:
        """
        Обработка событий мыши
        
        Args:
            event_type: Тип события ("press", "move", "release")
            x: Координата X
            y: Координата Y
        """
        if event_type == "press":
            self.drawing = True
            self.start_x, self.start_y = x, y
            self.end_x, self.end_y = x, y
            self.roi_selected = False
        
        elif event_type == "move" and self.drawing:
            self.end_x, self.end_y = x, y
        
        elif event_type == "release":
            self.roi_buffer.clear()
            self.end_x, self.end_y = x, y
            # Проверяем, что выделена реальная область, а не точка
            if abs(self.end_x - self.start_x) > 5 and abs(self.end_y - self.start_y) > 5:
                self.drawing = False
                self.roi_selected = True
            else:
                # Если выделение слишком маленькое, сбрасываем
                self.drawing = False
                self.roi_selected = False

    def stop(self):
        """Останавливает поток обработки видео"""
        self.running = False
        self.wait()
