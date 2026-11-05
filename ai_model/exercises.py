import time
from utils import calculate_angle

class BaseExercise:
    def __init__(self):
        self.counter = 0
        self.stage = "up"
        self.errors = 0
        self.current_errors = []
        
    def reset(self):
        self.counter = 0
        self.stage = "up"
        self.errors = 0
        self.current_errors = []

class Squat(BaseExercise):
    def __init__(self):
        super().__init__()
        self.standing_angle = 170
        self.is_calibrated = False
        self.calibration_frames = 0
        self.start_hip_y = 0
        self.min_hip_y = 0
        self.wrong_depth_start_time = None
        self.low_angle_reached = False
        # Флаг, чтобы не считать одну и ту же ошибку 30 раз в секунду
        self.error_just_counted = False 

    def process(self, landmarks):
        r_hip, r_knee, r_ankle = [landmarks[24].x, landmarks[24].y], [landmarks[26].x, landmarks[26].y], [landmarks[28].x, landmarks[28].y]
        l_hip, l_knee, l_ankle = [landmarks[23].x, landmarks[23].y], [landmarks[25].x, landmarks[25].y], [landmarks[27].x, landmarks[27].y]
        r_sh = [landmarks[12].x, landmarks[12].y]
        r_ear = [landmarks[8].x, landmarks[8].y]

        knee_angle = calculate_angle(r_hip, r_knee, r_ankle)
        back_angle = calculate_angle(r_ear, r_sh, r_hip)

        avg_hip_y = r_hip[1]
        self.current_errors = []
        current_time = time.time()

        if not self.is_calibrated:
            if self.calibration_frames < 30:
                self.calibration_frames += 1
                self.current_errors.append("КАЛИБРОВКА... Встаньте ровно!")
            else:
                self.standing_angle = knee_angle
                self.start_hip_y = avg_hip_y
                self.min_hip_y = avg_hip_y
                self.is_calibrated = True
            return knee_angle

        # Логика движения
        if avg_hip_y > self.min_hip_y:
            self.min_hip_y = avg_hip_y

        if knee_angle < 150 and self.stage == "up":
            self.stage = "going_down"
            self.wrong_depth_start_time = None
            self.low_angle_reached = False
            self.error_just_counted = False # Сбрасываем флаг при новом движении

        if knee_angle < 100:
            self.low_angle_reached = True

        if knee_angle > 160 and self.stage in ["down", "going_down"]:
            self.stage = "up"
            
            if self.low_angle_reached:
                self.counter += 1
            else:
                # Ошибка: недосел. Считаем её ОДИН раз за это повторение.
                self.current_errors.append("Сядьте глубже")
                if not self.error_just_counted:
                    self.errors += 1
                    self.error_just_counted = True
                
            self.min_hip_y = avg_hip_y

        # --- ОШИБКИ В ПРОЦЕССЕ ---
        # Если ошибка возникла в процессе (например, колено ушло), считаем её 1 раз
        error_happened = False
        
        if self.stage in ["going_down", "down"]:
            if back_angle < 130:
                self.current_errors.append("Держите спину ровнее")
                error_happened = True
            if r_knee[0] > r_ankle[0] + 0.05:
                self.current_errors.append("Колено вперед носка")
                error_happened = True

        # Зависание
        if 100 < knee_angle < 140 and self.stage in ["going_down", "down"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Сядьте глубже" not in self.current_errors:
                    self.current_errors.append("Сядьте глубже")
                error_happened = True
        else:
            self.wrong_depth_start_time = None

        # Увеличиваем счетчик, если ошибка в процессе возникла впервые (а не каждый кадр)
        if error_happened and not self.error_just_counted:
            self.errors += 1
            self.error_just_counted = True
        
        # Если ошибок нет в текущем кадре (мы исправились), разрешаем считать следующую
        if not self.current_errors and not error_happened:
            self.error_just_counted = False

        return knee_angle


class PushUp(BaseExercise):
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.low_angle_reached = False

    def process(self, landmarks):
        r_sh, r_el, r_wr = [landmarks[12].x, landmarks[12].y], [landmarks[14].x, landmarks[14].y], [landmarks[16].x, landmarks[16].y]
        l_sh, l_el, l_wr = [landmarks[11].x, landmarks[11].y], [landmarks[13].x, landmarks[13].y], [landmarks[15].x, landmarks[15].y]
        r_hip, l_hip = [landmarks[24].x, landmarks[24].y], [landmarks[23].x, landmarks[23].y]
        nose = [landmarks[0].x, landmarks[0].y]

        angle_r = calculate_angle(r_sh, r_el, r_wr)
        angle_l = calculate_angle(l_sh, l_el, l_wr)
        avg_angle = (angle_r + angle_l) / 2
        
        # Угол тела (плечо-бедро-колено) для проверки провисания таза
        back_angle = calculate_angle(r_sh, r_hip, [landmarks[26].x, landmarks[26].y])

        self.current_errors = []
        current_time = time.time()

        # Логика движения
        if avg_angle < 150 and self.stage == "up":
            self.stage = "going_down"
            self.wrong_depth_start_time = None
            self.low_angle_reached = False

        if avg_angle < 95:
            self.low_angle_reached = True

        if avg_angle > 160 and self.stage in ["down", "going_down"]:
            self.stage = "up"
            self.counter += 1
            if not self.low_angle_reached:
                self.current_errors.append("Опуститесь ниже")
            self.wrong_depth_start_time = None

        # Проверка ошибок ОСАНКИ
        if self.stage in ["going_down", "down"]:
            # Провисание таза (угол тела прямой или выгнут)
            if back_angle > 190 or back_angle < 160:
                 self.current_errors.append("Держите тело прямым")
            # Голова слишком низко (нос близко к рукам)
            if nose[1] > r_sh[1] + 0.05:
                self.current_errors.append("Поднимите голову")

        # Зависание
        if 95 < avg_angle < 130 and self.stage in ["going_down", "down"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Опуститесь ниже" not in self.current_errors:
                    self.current_errors.append("Опуститесь ниже")
        else:
            self.wrong_depth_start_time = None

        return avg_angle


class Lunge(BaseExercise):
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.low_angle_reached = False

    def process(self, landmarks):
        r_hip, r_knee, r_ankle = [landmarks[24].x, landmarks[24].y], [landmarks[26].x, landmarks[26].y], [landmarks[28].x, landmarks[28].y]
        l_hip, l_knee, l_ankle = [landmarks[23].x, landmarks[23].y], [landmarks[25].x, landmarks[25].y], [landmarks[27].x, landmarks[27].y]
        r_sh = [landmarks[12].x, landmarks[12].y]

        angle_r = calculate_angle(r_hip, r_knee, r_ankle)
        angle_l = calculate_angle(l_hip, l_knee, l_ankle)
        bent_leg_angle = min(angle_r, angle_l)
        
        # Угол наклона корпуса
        torso_angle = calculate_angle(r_sh, r_hip, r_knee)

        self.current_errors = []
        current_time = time.time()

        # Логика движения
        if bent_leg_angle < 160 and self.stage == "up":
            self.stage = "going_down"
            self.wrong_depth_start_time = None
            self.low_angle_reached = False

        if bent_leg_angle < 105:
            self.low_angle_reached = True

        if bent_leg_angle > 160 and self.stage in ["down", "going_down"]:
            self.stage = "up"
            self.counter += 1
            if not self.low_angle_reached:
                self.current_errors.append("Согните колено глубже")
            self.wrong_depth_start_time = None

        # Проверка ошибок ОСАНКИ (наклон корпуса)
        if self.stage in ["going_down", "down"]:
            if torso_angle < 140:
                self.current_errors.append("Выпрямите спину")

        # Зависание
        if 105 < bent_leg_angle < 140 and self.stage in ["going_down", "down"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Опуститесь ниже" not in self.current_errors:
                    self.current_errors.append("Опуститесь ниже")
        else:
            self.wrong_depth_start_time = None

        return bent_leg_angle


class GluteBridge(BaseExercise):
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.high_angle_reached = False

    def process(self, landmarks):
        r_sh, r_hip, r_knee = [landmarks[12].x, landmarks[12].y], [landmarks[24].x, landmarks[24].y], [landmarks[26].x, landmarks[26].y]
        l_sh, l_hip, l_knee = [landmarks[11].x, landmarks[11].y], [landmarks[23].x, landmarks[23].y], [landmarks[25].x, landmarks[25].y]
        nose = [landmarks[0].x, landmarks[0].y]

        angle_r = calculate_angle(r_sh, r_hip, r_knee)
        angle_l = calculate_angle(l_sh, l_hip, l_knee)
        avg_angle = (angle_r + angle_l) / 2

        self.current_errors = []
        current_time = time.time()

        # Логика движения
        if avg_angle > 120 and self.stage == "down":
            self.stage = "going_up"
            self.wrong_depth_start_time = None
            self.high_angle_reached = False

        if avg_angle > 160:
            self.high_angle_reached = True

        if avg_angle < 120 and self.stage in ["up", "going_up"]:
            self.stage = "down"
            self.counter += 1
            if not self.high_angle_reached:
                self.current_errors.append("Поднимите таз выше")
            self.wrong_depth_start_time = None

        # Проверка ошибок ОСАНКИ
        if self.stage in ["going_up", "up"]:
            # Голова не должна быть запрокинута назад
            if nose[1] < r_sh[1] - 0.1:
                self.current_errors.append("Не запрокидывайте голову")

        # Зависание
        if 130 < avg_angle < 155 and self.stage in ["going_up", "up"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Поднимите таз выше" not in self.current_errors:
                    self.current_errors.append("Поднимите таз выше")
        else:
            self.wrong_depth_start_time = None

        return avg_angle