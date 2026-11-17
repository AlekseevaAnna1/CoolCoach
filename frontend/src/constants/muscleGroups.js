export const ALL_MUSCLES = 'all';

// Order matches TargetMuscleGroup in the API spec.
export const MUSCLE_GROUPS = [
  { id: 'chest', label: 'Грудь' },
  { id: 'back', label: 'Спина' },
  { id: 'legs', label: 'Ноги' },
  { id: 'shoulders', label: 'Плечи' },
  { id: 'arms', label: 'Руки' },
  { id: 'core', label: 'Пресс' },
  { id: 'full_body', label: 'Всё тело' },
];

export const MUSCLE_FILTERS = [{ id: ALL_MUSCLES, label: 'Все' }, ...MUSCLE_GROUPS];

export function muscleLabel(id) {
  const group = MUSCLE_GROUPS.find((item) => item.id === id);
  return group ? group.label : id;
}
