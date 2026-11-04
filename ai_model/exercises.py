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
        self.start_hip_y = 0  # Запоминаем высоту таза в начале

    def process(self, landmarks):
        # Точки ног
        r_hip = [landmarks[24].x, landmarks[24].y]
        r_knee = [landmarks[26].x, landmarks[26].y]
        r_ankle = [landmarks[28].x, landmarks[28].y]
        
        l_hip = [landmarks[23].x, landmarks[23].y]
        l_knee = [landmarks[25].x, landmarks[25].y]
        l_ankle = [landmarks[27].x, landmarks[27].y]

        angle_r = calculate_angle(r_hip, r_knee, r_ankle)
        angle_l = calculate_angle(l_hip, l_knee, l_ankle)
        avg_angle = (angle_r + angle_l) / 2
        
        # Средняя координата Y таза (чем больше Y, тем ниже таз на экране)
        avg_hip_y = (r_hip[1] + l_hip[1]) / 2
        
        self.current_error_text = ""

        if not self.is_calibrated:
            if self.calibration_frames < 30:
                self.calibration_frames += 1
                self.current_error_text = "КАЛИБРОВКА... Встаньте ровно!"
            else:
                self.standing_angle = avg_angle
                self.start_hip_y = avg_hip_y # Запоминаем, где таз в положении стоя
                self.is_calibrated = True
            return avg_angle

        # --- ЛОГИКА ПРИСЕДАНИЙ ---
        # Присед засчитывается, только если угол маленький И таз реально опустился
        hip_dropped = avg_hip_y > (self.start_hip_y + 0.05) 

        if avg_angle < 110 and hip_dropped:
            self.stage = "down"
            
        if avg_angle > 160 and self.stage == "down":
            self.stage = "up"
            self.counter += 1
            self.error_counted = False

        # Проверка ошибки (слишком высоко)
        if 110 < avg_angle < 140 and self.stage == "up" and not self.error_counted:
            self.current_error_text = "Сядьте глубже"
            self.errors += 1
            self.error_counted = True

        return avg_angle

class PushUp(BaseExercise):
    def process(self, landmarks):
        r_sh, r_el, r_wr = [landmarks[12].x, landmarks[12].y], [landmarks[14].x, landmarks[14].y], [landmarks[16].x, landmarks[16].y]
        l_sh, l_el, l_wr = [landmarks[11].x, landmarks[11].y], [landmarks[13].x, landmarks[13].y], [landmarks[15].x, landmarks[15].y]

        angle_r = calculate_angle(r_sh, r_el, r_wr)
        angle_l = calculate_angle(l_sh, l_el, l_wr)
        avg_angle = (angle_r + angle_l) / 2

        self.current_error_text = ""
        if avg_angle < 90:
            self.stage = "down"
        if avg_angle > 160 and self.stage == "down":
            self.stage = "up"
            self.counter += 1

        return avg_angle

class Lunge(BaseExercise):
    def process(self, landmarks):
        r_hip, r_knee = [landmarks[24].x, landmarks[24].y], [landmarks[26].x, landmarks[26].y]
        angle_r = calculate_angle([landmarks[12].x, landmarks[12].y], r_hip, r_knee)
        
        self.current_error_text = ""
        if angle_r < 120:
            self.stage = "down"
        if angle_r > 160 and self.stage == "down":
            self.stage = "up"
            self.counter += 1
            
        if self.stage == "down" and angle_r > 140:
            self.current_error_text = "Опуститесь ниже"
            self.errors += 1

        return angle_r

class GluteBridge(BaseExercise):
    def process(self, landmarks):
        r_shoulder = [landmarks[12].x, landmarks[12].y]
        r_hip = [landmarks[24].x, landmarks[24].y]
        r_knee = [landmarks[26].x, landmarks[26].y]
        
        angle = calculate_angle(r_shoulder, r_hip, r_knee)
        
        self.current_error_text = ""
        
        if angle < 140:
            self.stage = "down"
        if angle > 160 and self.stage == "down":
            self.stage = "up"
            self.counter += 1

        if self.stage == "up" and angle < 150:
            self.current_error_text = "Поднимите таз выше"
            self.errors += 1

        return angle