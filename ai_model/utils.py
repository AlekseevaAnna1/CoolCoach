import numpy as np

def calculate_angle(a, b, c):
    """
    Вычисляет угол в точке b (в градусах).
    a, b, c - это координаты (x, y) в виде списков или кортежей [x, y].
    """
    # Переводим в numpy массивы для удобства
    a = np.array(a) 
    b = np.array(b) 
    c = np.array(c) 
    
    # Вычисляем векторы (b -> a) и (b -> c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    
    # Переводим радианы в градусы
    angle = np.abs(radians * 180.0 / np.pi)
    
    # Если угол больше 180, берем его дополнение до 360
    if angle > 180.0:
        angle = 360 - angle
        
    return angle