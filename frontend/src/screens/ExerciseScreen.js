import { useMemo } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { loadExercise } from '../api/home';
import { parseExerciseText, stepCountLabel } from '../api/parseExerciseText';
import { muscleLabel } from '../constants/muscleGroups';
import { navigate, routes } from '../navigation/routes';

export default function ExerciseScreen({ exerciseId }) {
  const exercise = useMemo(() => loadExercise(exerciseId), [exerciseId]);
  const text = useMemo(
    () => parseExerciseText(exercise ? exercise.description : null),
    [exercise],
  );

  return (
    <ScrollView contentContainerStyle={styles.content}>
      <Pressable
        accessibilityRole="button"
        testID="exercise_back"
        onPress={() => navigate(routes.home)}
        style={styles.back}
      >
        <Text>Назад</Text>
      </Pressable>

      {exercise ? (
        <View style={styles.plate}>
          {exercise.target_muscle_group ? (
            <Text>{muscleLabel(exercise.target_muscle_group)}</Text>
          ) : null}
          <Text>{exercise.name}</Text>
          {text.description ? <Text>{text.description}</Text> : null}

          {text.steps.length > 0 ? (
            <View style={styles.steps}>
              <View style={styles.stepsHeader}>
                <Text>Как выполнять</Text>
                <Text>{stepCountLabel(text.steps.length)}</Text>
              </View>
              {text.steps.map((step, index) => (
                <View key={`${exercise.exercise_id}-${index}`} style={styles.step}>
                  <Text>{String(index + 1).padStart(2, '0')}</Text>
                  <Text style={styles.stepText}>{step}</Text>
                </View>
              ))}
            </View>
          ) : null}

          {/* TODO: route Camera. Экран не смонтирован, см. routes.camera. */}
          <Pressable
            accessibilityRole="button"
            testID="exercise_camera"
            onPress={() => navigate(routes.camera, { exerciseId: exercise.exercise_id })}
            style={styles.camera}
          >
            <Text>Включить камеру</Text>
          </Pressable>
          <Text>Видео обрабатывается только на устройстве</Text>
        </View>
      ) : (
        <Text>Упражнение не найдено</Text>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: {
    padding: 16,
    gap: 12,
  },
  back: {
    alignSelf: 'flex-start',
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  plate: {
    padding: 12,
    gap: 12,
    borderWidth: 1,
  },
  steps: {
    gap: 8,
  },
  stepsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  step: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  stepText: {
    flex: 1,
  },
  camera: {
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
});
