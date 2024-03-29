import io
import re
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.style as style
import numpy as np


NEWLINE = '\n'


class CumulatedDataGenerator:

    def __init__(self, history):
        self._history = history

    def _flatmap_zip(self, list1, list2, offset=0.0):
        return [(item - offset) if isinstance(item, float) else item for sublist in zip(list1, list2) for item in
                sublist]

    def _use_german_date(self, val):
        return datetime.strptime(val, '%Y-%m-%d').strftime('%d.%m.')

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

        for date, day_data in self._history.items():
            # Check if the date is within the specified range
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
                        f"$\\bf{{{self._use_german_date(date)}}}Morgens$\n{NEWLINE.join(self._history[date]['morning']['tasks'])}")
                else:
                    separated_data['morning_labels'].append(
                        f"$\\bf{{{self._use_german_date(date)}}}$ Morgens")

                # Extract afternoon data
                afternoon_data = day_data.get('afternoon', {})
                separated_data['afternoon_energy'].append(afternoon_data.get('energy_state', None))
                separated_data['afternoon_stress'].append(afternoon_data.get('stress_state', None))
                separated_data['afternoon_fatigue'].append(afternoon_data.get('mental_fatigue_state', None))
                separated_data['afternoon_demotivation'].append(afternoon_data.get('motivation_state', None))
                if not compact:
                    separated_data['afternoon_labels'].append(
                        f"$\\bf{{{self._use_german_date(date)}}}Mittags$\n{NEWLINE.join(self._history[date].get('afternoon', {}).get('tasks', []))}")
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
        for date in self._history:
            if start_date <= date <= end_date:
                mood_states = self._history[date]['morning']['mood_state'] + self._history[date].get('afternoon',
                                                                                                     {}).get(
                    'mood_state', [])
                for mood_state in mood_states:
                    mood_data[mood_state] = mood_data.get(mood_state, 0) + 1

        # Get the most common mood states
        top_mood_states = sorted(mood_data.items(), key=lambda x: x[1], reverse=True)

        # Combine morning and afternoon data
        tasks_data = {}
        for date in self._history:
            if start_date <= date <= end_date:
                tasks = self._history[date]['morning']['tasks'] + self._history[date].get('afternoon', {}).get('tasks',
                                                                                                               [])
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


