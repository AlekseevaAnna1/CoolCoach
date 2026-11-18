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

    import time
from utils import calculate_angle


class Crunch(BaseExercise):
    """Пресс — подъёмы корпуса лёжа."""
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.high_angle_reached = False

    def process(self, landmarks):
        r_sh = [landmarks[12].x, landmarks[12].y]
        r_hip = [landmarks[24].x, landmarks[24].y]
        r_knee = [landmarks[26].x, landmarks[26].y]
        l_sh = [landmarks[11].x, landmarks[11].y]
        l_hip = [landmarks[23].x, landmarks[23].y]
        l_knee = [landmarks[25].x, landmarks[25].y]

        angle_r = calculate_angle(r_sh, r_hip, r_knee)
        angle_l = calculate_angle(l_sh, l_hip, l_knee)
        avg_angle = (angle_r + angle_l) / 2

        self.current_errors = []
        current_time = time.time()

        # Лёжа — угол маленький (~90-120), поднялись — больше (~140+)
        if avg_angle > 130 and self.stage == "down":
            self.stage = "going_up"
            self.wrong_depth_start_time = None
            self.high_angle_reached = False

        if avg_angle > 145:
            self.high_angle_reached = True

        if avg_angle < 125 and self.stage in ["up", "going_up"]:
            self.stage = "down"
            self.counter += 1
            if not self.high_angle_reached:
                self.current_errors.append("Поднимите корпус выше")
            self.wrong_depth_start_time = None

        # Зависание в середине
        if 125 < avg_angle < 140 and self.stage in ["going_up", "up"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Поднимите корпус выше" not in self.current_errors:
                    self.current_errors.append("Поднимите корпус выше")
        else:
            self.wrong_depth_start_time = None

        return avg_angle


class Plank(BaseExercise):
    """Планка — удержание, счётчик = секунды."""
    def __init__(self):
        super().__init__()
        self.hold_start_time = None
        self.hold_seconds = 0
        self.was_in_position = False

    def process(self, landmarks):
        r_sh = [landmarks[12].x, landmarks[12].y]
        r_hip = [landmarks[24].x, landmarks[24].y]
        r_ankle = [landmarks[28].x, landmarks[28].y]
        l_sh = [landmarks[11].x, landmarks[11].y]
        l_hip = [landmarks[23].x, landmarks[23].y]
        l_ankle = [landmarks[27].x, landmarks[27].y]
        nose = [landmarks[0].x, landmarks[0].y]

        angle_r = calculate_angle(r_sh, r_hip, r_ankle)
        angle_l = calculate_angle(l_sh, l_hip, l_ankle)
        avg_angle = (angle_r + angle_l) / 2

        self.current_errors = []
        current_time = time.time()

        in_position = 160 < avg_angle < 195

        if in_position:
            if self.hold_start_time is None:
                self.hold_start_time = current_time
            self.hold_seconds = current_time - self.hold_start_time
            self.counter = int(self.hold_seconds)
            self.was_in_position = True
        else:
            self.hold_start_time = None
            if self.was_in_position and avg_angle <= 160:
                self.current_errors.append("Держите тело прямым")
                self.errors += 1
                self.was_in_position = False
            elif self.was_in_position and avg_angle >= 195:
                self.current_errors.append("Опустите таз")
                self.errors += 1
                self.was_in_position = False

        # Голова вниз
        if nose[1] > r_sh[1] + 0.05:
            self.current_errors.append("Поднимите голову")

        return avg_angle


class SidePlank(BaseExercise):
    """Боковая планка — удержание, счётчик = секунды."""
    def __init__(self):
        super().__init__()
        self.hold_start_time = None
        self.was_in_position = False

    def process(self, landmarks):
        # Берём ту сторону, что видна лучше (по средней линии плеч/бёдер)
        r_sh = [landmarks[12].x, landmarks[12].y]
        r_hip = [landmarks[24].x, landmarks[24].y]
        r_ankle = [landmarks[28].x, landmarks[28].y]
        l_sh = [landmarks[11].x, landmarks[11].y]
        l_hip = [landmarks[23].x, landmarks[23].y]
        l_ankle = [landmarks[27].x, landmarks[27].y]

        angle_r = calculate_angle(r_sh, r_hip, r_ankle)
        angle_l = calculate_angle(l_sh, l_hip, l_ankle)
        avg_angle = (angle_r + angle_l) / 2

        self.current_errors = []
        current_time = time.time()

        in_position = 155 < avg_angle < 195

        if in_position:
            if self.hold_start_time is None:
                self.hold_start_time = current_time
            self.counter = int(current_time - self.hold_start_time)
            self.was_in_position = True
        else:
            self.hold_start_time = None
            if self.was_in_position:
                self.current_errors.append("Держите тело прямым")
                self.errors += 1
                self.was_in_position = False

        # Проверка провисания таза (угол слишком маленький)
        if avg_angle < 150 and in_position is False:
            self.current_errors.append("Поднимите таз")

        return avg_angle


class ReverseLunge(BaseExercise):
    """Обратные выпады — как Lunge, но логика та же."""
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.low_angle_reached = False

    def process(self, landmarks):
        r_hip = [landmarks[24].x, landmarks[24].y]
        r_knee = [landmarks[26].x, landmarks[26].y]
        r_ankle = [landmarks[28].x, landmarks[28].y]
        l_hip = [landmarks[23].x, landmarks[23].y]
        l_knee = [landmarks[25].x, landmarks[25].y]
        l_ankle = [landmarks[27].x, landmarks[27].y]
        r_sh = [landmarks[12].x, landmarks[12].y]

        angle_r = calculate_angle(r_hip, r_knee, r_ankle)
        angle_l = calculate_angle(l_hip, l_knee, l_ankle)
        bent_leg_angle = min(angle_r, angle_l)
        torso_angle = calculate_angle(r_sh, r_hip, r_knee)

        self.current_errors = []
        current_time = time.time()

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

        if self.stage in ["going_down", "down"]:
            if torso_angle < 140:
                self.current_errors.append("Выпрямите спину")

        if 105 < bent_leg_angle < 140 and self.stage in ["going_down", "down"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Опуститесь ниже" not in self.current_errors:
                    self.current_errors.append("Опуститесь ниже")
        else:
            self.wrong_depth_start_time = None

        return bent_leg_angle


class CalfRaise(BaseExercise):
    """Подъёмы на носки — считаем по вертикальному смещению стопы/бедра."""
    def __init__(self):
        super().__init__()
        self.min_ankle_y = None
        self.max_ankle_y = None
        self.low_reached = False
        self.high_reached = False

    def process(self, landmarks):
        r_ankle = [landmarks[28].x, landmarks[28].y]
        l_ankle = [landmarks[27].x, landmarks[27].y]
        avg_ankle_y = (r_ankle[1] + l_ankle[1]) / 2

        self.current_errors = []

        if self.max_ankle_y is None:
            self.max_ankle_y = avg_ankle_y
            self.min_ankle_y = avg_ankle_y
            return 0

        # Обновляем границы
        if avg_ankle_y > self.max_ankle_y:
            self.max_ankle_y = avg_ankle_y
        if avg_ankle_y < self.min_ankle_y:
            self.min_ankle_y = avg_ankle_y

        delta = self.max_ankle_y - self.min_ankle_y

        if self.stage == "down" and avg_ankle_y < self.max_ankle_y - 0.02:
            self.stage = "going_up"
            self.high_reached = False

        if avg_ankle_y < self.max_ankle_y - 0.04:
            self.high_reached = True

        if self.stage in ["up", "going_up"] and avg_ankle_y >= self.max_ankle_y - 0.01:
            self.stage = "down"
            self.counter += 1
            if not self.high_reached:
                self.current_errors.append("Поднимитесь выше")
            self.high_reached = False

        if self.stage == "up":
            self.stage = "down"

        return delta


class LateralRaise(BaseExercise):
    """Разведение гантелей в стороны (плечи)."""
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.high_angle_reached = False

    def process(self, landmarks):
        r_sh = [landmarks[12].x, landmarks[12].y]
        r_el = [landmarks[14].x, landmarks[14].y]
        r_wr = [landmarks[16].x, landmarks[16].y]
        l_sh = [landmarks[11].x, landmarks[11].y]
        l_el = [landmarks[13].x, landmarks[13].y]
        l_wr = [landmarks[15].x, landmarks[15].y]

        # Угол плечо-локоть-запястье (рука прямая ~180)
        angle_r = calculate_angle(r_sh, r_el, r_wr)
        angle_l = calculate_angle(l_sh, l_el, l_wr)
        avg_angle = (angle_r + angle_l) / 2

        # Высота запястья относительно плеча — подняли руки или нет
        wrist_above_shoulder_r = r_wr[1] < r_sh[1] - 0.03
        wrist_above_shoulder_l = l_wr[1] < l_sh[1] - 0.03
        arms_up = wrist_above_shoulder_r and wrist_above_shoulder_l

        self.current_errors = []
        current_time = time.time()

        # Руки внизу -> пошли вверх
        if arms_up and self.stage == "down":
            self.stage = "going_up"
            self.wrong_depth_start_time = None
            self.high_angle_reached = False

        if arms_up:
            self.high_angle_reached = True

        # Руки вернулись вниз -> повторение
        if not arms_up and self.stage in ["up", "going_up"]:
            self.stage = "down"
            self.counter += 1
            if not self.high_angle_reached:
                self.current_errors.append("Поднимите руки до уровня плеч")
            self.wrong_depth_start_time = None

        # Руки должны быть прямыми
        if avg_angle < 150:
            self.current_errors.append("Не сгибайте руки")

        # Зависание в середине
        if 100 < avg_angle < 150 and self.stage in ["going_up", "up"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Поднимите руки до уровня плеч" not in self.current_errors:
                    self.current_errors.append("Поднимите руки до уровня плеч")
        else:
            self.wrong_depth_start_time = None

        return avg_angle


class LegRaise(BaseExercise):
    """Подъёмы ног лёжа."""
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.high_angle_reached = False

    def process(self, landmarks):
        r_sh = [landmarks[12].x, landmarks[12].y]
        r_hip = [landmarks[24].x, landmarks[24].y]
        r_ankle = [landmarks[28].x, landmarks[28].y]
        l_sh = [landmarks[11].x, landmarks[11].y]
        l_hip = [landmarks[23].x, landmarks[23].y]
        l_ankle = [landmarks[27].x, landmarks[27].y]

        angle_r = calculate_angle(r_sh, r_hip, r_ankle)
        angle_l = calculate_angle(l_sh, l_hip, l_ankle)
        avg_angle = (angle_r + angle_l) / 2

        self.current_errors = []
        current_time = time.time()

        # Ноги внизу — угол ~90-110, подняли — ~160+
        if avg_angle > 130 and self.stage == "down":
            self.stage = "going_up"
            self.wrong_depth_start_time = None
            self.high_angle_reached = False

        if avg_angle > 150:
            self.high_angle_reached = True

        if avg_angle < 120 and self.stage in ["up", "going_up"]:
            self.stage = "down"
            self.counter += 1
            if not self.high_angle_reached:
                self.current_errors.append("Поднимите ноги выше")
            self.wrong_depth_start_time = None

        if 120 < avg_angle < 145 and self.stage in ["going_up", "up"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Поднимите ноги выше" not in self.current_errors:
                    self.current_errors.append("Поднимите ноги выше")
        else:
            self.wrong_depth_start_time = None

        return avg_angle


class MountainClimber(BaseExercise):
    """Альпинист — считаем подтягивания колена к груди."""
    def __init__(self):
        super().__init__()
        self.prev_knee_up = False

    def process(self, landmarks):
        r_hip = [landmarks[24].x, landmarks[24].y]
        r_knee = [landmarks[26].x, landmarks[26].y]
        r_ankle = [landmarks[28].x, landmarks[28].y]
        l_hip = [landmarks[23].x, landmarks[23].y]
        l_knee = [landmarks[25].x, landmarks[25].y]
        l_ankle = [landmarks[27].x, landmarks[27].y]

        angle_r = calculate_angle(r_hip, r_knee, r_ankle)
        angle_l = calculate_angle(l_hip, l_knee, l_ankle)
        min_angle = min(angle_r, angle_l)

        self.current_errors = []

        # Колено подтянуто — угол маленький (< 100)
        knee_up = min_angle < 100

        if knee_up and not self.prev_knee_up:
            self.counter += 1

        self.prev_knee_up = knee_up

        # Проверка: таз не должен задираться
        if r_hip[1] < r_knee[1] - 0.05:
            self.current_errors.append("Опустите таз")

        return min_angle


class Superman(BaseExercise):
    """Супермен — подъём рук и ног лёжа на животе."""
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.high_angle_reached = False

    def process(self, landmarks):
        r_sh = [landmarks[12].x, landmarks[12].y]
        r_hip = [landmarks[24].x, landmarks[24].y]
        r_ankle = [landmarks[28].x, landmarks[28].y]
        l_sh = [landmarks[11].x, landmarks[11].y]
        l_hip = [landmarks[23].x, landmarks[23].y]
        l_ankle = [landmarks[27].x, landmarks[27].y]

        angle_r = calculate_angle(r_sh, r_hip, r_ankle)
        angle_l = calculate_angle(l_sh, l_hip, l_ankle)
        avg_angle = (angle_r + angle_l) / 2

        self.current_errors = []
        current_time = time.time()

        if avg_angle > 140 and self.stage == "down":
            self.stage = "going_up"
            self.wrong_depth_start_time = None
            self.high_angle_reached = False

        if avg_angle > 160:
            self.high_angle_reached = True

        if avg_angle < 130 and self.stage in ["up", "going_up"]:
            self.stage = "down"
            self.counter += 1
            if not self.high_angle_reached:
                self.current_errors.append("Поднимите руки и ноги выше")
            self.wrong_depth_start_time = None

        if 130 < avg_angle < 155 and self.stage in ["going_up", "up"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Поднимите руки и ноги выше" not in self.current_errors:
                    self.current_errors.append("Поднимите руки и ноги выше")
        else:
            self.wrong_depth_start_time = None

        return avg_angle

class DumbbellCurl(BaseExercise):
    """Сгибание рук с гантелями (бицепс)."""
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.high_angle_reached = False

    def process(self, landmarks):
        r_sh = [landmarks[12].x, landmarks[12].y]
        r_el = [landmarks[14].x, landmarks[14].y]
        r_wr = [landmarks[16].x, landmarks[16].y]
        l_sh = [landmarks[11].x, landmarks[11].y]
        l_el = [landmarks[13].x, landmarks[13].y]
        l_wr = [landmarks[15].x, landmarks[15].y]

        # Угол плечо-локоть-запястье: внизу ~160-180, вверху ~40-60
        angle_r = calculate_angle(r_sh, r_el, r_wr)
        angle_l = calculate_angle(l_sh, l_el, l_wr)
        avg_angle = (angle_r + angle_l) / 2

        self.current_errors = []
        current_time = time.time()

        # Руки внизу -> начали сгибать
        if avg_angle < 140 and self.stage == "down":
            self.stage = "going_up"
            self.wrong_depth_start_time = None
            self.high_angle_reached = False

        # Дошли до верха
        if avg_angle < 70:
            self.high_angle_reached = True

        # Вернулись вниз -> повторение
        if avg_angle > 150 and self.stage in ["up", "going_up"]:
            self.stage = "down"
            self.counter += 1
            if not self.high_angle_reached:
                self.current_errors.append("Согните руки сильнее")
            self.wrong_depth_start_time = None

        # Локти не должны уходить вперёд/в стороны
        if abs(r_el[0] - r_sh[0]) > 0.08:
            self.current_errors.append("Держите локти ближе к корпусу")

        # Зависание в середине
        if 70 < avg_angle < 140 and self.stage in ["going_up", "up"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Согните руки сильнее" not in self.current_errors:
                    self.current_errors.append("Согните руки сильнее")
        else:
            self.wrong_depth_start_time = None

        return avg_angle


class BicycleCrunch(BaseExercise):
    """Велосипед — попеременное подтягивание колена к противоположному локтю."""
    def __init__(self):
        super().__init__()
        self.prev_left_up = False
        self.prev_right_up = False

    def process(self, landmarks):
        r_sh = [landmarks[12].x, landmarks[12].y]
        l_sh = [landmarks[11].x, landmarks[11].y]
        r_hip = [landmarks[24].x, landmarks[24].y]
        l_hip = [landmarks[23].x, landmarks[23].y]
        r_knee = [landmarks[26].x, landmarks[26].y]
        l_knee = [landmarks[25].x, landmarks[25].y]
        r_ankle = [landmarks[28].x, landmarks[28].y]
        l_ankle = [landmarks[27].x, landmarks[27].y]

        # Угол сгиба правого и левого колена
        angle_r = calculate_angle(r_hip, r_knee, r_ankle)
        angle_l = calculate_angle(l_hip, l_knee, l_ankle)

        # Колено подтянуто к груди — угол маленький
        right_knee_up = angle_r < 100
        left_knee_up = angle_l < 100

        self.current_errors = []

        # Считаем каждое попеременное подтягивание (правое или левое)
        if right_knee_up and not self.prev_right_up:
            self.counter += 1
        if left_knee_up and not self.prev_left_up:
            self.counter += 1

        self.prev_right_up = right_knee_up
        self.prev_left_up = left_knee_up

        # Проверка: колено должно идти к противоположному плечу
        # (по горизонтали колено должно быть ближе к центру, а не строго вверх)
        if right_knee_up:
            dist_to_left_sh = abs(r_knee[0] - l_sh[0])
            dist_to_right_sh = abs(r_knee[0] - r_sh[0])
            if dist_to_left_sh > dist_to_right_sh:
                self.current_errors.append("Тяните колено к противоположному локтю")

        if left_knee_up:
            dist_to_right_sh = abs(l_knee[0] - r_sh[0])
            dist_to_left_sh = abs(l_knee[0] - l_sh[0])
            if dist_to_right_sh > dist_to_left_sh:
                self.current_errors.append("Тяните колено к противоположному локтю")

        return min(angle_r, angle_l)