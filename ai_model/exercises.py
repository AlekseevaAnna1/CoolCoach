from utils import calculate_angle
import time

class BaseExercise:
    def __init__(self):
        self.counter = 0
        self.stage = "up"
        self.errors = 0
        self.current_errors = [] # <--- Теперь это СПИСОК ошибок
        self.spoken_errors = []  # Запоминаем, что уже озвучили
        
    def reset(self):
        self.counter = 0
        self.stage = "up"
        self.errors = 0
        self.current_errors = []
        self.spoken_errors = []


class Squat(BaseExercise):
    def __init__(self):
        super().__init__()
        self.standing_angle = 170
        self.is_calibrated = False
        self.calibration_frames = 0
        self.start_hip_y = 0
        self.min_hip_y = 0
        
        # Переменные для отслеживания времени
        self.wrong_depth_start_time = None 
        self.low_angle_reached = False # Флаг: дошел ли он до нужной глубины

    def process(self, landmarks):
        r_hip, r_knee, r_ankle = [landmarks[24].x, landmarks[24].y], [landmarks[26].x, landmarks[26].y], [landmarks[28].x, landmarks[28].y]
        l_hip, l_knee, l_ankle = [landmarks[23].x, landmarks[23].y], [landmarks[25].x, landmarks[25].y], [landmarks[27].x, landmarks[27].y]

        angle_r = calculate_angle(r_hip, r_knee, r_ankle)
        angle_l = calculate_angle(l_hip, l_knee, l_ankle)
        avg_angle = (angle_r + angle_l) / 2
        
        avg_hip_y = (r_hip[1] + l_hip[1]) / 2
        
        self.current_errors = []

        if not self.is_calibrated:
            if self.calibration_frames < 30:
                self.calibration_frames += 1
                self.current_errors.append("КАЛИБРОВКА... Встаньте ровно!")
            else:
                self.standing_angle = avg_angle
                self.start_hip_y = avg_hip_y
                self.min_hip_y = avg_hip_y
                self.is_calibrated = True
            return avg_angle

        current_time = time.time()

        # --- ЛОГИКА ---
        if avg_hip_y > self.min_hip_y:
            self.min_hip_y = avg_hip_y

        # Если мы начали опускаться (угол стал меньше 150)
        if avg_angle < 150 and self.stage == "up":
            self.stage = "going_down"
            self.wrong_depth_start_time = None # Сбрасываем таймер
            self.low_angle_reached = False

        # Если мы достигли нужной глубины
        if avg_angle < 100:
            self.low_angle_reached = True

        # Если мы вернулись наверх
        if avg_angle > 160 and self.stage in ["down", "going_down"]:
            self.stage = "up"
            self.counter += 1
            
            # Ошибка: вернулся наверх, но не сел глубоко
            if not self.low_angle_reached:
                self.current_errors.append("Сядьте глубже")
            
            self.min_hip_y = avg_hip_y

        # --- ПРОВЕРКА "ЗАВИСАНИЯ" В НЕПРАВИЛЬНОЙ ПОЗЕ ---
        # Если мы находимся в нижней точке, но угол больше 100 (недосел)
        if 100 < avg_angle < 140 and self.stage in ["going_down", "down"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5: # Ждем 1.5 секунды
                self.current_errors.append("Сядьте глубже")
        else:
            self.wrong_depth_start_time = None

        return avg_angle

class PushUp(BaseExercise):
    def process(self, landmarks):
        # Плечи, локти, запястья
        r_sh, r_el, r_wr = [landmarks[12].x, landmarks[12].y], [landmarks[14].x, landmarks[14].y], [landmarks[16].x, landmarks[16].y]
        l_sh, l_el, l_wr = [landmarks[11].x, landmarks[11].y], [landmarks[13].x, landmarks[13].y], [landmarks[15].x, landmarks[15].y]

        angle_r = calculate_angle(r_sh, r_el, r_wr)
        angle_l = calculate_angle(l_sh, l_el, l_wr)
        avg_angle = (angle_r + angle_l) / 2

        self.current_error_text = ""
        
        # Опускание (угол в локте меньше 90)
        if avg_angle < 90:
            self.stage = "down"
            
        # Подъем (угол больше 160) + проверка, что мы реально были внизу
        if avg_angle > 160 and self.stage == "down":
            self.stage = "up"
            self.counter += 1
            self.error_counted = False # Сбрасываем флаг ошибки

        # Ошибка: если локти не согнулись достаточно (глубина)
        if 90 < avg_angle < 120 and self.stage == "up" and not self.error_counted:
            self.current_error_text = "Опуститесь ниже"
            self.errors += 1
            self.error_counted = True

        return avg_angle


class Lunge(BaseExercise):
    def process(self, landmarks):
        # Для выпадов главное - угол передней ноги. 
        # Берем правую ногу (если вы делаете выпад левой, программа все равно увидит согнутую ногу)
        r_hip, r_knee, r_ankle = [landmarks[24].x, landmarks[24].y], [landmarks[26].x, landmarks[26].y], [landmarks[28].x, landmarks[28].y]
        l_hip, l_knee, l_ankle = [landmarks[23].x, landmarks[23].y], [landmarks[25].x, landmarks[25].y], [landmarks[27].x, landmarks[27].y]

        angle_r = calculate_angle(r_hip, r_knee, r_ankle)
        angle_l = calculate_angle(l_hip, l_knee, l_ankle)
        
        # В выпаде одна нога согнута (угол ~90), другая прямая (угол ~170)
        # Берем ту ногу, которая согнута сильнее
        bent_leg_angle = min(angle_r, angle_l)

        self.current_error_text = ""

        # Присели в выпаде (колено согнуто)
        if bent_leg_angle < 110:
            self.stage = "down"
            
        # Вернулись в исходное (нога выпрямилась)
        if bent_leg_angle > 150 and self.stage == "down":
            self.stage = "up"
            self.counter += 1
            self.error_counted = False

        # Ошибка: колено выходит за носок (проверяем по X-координате)
        # Если колено ушло вперед дальше, чем носок (или лодыжка)
        if self.stage == "down":
            # Для правой ноги
            if angle_r < 110 and r_knee[0] > r_ankle[0] + 0.05 and not self.error_counted:
                self.current_error_text = "Колено выходит за носок"
                self.errors += 1
                self.error_counted = True
            # Для левой ноги
            elif angle_l < 110 and l_knee[0] < l_ankle[0] - 0.05 and not self.error_counted:
                self.current_error_text = "Колено выходит за носок"
                self.errors += 1
                self.error_counted = True

        return bent_leg_angle


class GluteBridge(BaseExercise):
    def process(self, landmarks):
        # В мостике мы смотрим на угол между плечом, бедром и коленом.
        # Когда таз на полу - угол острый. Когда поднят - прямой (180).
        r_sh, r_hip, r_knee = [landmarks[12].x, landmarks[12].y], [landmarks[24].x, landmarks[24].y], [landmarks[26].x, landmarks[26].y]
        l_sh, l_hip, l_knee = [landmarks[11].x, landmarks[11].y], [landmarks[23].x, landmarks[23].y], [landmarks[25].x, landmarks[25].y]

        angle_r = calculate_angle(r_sh, r_hip, r_knee)
        angle_l = calculate_angle(l_sh, l_hip, l_knee)
        avg_angle = (angle_r + angle_l) / 2

        self.current_error_text = ""

        # Если угол прямой (таз наверху)
        if avg_angle > 160:
            self.stage = "up"
            
        # Если таз опустился (угол стал острым) и мы до этого были наверху
        if avg_angle < 130 and self.stage == "up":
            self.stage = "down"
            self.counter += 1
            self.error_counted = False

        # Ошибка: если таз поднят, но недостаточно высоко
        if 140 < avg_angle < 155 and self.stage == "up" and not self.error_counted:
            self.current_error_text = "Поднимите таз выше"
            self.errors += 1
            self.error_counted = True

        return avg_angle