class ChartGenerator:
    def __init__(self, data_generator):
        self.data_generator = data_generator

    def _prepare_line_chart(self, ax, energy, stress, fatigue, demotivation, labels, title, compact=False):
        median_energy = np.average([value for value in energy if value is not None])
        median_stress = np.average([value for value in stress if value is not None])
        median_fatigue = np.average([value for value in fatigue if value is not None])
        median_demotivation = np.average([value for value in demotivation if value is not None])
        linewidth = 5.0 if not compact else 3.0
        markersize = 24 if not compact else 18
        ax.plot(energy, range(len(labels)), label=f'Schläfrigkeit (Avg: {median_energy:.2f})', marker='o',
                markersize=markersize, linestyle='solid', alpha=1, color='skyblue', linewidth=linewidth)
        ax.plot(fatigue, range(len(labels)), label=f'Mentale Ermüdung (Avg: {median_fatigue:.2f})', marker='o',
                markersize=markersize, linestyle='solid', alpha=1, color='palegreen', linewidth=linewidth)
        ax.plot(demotivation, range(len(labels)), label=f'Unlust (Avg: {median_demotivation:.2f})', marker='o',
                markersize=markersize, linestyle='solid', alpha=1, color='wheat', linewidth=linewidth)
        ax.plot(stress, range(len(labels)), label=f'Stress Level (Avg: {median_stress:.2f})', marker='o', markersize=markersize,
                linestyle='solid', alpha=1, color='coral', linewidth=linewidth)
        # ax.set_xlabel('Höhe', color='white')  # Set text color
        ax.set_title(title, fontweight='light', fontsize=32, color='white')  # Adjust title font and color
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, ha='right', fontsize=16, color='white')  # Adjust y-axis label font and color
        ax.set_xticks(np.arange(1, 6, 1))
        ax.set_facecolor('#404040')  # Set background color to a dark shade
        ax.spines['bottom'].set_color('#bfbfbf')  # Set bottom spine color
        ax.spines['top'].set_color('#bfbfbf')  # Set top spine color
        ax.spines['right'].set_color('#bfbfbf')  # Set right spine color
        ax.spines['left'].set_color('#bfbfbf')  # Set left spine color
        ax.tick_params(axis='x', colors='#fafafa', labelsize=16)  # Set x-axis tick color
        ax.tick_params(axis='y', colors='#fafafa')  # Set y-axis tick color
        ax.invert_yaxis()
        frame = ax.legend(loc=1, prop={'size': 13}, markerscale=0.5).get_frame()
        frame.set_facecolor('#404040')
        frame.set_linewidth(0)

    def generate_line_chart(self, title, start_date=None, end_date=None, compact=False):
        combined_data = self.data_generator.calculate_combined_states(start_date, end_date, compact=compact)

        # Plotting the combined data
        style.use('dark_background')  # Use a dark mode-like style
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 20 if compact else 16))
        fig.patch.set_facecolor('#404040')

        self._prepare_line_chart(ax,
                                 combined_data['combined_energy'],
                                 combined_data['combined_stress'],
                                 combined_data['combined_fatigue'],
                                 combined_data['combined_demotivation'],
                                 combined_data['combined_labels'],
                                 title=title, compact=compact)

        alpha = 0.5
        for i, label in enumerate(combined_data['combined_labels']):
            if re.search(r'(Morgens|Mittags)', label).group() == 'Morgens':
                alpha = 0.5 if alpha == 0 else 0
            plt.axhspan(i - 0.5, i + 0.5, facecolor='0.2', alpha=alpha)

        line_chart_buffer = io.BytesIO()
        plt.savefig(line_chart_buffer, dpi=fig.dpi, bbox_inches="tight", facecolor=fig.get_facecolor(),
                    edgecolor='none', format='png')
        line_chart_buffer.seek(0)
        result = line_chart_buffer.read()
        line_chart_buffer.close()
        return result

    def generate_bar_chart(self, top_data, title, color):
        data_labels, data_counts = zip(*top_data[:min(5, len(top_data))])

        fig, ax = plt.subplots(figsize=(10, 16))
        fig.patch.set_facecolor('#404040')

        # Create a vertical bar chart
        ax.bar(data_labels, data_counts, color=color, alpha=1)
        ax.set_title(f'{NEWLINE}{title}{NEWLINE}', color='white', fontsize=32)
        ax.set_facecolor('#404040')
        ax.spines['bottom'].set_color('#bfbfbf')
        ax.spines['top'].set_color('#bfbfbf')
        ax.spines['right'].set_color('#bfbfbf')
        ax.spines['left'].set_color('#bfbfbf')
        ax.tick_params(axis='x', colors='#fafafa', labelsize=16)
        ax.tick_params(axis='y', colors='#fafafa', labelsize=16)
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

        bar_chart_buffer = io.BytesIO()
        plt.savefig(bar_chart_buffer, dpi=fig.dpi, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor='none',
                    format='png')
        bar_chart_buffer.seek(0)
        result = bar_chart_buffer.read()
        bar_chart_buffer.close()
        return result

    def generate_bar_charts(self, start_date=None, end_date=None):
        top_mood_states, top_tasks = self.data_generator.calculate_most_used(start_date, end_date)
        tasks_chart = self.generate_bar_chart(top_tasks, 'Häufigste Aufgaben', 'skyblue')
        mood_chart = self.generate_bar_chart(top_mood_states, 'Häufigste Stimmungen', 'palegreen')
        return tasks_chart, mood_chart
