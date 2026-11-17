import { getSessionUser } from './auth';

// TODO: GET /auth/me → UserRead
export function loadCurrentUser() {
  const sessionUser = getSessionUser();
  if (sessionUser) {
    return sessionUser;
  }
  return {
    user_id: 1,
    email: 'max@example.com',
    name: 'Макс',
    created_at: '2026-01-01T00:00:00Z',
  };
}

// TODO: GET /exercises/{exercise_id} → ExerciseRead
export function loadExercise(exerciseId) {
  return loadExercises().find((exercise) => exercise.exercise_id === exerciseId) ?? null;
}

// TODO: GET /exercises → ExerciseRead[]
export function loadExercises() {
  return [
    {
      exercise_id: 1,
      name: 'Приседания',
      description: [
        'Базовое упражнение для силы, баланса и уверенных движений.',
        '',
        'Как выполнять:',
        '1. Поставь стопы чуть шире плеч, носки разверни наружу.',
        '2. Отведи таз назад и плавно опускайся, сохраняя спину прямой.',
        '3. Толкайся пятками и вернись вверх без резких движений.',
      ].join('\n'),
      target_muscle_group: 'legs',
    },
    {
      exercise_id: 2,
      name: 'Планка',
      description: [
        'Удержание корпуса в прямой линии.',
        '',
        'Как выполнять:',
        '1. Обопрись на предплечья и носки.',
        '2. Держи спину ровно и не провисай в пояснице.',
        '3. Дыши спокойно, пока держишь положение.',
      ].join('\n'),
      target_muscle_group: 'core',
    },
    {
      exercise_id: 3,
      name: 'Отжимания',
      description: null,
      target_muscle_group: 'chest',
    },
    {
      exercise_id: 4,
      name: 'Тяга',
      description: [
        'Упражнение для спины.',
        '',
        'Как выполнять:',
        '1. Наклонись с прямой спиной.',
        '2. Подтяни вес к поясу.',
        '3. Опусти его обратно без рывка.',
      ].join('\n'),
      target_muscle_group: 'back',
    },
    {
      exercise_id: 5,
      name: 'Жим стоя',
      description: [
        'Упражнение для плеч.',
        '',
        'Как выполнять:',
        '1. Встань прямо, вес у плеч.',
        '2. Выжми его вверх.',
        '3. Опусти к плечам.',
      ].join('\n'),
      target_muscle_group: 'shoulders',
    },
    {
      exercise_id: 6,
      name: 'Сгибания рук',
      description: [
        'Упражнение для рук.',
        '',
        'Как выполнять:',
        '1. Прижми локти к корпусу.',
        '2. Согни руки.',
        '3. Медленно разогни их.',
      ].join('\n'),
      target_muscle_group: 'arms',
    },
    {
      exercise_id: 7,
      name: 'Берпи',
      description: [
        'Упражнение на всё тело.',
        '',
        'Как выполнять:',
        '1. Присядь и поставь ладони на пол.',
        '2. Выпрыгни ногами назад в планку.',
        '3. Вернись в присед и встань.',
      ].join('\n'),
      target_muscle_group: 'full_body',
    },
  ];
}
