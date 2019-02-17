import tempfile
import uuid
import pandas as pd
from datetime import datetime
import plotly.graph_objs as go
import plotly.io as pio
from string import punctuation
import os

pio.orca.config.executable = './node_modules/orca/bin/orca.js'


class DivergentBarChart():
    def generate(self, subject, timestamps, answers, question):
        answers = answers.apply(lambda x: int(x) if x != '' and x is not None else 0)
        answers = answers[answers > 0]
        frequencies = pd.crosstab(timestamps, answers, normalize='index')

        for index in range(1, 5):
            if index not in frequencies.columns:
                frequencies[index] = 0

        frequencies[0] = 1 - frequencies[1] - frequencies[2]
        frequencies[5] = 1 - frequencies[3] - frequencies[4]

        figure = go.Figure(layout=go.Layout(barmode='stack', title=None, margin=dict(b=0, t=0), showlegend=False,
                                            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                                            yaxis=dict(autorange=True), autosize=True))

        colors = [
            'rgba(255, 255, 255, 1)',
            'rgba(220, 57, 18, 1)',
            'rgba(255, 153, 0, 1)',
            'rgba(16, 150, 24, 1)',
            'rgba(153, 0, 153, 1)',
            'rgba(255, 255, 255, 1)'
        ]
        for index in range(0, 6):
            self._add_bar(figure, frequencies[index][::-1], frequencies.index[::-1], colors[index])

        if not os.path.exists(subject):
            os.mkdir(subject)

        translation_table = str.maketrans("", "", punctuation)

        image_path = "{}.png".format(os.path.join(tempfile.mkdtemp(), str(uuid.uuid4())))
        pio.write_image(figure, image_path, format='png', scale=1, height=30 * len(frequencies))

        return image_path

    def _add_bar(self, figure, values, months, fill_color):
        figure.add_bar(
            x=values,
            y=[datetime.strptime(month, "%Y%m").strftime("%b %Y") for month in months],
            orientation='h',
            marker=dict(
                color=fill_color,
                line=None
            )
        )


class RecentResponses():
    def filter(self, timestamps, answers):
        indexes = timestamps.loc[timestamps == timestamps.iloc[-1]].index
        answers = answers[indexes]
        return answers[answers.apply(lambda x: len(x) > 0)]
