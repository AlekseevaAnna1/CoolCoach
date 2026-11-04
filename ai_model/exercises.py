from utils import calculate_angle

class BaseExercise:
    def __init__(self):
        self.counter = 0
        self.stage = "up"
        self.errors = 0
        self.current_error_text = ""
        self.error_counted = False # <--- НОВЫЙ ФЛАГ
        
    def reset(self):
        self.counter = 0
        self.stage = "up"
        self.errors = 0
        self.current_error_text = ""
        self.error_counted = False

class Squat(BaseExercise):
    def __init__(self):
        super().__init__()
        self.standing_angle = 170
        self.is_calibrated = False
        self.calibration_frames = 0
        self.start_hip_y = 0
        self.min_hip_y = 0  # Запоминаем самую низкую точку таза

    def process(self, landmarks):
        r_hip = [landmarks[24].x, landmarks[24].y]
        r_knee = [landmarks[26].x, landmarks[26].y]
        r_ankle = [landmarks[28].x, landmarks[28].y]
        
        l_hip = [landmarks[23].x, landmarks[23].y]
        l_knee = [landmarks[25].x, landmarks[25].y]
        l_ankle = [landmarks[27].x, landmarks[27].y]

        angle_r = calculate_angle(r_hip, r_knee, r_ankle)
        angle_l = calculate_angle(l_hip, l_knee, l_ankle)
        avg_angle = (angle_r + angle_l) / 2
        
        avg_hip_y = (r_hip[1] + l_hip[1]) / 2
        
        self.current_error_text = ""

        if not self.is_calibrated:
            if self.calibration_frames < 30:
                self.calibration_frames += 1
                self.current_error_text = "КАЛИБРОВКА... Встаньте ровно!"
            else:
                self.standing_angle = avg_angle
                self.start_hip_y = avg_hip_y
                self.min_hip_y = avg_hip_y
                self.is_calibrated = True
            return avg_angle

        # --- ЛОГИКА ---
        # Если таз опустился ниже, чем был в начале, запоминаем эту точку
        if avg_hip_y > self.min_hip_y:
            self.min_hip_y = avg_hip_y

        # Присед: угол маленький, и таз действительно опустился
        if avg_angle < 110 and self.min_hip_y > (self.start_hip_y + 0.03):
            self.stage = "down"
            
        # Встали: угол прямой, и мы до этого были внизу
        if avg_angle > 160 and self.stage == "down":
            self.stage = "up"
            self.counter += 1
            self.error_counted = False
            self.min_hip_y = avg_hip_y # Сбрасываем нижнюю точку для нового подхода

        # Ошибка (недосел)
        if 110 < avg_angle < 140 and self.stage == "up" and not self.error_counted:
            self.current_error_text = "Сядьте глубже"
            self.errors += 1
            self.error_counted = True

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