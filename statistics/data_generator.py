from datetime import datetime

NEWLINE = '\n'


class CumulatedDataGenerator:

    def __init__(self, history):
        self._history = history

    def _flatmap_zip(self, list1, list2, offset=0.0):
        return [(item - offset) if isinstance(item, float) else item for sublist in zip(list1, list2) for item in
                sublist]

    def calculate_separated_states(self, start_date, end_date, compact=False):
        separated_data = {'dates': [],
                          'morning_labels': [],
                          'morning_energy': [],
                          'morning_stress': [],
                          'morning_fatigue': [],
                          'morning_demotivation': [],
                          'afternoon_labels': [],
                          'afternoon_energy': [],
                          'afternoon_stress': [],
                          'afternoon_fatigue': [],
                          'afternoon_demotivation': []}

        for date_str, day_data in self._history.items():
            date = datetime.strptime(date_str, '%Y-%m-%d').date()

            if start_date <= date <= end_date:
                separated_data['dates'].append(date)

                # Extract morning data
                morning_data = day_data.get('morning', {})
                separated_data['morning_energy'].append(morning_data.get('energy_state', None))
                separated_data['morning_stress'].append(morning_data.get('stress_state', None))
                separated_data['morning_fatigue'].append(morning_data.get('mental_fatigue_state', None))
                separated_data['morning_demotivation'].append(morning_data.get('motivation_state', None))
                if not compact:
                    separated_data['morning_labels'].append(
                        f"$\\bf{{{date.strftime('%d.%m.')}}}Morgens$\n{NEWLINE.join(self._history[date_str]['morning']['tasks'])}")
                else:
                    separated_data['morning_labels'].append(
                        f"$\\bf{{{date.strftime('%d.%m.')}}}$ Morgens")

                # Extract afternoon data
                afternoon_data = day_data.get('afternoon', {})
                separated_data['afternoon_energy'].append(afternoon_data.get('energy_state', None))
                separated_data['afternoon_stress'].append(afternoon_data.get('stress_state', None))
                separated_data['afternoon_fatigue'].append(afternoon_data.get('mental_fatigue_state', None))
                separated_data['afternoon_demotivation'].append(afternoon_data.get('motivation_state', None))
                if not compact:
                    separated_data['afternoon_labels'].append(
                        f"$\\bf{{{date.strftime('%d.%m.')}}}Mittags$\n{NEWLINE.join(self._history[date_str].get('afternoon', {}).get('tasks', []))}")
                else:
                    separated_data['afternoon_labels'].append(
                        f"Mittags")

        return separated_data

    def calculate_combined_states(self, start_date, end_date, compact=False):
        sep_data = self.calculate_separated_states(start_date, end_date, compact=compact)

        # Combine morning and afternoon data
        combined_dates = self._flatmap_zip(sep_data['dates'], sep_data['dates'])
        combined_energy = self._flatmap_zip(sep_data['morning_energy'], sep_data['afternoon_energy'], offset=0.03375)
        combined_fatigue = self._flatmap_zip(sep_data['morning_fatigue'], sep_data['afternoon_fatigue'], offset=-0.03375)
        combined_demotivation = self._flatmap_zip(sep_data['morning_demotivation'], sep_data['afternoon_demotivation'], offset=0.01125)
        combined_stress = self._flatmap_zip(sep_data['morning_stress'], sep_data['afternoon_stress'], offset=-0.01125)
        combined_labels = self._flatmap_zip(sep_data['morning_labels'], sep_data['afternoon_labels'])

        return {'combined_dates': combined_dates,
                'combined_energy': combined_energy,
                'combined_stress': combined_stress,
                'combined_fatigue': combined_fatigue,
                'combined_demotivation': combined_demotivation,
                'combined_labels': combined_labels,
                }

    def calculate_most_used(self, start_date, end_date):
        # Combine morning and afternoon data
        mood_data = {}
        for date_str in self._history:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if start_date <= date <= end_date:
                morning_mood_state = self._history.get(date_str, {}).get('morning', {}).get('mood_state', [])
                afternoon_mood_state = self._history.get(date_str, {}).get('afternoon', {}).get('mood_state', [])
                mood_states = morning_mood_state + afternoon_mood_state
                for mood_state in mood_states:
                    mood_data[mood_state] = mood_data.get(mood_state, 0) + 1

        # Get the most common mood states
        top_mood_states = sorted(mood_data.items(), key=lambda x: x[1], reverse=True)

        # Combine morning and afternoon data
        tasks_data = {}
        for date_str in self._history:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if start_date <= date <= end_date:
                morning_tasks = self._history.get(date_str, {}).get('morning', {}).get('tasks', [])
                afternoon_tasks = self._history.get(date_str, {}).get('afternoon', {}).get('tasks', [])
                tasks = morning_tasks + afternoon_tasks
                for task in tasks:
                    tasks_data[task] = tasks_data.get(task, 0) + 1

        # Get the five most used tasks
        top_tasks = sorted(tasks_data.items(), key=lambda x: x[1], reverse=True)

        return top_mood_states, top_tasks

    def calculate_metadata(self, start_date, end_date):
        sep_data = self.calculate_separated_states(start_date, end_date)

        day_count = len(sep_data.get('dates'))
        good_mornings = 0
        good_afternoons = 0
        mid_mornings = 0
        mid_afternoons = 0
        bad_mornings = 0
        bad_afternoons = 0
        stress_days = 0
        mental_fatigue_days = 0
        sleepy_days = 0
        no_motivation_days = 0

        for idx, day in enumerate(sep_data.get('dates')):
            # Morning mood states
            morning_mood_states = [sep_data['morning_energy'][idx], sep_data['morning_stress'][idx],
                                   sep_data['morning_fatigue'][idx], sep_data['morning_demotivation'][idx]]
            morning_med_mood = sorted(morning_mood_states)[len(morning_mood_states) // 2]

            if morning_med_mood < 3:
                good_mornings += 1
            elif morning_med_mood == 3:
                if any(val >= 4 for val in morning_mood_states):
                    bad_mornings += 1
                else:
                    mid_mornings += 1
            else:
                bad_mornings += 1

            # Afternoon mood states
            afternoon_mood_states = [sep_data['afternoon_energy'][idx], sep_data['afternoon_stress'][idx],
                                     sep_data['afternoon_fatigue'][idx], sep_data['afternoon_demotivation'][idx]]
            afternoon_med_mood = sorted(afternoon_mood_states)[len(afternoon_mood_states) // 2]

            if afternoon_med_mood < 3:
                good_afternoons += 1
            elif afternoon_med_mood == 3:
                if any(val >= 4 for val in afternoon_mood_states):
                    bad_afternoons += 1
                else:
                    mid_afternoons += 1
            else:
                bad_afternoons += 1

            # Update counters for stress, mental fatigue, sleepy, and no motivation days
            if sep_data['morning_stress'][idx] > 3 or sep_data['afternoon_stress'][idx] > 3:
                stress_days += 1
            if sep_data['morning_fatigue'][idx] > 3 or sep_data['afternoon_fatigue'][idx] > 3:
                mental_fatigue_days += 1
            if sep_data['morning_energy'][idx] > 3 or sep_data['afternoon_energy'][idx] > 3:
                sleepy_days += 1
            if sep_data['morning_demotivation'][idx] > 3 or sep_data['afternoon_demotivation'][idx] > 3:
                no_motivation_days += 1

        return (day_count, good_mornings, good_afternoons, mid_mornings, mid_afternoons, bad_mornings,
                bad_afternoons, stress_days, mental_fatigue_days, sleepy_days, no_motivation_days)

    def prepare_mood_calendar_data(self, start_date, end_date):
        morning_mood_states = {}
        afternoon_mood_states = {}
        for date_str in self._history:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if start_date <= date <= end_date:
                morning_mood_states[date_str] = self._history.get(date_str, {}).get('morning', {}).get('mood_state', [])
                afternoon_mood_states[date_str] = self._history.get(date_str, {}).get('afternoon', {}).get('mood_state', [])
        return morning_mood_states, afternoon_mood_states
