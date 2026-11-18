import time
from utils import calculate_angle

class BaseExercise:
    def __init__(self):
        self.counter = 0
        self.stage = "up"
        self.errors = 0
        self.current_errors = []
        
        # НОВОЕ: Словарь для статистики ошибок для БД
        # Формат: { "error_type": {"count": 1, "first_sec": 12.5} }
        self.error_stats = {}
        
    def reset(self):
        self.counter = 0
        self.stage = "up"
        self.errors = 0
        self.current_errors = []
        self.error_stats = {}

    # НОВЫЙ МЕТОД: Централизованная запись ошибки
    def log_error(self, error_type, workout_time):
        self.errors += 1
        if error_type not in self.error_stats:
            self.error_stats[error_type] = {
                "count": 1,
                "first_sec": round(workout_time, 1)
            }
        else:
            self.error_stats[error_type]["count"] += 1


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
        self.error_just_counted = False 

    def process(self, landmarks, workout_time):
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

        if avg_hip_y > self.min_hip_y:
            self.min_hip_y = avg_hip_y

        if knee_angle < 150 and self.stage == "up":
            self.stage = "going_down"
            self.wrong_depth_start_time = None
            self.low_angle_reached = False
            self.error_just_counted = False 

        if knee_angle < 100:
            self.low_angle_reached = True

        if knee_angle > 160 and self.stage in ["down", "going_down"]:
            self.stage = "up"
            
            if self.low_angle_reached:
                self.counter += 1
            else:
                self.current_errors.append("Сядьте глубже")
                if not self.error_just_counted:
                    self.log_error("squat_not_deep_enough", workout_time)
                    self.error_just_counted = True
                
            self.min_hip_y = avg_hip_y

        error_happened = False
        
        if self.stage in ["going_down", "down"]:
            if back_angle < 130:
                self.current_errors.append("Держите спину ровнее")
                if not self.error_just_counted:
                    self.log_error("back_rounded", workout_time)
                    self.error_just_counted = True
                    error_happened = True
            if r_knee[0] > r_ankle[0] + 0.05:
                self.current_errors.append("Колено вперед носка")
                if not self.error_just_counted:
                    self.log_error("knee_over_toe", workout_time)
                    self.error_just_counted = True
                    error_happened = True

        if 100 < knee_angle < 140 and self.stage in ["going_down", "down"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Сядьте глубже" not in self.current_errors:
                    self.current_errors.append("Сядьте глубже")
                    if not self.error_just_counted:
                        self.log_error("squat_stuck_high", workout_time)
                        self.error_just_counted = True
                        error_happened = True
        else:
            self.wrong_depth_start_time = None

        if not self.current_errors and not error_happened:
            self.error_just_counted = False

        return knee_angle


class PushUp(BaseExercise):
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.low_angle_reached = False
        self.error_just_counted = False

    def process(self, landmarks, workout_time):
        r_sh, r_el, r_wr = [landmarks[12].x, landmarks[12].y], [landmarks[14].x, landmarks[14].y], [landmarks[16].x, landmarks[16].y]
        l_sh, l_el, l_wr = [landmarks[11].x, landmarks[11].y], [landmarks[13].x, landmarks[13].y], [landmarks[15].x, landmarks[15].y]
        r_hip, l_hip = [landmarks[24].x, landmarks[24].y], [landmarks[23].x, landmarks[23].y]
        nose = [landmarks[0].x, landmarks[0].y]

        angle_r = calculate_angle(r_sh, r_el, r_wr)
        angle_l = calculate_angle(l_sh, l_el, l_wr)
        avg_angle = (angle_r + angle_l) / 2
        back_angle = calculate_angle(r_sh, r_hip, [landmarks[26].x, landmarks[26].y])

        self.current_errors = []
        current_time = time.time()

        if avg_angle < 150 and self.stage == "up":
            self.stage = "going_down"
            self.wrong_depth_start_time = None
            self.low_angle_reached = False
            self.error_just_counted = False

        if avg_angle < 95:
            self.low_angle_reached = True

        if avg_angle > 160 and self.stage in ["down", "going_down"]:
            self.stage = "up"
            self.counter += 1
            if not self.low_angle_reached:
                self.current_errors.append("Опуститесь ниже")
                if not self.error_just_counted:
                    self.log_error("pushup_not_deep_enough", workout_time)
                    self.error_just_counted = True
            self.wrong_depth_start_time = None

        error_happened = False
        if self.stage in ["going_down", "down"]:
            if back_angle > 190 or back_angle < 160:
                 self.current_errors.append("Держите тело прямым")
                 if not self.error_just_counted:
                     self.log_error("body_not_straight", workout_time)
                     self.error_just_counted = True
                     error_happened = True
            if nose[1] > r_sh[1] + 0.05:
                self.current_errors.append("Поднимите голову")
                if not self.error_just_counted:
                    self.log_error("head_down", workout_time)
                    self.error_just_counted = True
                    error_happened = True

        if 95 < avg_angle < 130 and self.stage in ["going_down", "down"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Опуститесь ниже" not in self.current_errors:
                    self.current_errors.append("Опуститесь ниже")
                    if not self.error_just_counted:
                        self.log_error("pushup_stuck_high", workout_time)
                        self.error_just_counted = True
                        error_happened = True
        else:
            self.wrong_depth_start_time = None

        if not self.current_errors and not error_happened:
            self.error_just_counted = False

        return avg_angle


class Lunge(BaseExercise):
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.low_angle_reached = False
        self.error_just_counted = False

    def process(self, landmarks, workout_time):
        r_hip, r_knee, r_ankle = [landmarks[24].x, landmarks[24].y], [landmarks[26].x, landmarks[26].y], [landmarks[28].x, landmarks[28].y]
        l_hip, l_knee, l_ankle = [landmarks[23].x, landmarks[23].y], [landmarks[25].x, landmarks[25].y], [landmarks[27].x, landmarks[27].y]
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
            self.error_just_counted = False

        if bent_leg_angle < 105:
            self.low_angle_reached = True

        if bent_leg_angle > 160 and self.stage in ["down", "going_down"]:
            self.stage = "up"
            self.counter += 1
            if not self.low_angle_reached:
                self.current_errors.append("Согните колено глубже")
                if not self.error_just_counted:
                    self.log_error("lunge_not_deep_enough", workout_time)
                    self.error_just_counted = True
            self.wrong_depth_start_time = None

        error_happened = False
        if self.stage in ["going_down", "down"]:
            if torso_angle < 140:
                self.current_errors.append("Выпрямите спину")
                if not self.error_just_counted:
                    self.log_error("torso_not_straight", workout_time)
                    self.error_just_counted = True
                    error_happened = True

        if 105 < bent_leg_angle < 140 and self.stage in ["going_down", "down"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Опуститесь ниже" not in self.current_errors:
                    self.current_errors.append("Опуститесь ниже")
                    if not self.error_just_counted:
                        self.log_error("lunge_stuck_high", workout_time)
                        self.error_just_counted = True
                        error_happened = True
        else:
            self.wrong_depth_start_time = None

        if not self.current_errors and not error_happened:
            self.error_just_counted = False

        return bent_leg_angle


class GluteBridge(BaseExercise):
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.high_angle_reached = False
        self.error_just_counted = False

    def process(self, landmarks, workout_time):
        r_sh, r_hip, r_knee = [landmarks[12].x, landmarks[12].y], [landmarks[24].x, landmarks[24].y], [landmarks[26].x, landmarks[26].y]
        l_sh, l_hip, l_knee = [landmarks[11].x, landmarks[11].y], [landmarks[23].x, landmarks[23].y], [landmarks[25].x, landmarks[25].y]
        nose = [landmarks[0].x, landmarks[0].y]

        angle_r = calculate_angle(r_sh, r_hip, r_knee)
        angle_l = calculate_angle(l_sh, l_hip, l_knee)
        avg_angle = (angle_r + angle_l) / 2

        self.current_errors = []
        current_time = time.time()

        if avg_angle > 120 and self.stage == "down":
            self.stage = "going_up"
            self.wrong_depth_start_time = None
            self.high_angle_reached = False
            self.error_just_counted = False

        if avg_angle > 160:
            self.high_angle_reached = True

        if avg_angle < 120 and self.stage in ["up", "going_up"]:
            self.stage = "down"
            self.counter += 1
            if not self.high_angle_reached:
                self.current_errors.append("Поднимите таз выше")
                if not self.error_just_counted:
                    self.log_error("bridge_not_high_enough", workout_time)
                    self.error_just_counted = True
            self.wrong_depth_start_time = None

        error_happened = False
        if self.stage in ["going_up", "up"]:
            if nose[1] < r_sh[1] - 0.1:
                self.current_errors.append("Не запрокидывайте голову")
                if not self.error_just_counted:
                    self.log_error("head_back", workout_time)
                    self.error_just_counted = True
                    error_happened = True

        if 130 < avg_angle < 155 and self.stage in ["going_up", "up"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Поднимите таз выше" not in self.current_errors:
                    self.current_errors.append("Поднимите таз выше")
                    if not self.error_just_counted:
                        self.log_error("bridge_stuck_mid", workout_time)
                        self.error_just_counted = True
                        error_happened = True
        else:
            self.wrong_depth_start_time = None

        if not self.current_errors and not error_happened:
            self.error_just_counted = False

        return avg_angle


class Crunch(BaseExercise):
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.high_angle_reached = False
        self.error_just_counted = False

    def process(self, landmarks, workout_time):
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

        if avg_angle > 130 and self.stage == "down":
            self.stage = "going_up"
            self.wrong_depth_start_time = None
            self.high_angle_reached = False
            self.error_just_counted = False

        if avg_angle > 145:
            self.high_angle_reached = True

        if avg_angle < 125 and self.stage in ["up", "going_up"]:
            self.stage = "down"
            self.counter += 1
            if not self.high_angle_reached:
                self.current_errors.append("Поднимите корпус выше")
                if not self.error_just_counted:
                    self.log_error("crunch_not_high_enough", workout_time)
                    self.error_just_counted = True
            self.wrong_depth_start_time = None

        error_happened = False
        if 125 < avg_angle < 140 and self.stage in ["going_up", "up"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Поднимите корпус выше" not in self.current_errors:
                    self.current_errors.append("Поднимите корпус выше")
                    if not self.error_just_counted:
                        self.log_error("crunch_stuck_mid", workout_time)
                        self.error_just_counted = True
                        error_happened = True
        else:
            self.wrong_depth_start_time = None

        if not self.current_errors and not error_happened:
            self.error_just_counted = False

        return avg_angle


class Plank(BaseExercise):
    def __init__(self):
        super().__init__()
        self.hold_start_time = None
        self.hold_seconds = 0
        self.was_in_position = False
        self.error_just_counted = False

    def process(self, landmarks, workout_time):
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
            self.error_just_counted = False
        else:
            self.hold_start_time = None
            if self.was_in_position:
                if avg_angle <= 160:
                    self.current_errors.append("Держите тело прямым")
                    self.log_error("plank_hips_sagging", workout_time)
                elif avg_angle >= 195:
                    self.current_errors.append("Опустите таз")
                    self.log_error("plank_hips_too_high", workout_time)
                self.was_in_position = False

        error_happened = False
        if nose[1] > r_sh[1] + 0.05:
            self.current_errors.append("Поднимите голову")
            if not self.error_just_counted:
                self.log_error("head_down", workout_time)
                self.error_just_counted = True
                error_happened = True

        if not self.current_errors and not error_happened:
            self.error_just_counted = False

        return avg_angle


class SidePlank(BaseExercise):
    def __init__(self):
        super().__init__()
        self.hold_start_time = None
        self.was_in_position = False
        self.error_just_counted = False

    def process(self, landmarks, workout_time):
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
            self.error_just_counted = False
        else:
            self.hold_start_time = None
            if self.was_in_position:
                self.current_errors.append("Держите тело прямым")
                self.log_error("sideplank_hips_sagging", workout_time)
                self.was_in_position = False

        error_happened = False
        if avg_angle < 150 and not in_position:
            self.current_errors.append("Поднимите таз")
            if not self.error_just_counted:
                self.log_error("sideplank_hips_sagging", workout_time)
                self.error_just_counted = True
                error_happened = True

        if not self.current_errors and not error_happened:
            self.error_just_counted = False

        return avg_angle


class ReverseLunge(BaseExercise):
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.low_angle_reached = False
        self.error_just_counted = False

    def process(self, landmarks, workout_time):
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
            self.error_just_counted = False

        if bent_leg_angle < 105:
            self.low_angle_reached = True

        if bent_leg_angle > 160 and self.stage in ["down", "going_down"]:
            self.stage = "up"
            self.counter += 1
            if not self.low_angle_reached:
                self.current_errors.append("Согните колено глубже")
                if not self.error_just_counted:
                    self.log_error("revlunge_not_deep_enough", workout_time)
                    self.error_just_counted = True
            self.wrong_depth_start_time = None

        error_happened = False
        if self.stage in ["going_down", "down"]:
            if torso_angle < 140:
                self.current_errors.append("Выпрямите спину")
                if not self.error_just_counted:
                    self.log_error("torso_not_straight", workout_time)
                    self.error_just_counted = True
                    error_happened = True

        if 105 < bent_leg_angle < 140 and self.stage in ["going_down", "down"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Опуститесь ниже" not in self.current_errors:
                    self.current_errors.append("Опуститесь ниже")
                    if not self.error_just_counted:
                        self.log_error("revlunge_stuck_high", workout_time)
                        self.error_just_counted = True
                        error_happened = True
        else:
            self.wrong_depth_start_time = None

        if not self.current_errors and not error_happened:
            self.error_just_counted = False

        return bent_leg_angle


class CalfRaise(BaseExercise):
    def __init__(self):
        super().__init__()
        self.min_ankle_y = None
        self.max_ankle_y = None
        self.low_reached = False
        self.high_reached = False
        self.error_just_counted = False

    def process(self, landmarks, workout_time):
        r_ankle = [landmarks[28].x, landmarks[28].y]
        l_ankle = [landmarks[27].x, landmarks[27].y]
        avg_ankle_y = (r_ankle[1] + l_ankle[1]) / 2

        self.current_errors = []

        if self.max_ankle_y is None:
            self.max_ankle_y = avg_ankle_y
            self.min_ankle_y = avg_ankle_y
            return 0

        if avg_ankle_y > self.max_ankle_y:
            self.max_ankle_y = avg_ankle_y
        if avg_ankle_y < self.min_ankle_y:
            self.min_ankle_y = avg_ankle_y

        delta = self.max_ankle_y - self.min_ankle_y

        if self.stage == "down" and avg_ankle_y < self.max_ankle_y - 0.02:
            self.stage = "going_up"
            self.high_reached = False
            self.error_just_counted = False

        if avg_ankle_y < self.max_ankle_y - 0.04:
            self.high_reached = True

        if self.stage in ["up", "going_up"] and avg_ankle_y >= self.max_ankle_y - 0.01:
            self.stage = "down"
            self.counter += 1
            if not self.high_reached:
                self.current_errors.append("Поднимитесь выше")
                if not self.error_just_counted:
                    self.log_error("calfraise_not_high_enough", workout_time)
                    self.error_just_counted = True
            self.high_reached = False

        if self.stage == "up":
            self.stage = "down"
            self.error_just_counted = False

        return delta


class LateralRaise(BaseExercise):
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.high_angle_reached = False
        self.error_just_counted = False

    def process(self, landmarks, workout_time):
        r_sh = [landmarks[12].x, landmarks[12].y]
        r_el = [landmarks[14].x, landmarks[14].y]
        r_wr = [landmarks[16].x, landmarks[16].y]
        l_sh = [landmarks[11].x, landmarks[11].y]
        l_el = [landmarks[13].x, landmarks[13].y]
        l_wr = [landmarks[15].x, landmarks[15].y]

        angle_r = calculate_angle(r_sh, r_el, r_wr)
        angle_l = calculate_angle(l_sh, l_el, l_wr)
        avg_angle = (angle_r + angle_l) / 2

        wrist_above_shoulder_r = r_wr[1] < r_sh[1] - 0.03
        wrist_above_shoulder_l = l_wr[1] < l_sh[1] - 0.03
        arms_up = wrist_above_shoulder_r and wrist_above_shoulder_l

        self.current_errors = []
        current_time = time.time()

        if arms_up and self.stage == "down":
            self.stage = "going_up"
            self.wrong_depth_start_time = None
            self.high_angle_reached = False
            self.error_just_counted = False

        if arms_up:
            self.high_angle_reached = True

        if not arms_up and self.stage in ["up", "going_up"]:
            self.stage = "down"
            self.counter += 1
            if not self.high_angle_reached:
                self.current_errors.append("Поднимите руки до уровня плеч")
                if not self.error_just_counted:
                    self.log_error("lateralraise_not_high_enough", workout_time)
                    self.error_just_counted = True
            self.wrong_depth_start_time = None

        error_happened = False
        if avg_angle < 150:
            self.current_errors.append("Не сгибайте руки")
            if not self.error_just_counted:
                self.log_error("arms_bent", workout_time)
                self.error_just_counted = True
                error_happened = True

        if 100 < avg_angle < 150 and self.stage in ["going_up", "up"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Поднимите руки до уровня плеч" not in self.current_errors:
                    self.current_errors.append("Поднимите руки до уровня плеч")
                    if not self.error_just_counted:
                        self.log_error("lateralraise_stuck_mid", workout_time)
                        self.error_just_counted = True
                        error_happened = True
        else:
            self.wrong_depth_start_time = None

        if not self.current_errors and not error_happened:
            self.error_just_counted = False

        return avg_angle


class LegRaise(BaseExercise):
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.high_angle_reached = False
        self.error_just_counted = False

    def process(self, landmarks, workout_time):
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

        if avg_angle > 130 and self.stage == "down":
            self.stage = "going_up"
            self.wrong_depth_start_time = None
            self.high_angle_reached = False
            self.error_just_counted = False

        if avg_angle > 150:
            self.high_angle_reached = True

        if avg_angle < 120 and self.stage in ["up", "going_up"]:
            self.stage = "down"
            self.counter += 1
            if not self.high_angle_reached:
                self.current_errors.append("Поднимите ноги выше")
                if not self.error_just_counted:
                    self.log_error("legraise_not_high_enough", workout_time)
                    self.error_just_counted = True
            self.wrong_depth_start_time = None

        error_happened = False
        if 120 < avg_angle < 145 and self.stage in ["going_up", "up"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Поднимите ноги выше" not in self.current_errors:
                    self.current_errors.append("Поднимите ноги выше")
                    if not self.error_just_counted:
                        self.log_error("legraise_stuck_mid", workout_time)
                        self.error_just_counted = True
                        error_happened = True
        else:
            self.wrong_depth_start_time = None

        if not self.current_errors and not error_happened:
            self.error_just_counted = False

        return avg_angle


class MountainClimber(BaseExercise):
    """Альпинист — считаем подтягивания колена к груди."""
    def __init__(self):
        super().__init__()
        self.prev_knee_up = False
        self.error_just_counted = False

    def process(self, landmarks, workout_time):
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
            self.error_just_counted = False # Сброс при новом движении

        self.prev_knee_up = knee_up

        error_happened = False
        # Проверка: таз не должен задираться
        if r_hip[1] < r_knee[1] - 0.05:
            self.current_errors.append("Опустите таз")
            if not self.error_just_counted:
                self.log_error("hips_too_high", workout_time)
                self.error_just_counted = True
                error_happened = True

        if not self.current_errors and not error_happened:
            self.error_just_counted = False

        return min_angle


class Superman(BaseExercise):
    """Супермен — подъём рук и ног лёжа на животе."""
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.high_angle_reached = False
        self.error_just_counted = False

    def process(self, landmarks, workout_time):
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
            self.error_just_counted = False

        if avg_angle > 160:
            self.high_angle_reached = True

        if avg_angle < 130 and self.stage in ["up", "going_up"]:
            self.stage = "down"
            self.counter += 1
            if not self.high_angle_reached:
                self.current_errors.append("Поднимите руки и ноги выше")
                if not self.error_just_counted:
                    self.log_error("superman_not_high_enough", workout_time)
                    self.error_just_counted = True
            self.wrong_depth_start_time = None

        error_happened = False
        if 130 < avg_angle < 155 and self.stage in ["going_up", "up"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Поднимите руки и ноги выше" not in self.current_errors:
                    self.current_errors.append("Поднимите руки и ноги выше")
                    if not self.error_just_counted:
                        self.log_error("superman_stuck_mid", workout_time)
                        self.error_just_counted = True
                        error_happened = True
        else:
            self.wrong_depth_start_time = None

        if not self.current_errors and not error_happened:
            self.error_just_counted = False

        return avg_angle


class DumbbellCurl(BaseExercise):
    """Сгибание рук с гантелями (бицепс)."""
    def __init__(self):
        super().__init__()
        self.wrong_depth_start_time = None
        self.high_angle_reached = False
        self.error_just_counted = False

    def process(self, landmarks, workout_time):
        r_sh = [landmarks[12].x, landmarks[12].y]
        r_el = [landmarks[14].x, landmarks[14].y]
        r_wr = [landmarks[16].x, landmarks[16].y]
        l_sh = [landmarks[11].x, landmarks[11].y]
        l_el = [landmarks[13].x, landmarks[13].y]
        l_wr = [landmarks[15].x, landmarks[15].y]

        angle_r = calculate_angle(r_sh, r_el, r_wr)
        angle_l = calculate_angle(l_sh, l_el, l_wr)
        avg_angle = (angle_r + angle_l) / 2

        self.current_errors = []
        current_time = time.time()

        if avg_angle < 140 and self.stage == "down":
            self.stage = "going_up"
            self.wrong_depth_start_time = None
            self.high_angle_reached = False
            self.error_just_counted = False

        if avg_angle < 70:
            self.high_angle_reached = True

        if avg_angle > 150 and self.stage in ["up", "going_up"]:
            self.stage = "down"
            self.counter += 1
            if not self.high_angle_reached:
                self.current_errors.append("Согните руки сильнее")
                if not self.error_just_counted:
                    self.log_error("curl_not_high_enough", workout_time)
                    self.error_just_counted = True
            self.wrong_depth_start_time = None

        error_happened = False
        if abs(r_el[0] - r_sh[0]) > 0.08:
            self.current_errors.append("Держите локти ближе к корпусу")
            if not self.error_just_counted:
                self.log_error("elbows_flared", workout_time)
                self.error_just_counted = True
                error_happened = True

        if 70 < avg_angle < 140 and self.stage in ["going_up", "up"]:
            if self.wrong_depth_start_time is None:
                self.wrong_depth_start_time = current_time
            elif current_time - self.wrong_depth_start_time > 1.5:
                if "Согните руки сильнее" not in self.current_errors:
                    self.current_errors.append("Согните руки сильнее")
                    if not self.error_just_counted:
                        self.log_error("curl_stuck_mid", workout_time)
                        self.error_just_counted = True
                        error_happened = True
        else:
            self.wrong_depth_start_time = None

        if not self.current_errors and not error_happened:
            self.error_just_counted = False

        return avg_angle


class BicycleCrunch(BaseExercise):
    """Велосипед — попеременное подтягивание колена к противоположному локтю."""
    def __init__(self):
        super().__init__()
        self.prev_left_up = False
        self.prev_right_up = False
        self.error_just_counted = False

    def process(self, landmarks, workout_time):
        r_sh = [landmarks[12].x, landmarks[12].y]
        l_sh = [landmarks[11].x, landmarks[11].y]
        r_hip = [landmarks[24].x, landmarks[24].y]
        l_hip = [landmarks[23].x, landmarks[23].y]
        r_knee = [landmarks[26].x, landmarks[26].y]
        l_knee = [landmarks[25].x, landmarks[25].y]
        r_ankle = [landmarks[28].x, landmarks[28].y]
        l_ankle = [landmarks[27].x, landmarks[27].y]

        angle_r = calculate_angle(r_hip, r_knee, r_ankle)
        angle_l = calculate_angle(l_hip, l_knee, l_ankle)

        right_knee_up = angle_r < 100
        left_knee_up = angle_l < 100

        self.current_errors = []
        error_happened = False

        if right_knee_up and not self.prev_right_up:
            self.counter += 1
            self.error_just_counted = False
        if left_knee_up and not self.prev_left_up:
            self.counter += 1
            self.error_just_counted = False

        self.prev_right_up = right_knee_up
        self.prev_left_up = left_knee_up

        if right_knee_up:
            dist_to_left_sh = abs(r_knee[0] - l_sh[0])
            dist_to_right_sh = abs(r_knee[0] - r_sh[0])
            if dist_to_left_sh > dist_to_right_sh:
                self.current_errors.append("Тяните колено к противоположному локтю")
                if not self.error_just_counted:
                    self.log_error("wrong_side_twist", workout_time)
                    self.error_just_counted = True
                    error_happened = True

        if left_knee_up:
            dist_to_right_sh = abs(l_knee[0] - r_sh[0])
            dist_to_left_sh = abs(l_knee[0] - l_sh[0])
            if dist_to_right_sh > dist_to_left_sh:
                self.current_errors.append("Тяните колено к противоположному локтю")
                if not self.error_just_counted:
                    self.log_error("wrong_side_twist", workout_time)
                    self.error_just_counted = True
                    error_happened = True

        if not self.current_errors and not error_happened:
            self.error_just_counted = False

        return min(angle_r, angle_l)