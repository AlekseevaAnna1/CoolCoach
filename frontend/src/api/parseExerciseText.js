// ОТХОД ОТ СПЕЦИФИКАЦИИ.
//
// В OpenAPI у упражнения одно поле ExerciseRead.description: строка или null.
// Отдельных полей для краткого описания и для блока «Как выполнять» в схеме нет.
// Нет массива шагов, заголовка секции и счётчика шагов. GET /exercises и
// GET /exercises/{exercise_id} оба отдают этот же ExerciseRead, так что
// контракт API мы не меняем и новое поле на бэкенд не просим.
//
// На макете окна упражнения это два разных блока: абзац под названием и
// нумерованный список «Как выполнять». Чтобы не расходиться с ответом сервера,
// весь этот текст по-прежнему приходит одной строкой в description. Фронт
// делит её сам, уже после загрузки.
//
// Формат, который должен соблюдать текст в description:
//
//   Базовое упражнение для силы, баланса и уверенных движений.
//
//   Как выполнять:
//   1. Поставь стопы чуть шире плеч, носки разверни наружу.
//   2. Отведи таз назад и плавно опускайся, сохраняя спину прямой.
//
// Правила разбора:
// - null, пустая строка и строка без маркера целиком становятся описанием,
//   список шагов пустой.
// - Маркер — отдельная строка, которая после trim равна «Как выполнять:».
//   Регистр не учитывается.
// - Всё до маркера — описание. Пустые строки по краям снимаются.
// - После маркера шагом считается строка «1. текст» или «01. текст».
//   Номер из текста на экране не используется: шаги нумеруются заново.
// - Любая другая строка после маркера пропускается.
// - Если маркер есть, а ни одного шага разобрать не удалось, блок
//   «Как выполнять» не показывается, на экране остаётся только описание.

const STEPS_MARKER = 'как выполнять:';
const STEP_LINE = /^\d+\.\s*(.+)$/;

export function parseExerciseText(description) {
  if (typeof description !== 'string') {
    return { description: '', steps: [] };
  }

  const lines = description.split(/\r?\n/);
  const markerIndex = lines.findIndex((line) => line.trim().toLowerCase() === STEPS_MARKER);

  if (markerIndex === -1) {
    return { description: description.trim(), steps: [] };
  }

  const steps = lines
    .slice(markerIndex + 1)
    .map((line) => {
      const match = line.trim().match(STEP_LINE);
      return match ? match[1].trim() : '';
    })
    .filter((step) => step.length > 0);

  return {
    description: lines.slice(0, markerIndex).join('\n').trim(),
    steps,
  };
}

export function stepCountLabel(count) {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) {
    return `${count} шаг`;
  }
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    return `${count} шага`;
  }
  return `${count} шагов`;
}
