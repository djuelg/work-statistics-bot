import io
import re
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.style as style
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from statistics.data_generator import NEWLINE
from statistics.mood_colors import get_mood_color


class ChartGenerator:
    def __init__(self, data_generator):
        self.data_generator = data_generator

    def _prepare_line_chart(self, ax, energy, stress, fatigue, demotivation, labels, title, compact=False):
        median_energy = np.average([value for value in energy if value is not None]) if energy else 0
        median_stress = np.average([value for value in stress if value is not None]) if stress else 0
        median_fatigue = np.average([value for value in fatigue if value is not None]) if fatigue else 0
        median_demotivation = np.average([value for value in demotivation if value is not None]) if demotivation else 0
        linewidth = 5.0 if not compact else 3.0
        markersize = 24 if not compact else 18
        ax.plot(energy, range(len(labels)), label=f'Schläfrigkeit (Avg: {median_energy:.2f})', marker='o',
                markersize=markersize, linestyle='solid', alpha=1, color='skyblue', linewidth=linewidth)
        ax.plot(fatigue, range(len(labels)), label=f'Mentale Ermüdung (Avg: {median_fatigue:.2f})', marker='o',
                markersize=markersize, linestyle='solid', alpha=1, color='palegreen', linewidth=linewidth)
        ax.plot(demotivation, range(len(labels)), label=f'Unlust (Avg: {median_demotivation:.2f})', marker='o',
                markersize=markersize, linestyle='solid', alpha=1, color='wheat', linewidth=linewidth)
        ax.plot(stress, range(len(labels)), label=f'Stress Level (Avg: {median_stress:.2f})', marker='o',
                markersize=markersize,
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

    # TODO: Different row heights for different number of moods
    # TODO: larger resolution -> The problem is downscaling done by telegram
    def generate_mood_calendar(self, start_date=None, end_date=None):
        # Function to format date from YYYY-MM-DD to DD.MM.
        def format_date(date_str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%d.%m.')

        morning_mood_states, afternoon_mood_states = self.data_generator.prepare_mood_calendar_data(start_date, end_date)

        # Set up the colors
        border_gray = (90, 90, 90)

        # Set up the image properties
        date_cell_width = 172  # Width of the date column
        cell_width = 274  # Increase column width
        cell_height = 160  # Increase row height
        padding = 30  # Increase padding
        header_height = 80  # Increase header height
        num_rows = len(morning_mood_states.keys())  # Extra row for the header
        image_width = date_cell_width + cell_width * 2 + 2 * padding  # 3 columns: Date, Morning, Afternoon
        image_height = num_rows * cell_height + header_height + padding

        # Create a blank image with a dark background
        img = Image.new('RGB', (image_width, image_height), color=(64, 64, 64))
        draw = ImageDraw.Draw(img)

        # Load a smoother font (ensure this font file is in the same directory or provide a full path)
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 28)  # Larger, smoother font
            header_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)  # Bold font for header
        except IOError:
            # Fallback to default if font not found
            font = ImageFont.load_default()
            header_font = ImageFont.load_default()

        # Draw table headers
        headers = ['Datum', 'Mogens', 'Abends']
        header_y = padding

        for i, header in enumerate(headers):
            x = (padding + i * date_cell_width) if i <= 1 else (padding + date_cell_width + cell_width)
            draw.text((x + 10, header_y + 10), header, font=header_font, fill=(250, 250, 250))

        # Draw a horizontal line for header separation
        draw.line([(padding, header_y + header_height), (image_width - padding, header_y + header_height)],
                  fill=border_gray, width=1)

        # Function to draw colored circles and mood states
        def draw_mood_states(moods, x, y, draw, font):
            circle_radius = 6  # Smaller circles
            circle_offset_x = -10
            text_offset_x = circle_offset_x + 2 * circle_radius + 10
            current_y = y

            for mood in moods:
                # Get circle color
                color = get_mood_color(mood)

                # Calculate text size to vertically center the circle
                bbox = draw.textbbox((0, 0), mood, font=font)
                text_height = bbox[3] - bbox[1]  # Height of the text
                circle_y = current_y + (((text_height - 2) * 1.5) / 2) - circle_radius
                # ((text_height - 2 * circle_radius) / 2)  # Center the circle vertically

                # Draw the circle
                draw.ellipse(
                    [x + circle_offset_x, circle_y, x + circle_offset_x + 2 * circle_radius,
                     circle_y + 2 * circle_radius],
                    fill=color
                )

                # Draw the mood text next to the circle
                draw.text((x + text_offset_x, current_y), mood, font=font, fill=(250, 250, 250))

                # Move to next line
                current_y += 36  # Adjust line spacing for larger font and smaller circles

        # Draw table rows for each date
        for row_index, date in enumerate(morning_mood_states.keys()):
            y = header_y + header_height + row_index * cell_height
            date_x = padding
            morning_x = padding + date_cell_width
            afternoon_x = padding + date_cell_width + cell_width

            # Format date and draw it
            formatted_date = format_date(date)
            draw.text((date_x + 10, y + 10), formatted_date, font=font, fill=(250, 250, 250))

            # Draw mood states for morning and afternoon
            morning_moods = sorted(list(set(morning_mood_states[date])))
            afternoon_moods = sorted(list(set(afternoon_mood_states[date])))
            draw_mood_states(morning_moods, morning_x, y + 10, draw, font)
            draw_mood_states(afternoon_moods, afternoon_x, y + 10, draw, font)

            # Draw horizontal lines to separate rows
            draw.line([(padding, y), (image_width - padding, y)], fill=border_gray, width=1)

        # Save the image to a file
        image_buffer = io.BytesIO()
        img.save(image_buffer, format="PNG")
        image_buffer.seek(0)
        return image_buffer  # Image.open(image_buffer)
