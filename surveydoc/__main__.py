import sys
import click
import json
from .google_survey_results import GoogleSurveyResultsRepository
from .chart_writer import ChartWriter
from .google_auth_flow import authenticate


@click.command()
@click.option('--credentials_path', default='credentials.json', type=click.Path(), help='The path to your Google credentials.json file')
@click.option('--config_path', default='config.json', type=click.File(), help='The path to your configuration file.')
def main(credentials_path, config_path):
    credentials = authenticate(credentials_path)

    config = json.load(config_path)
    config_path.close()

    surveyResultsRepository = GoogleSurveyResultsRepository(credentials)
    chart_writer = ChartWriter()

    for subject_config in config['subjects']:
        data = surveyResultsRepository.get_survey_results(
            subject_config['spreadsheet']['id'],
            subject_config['spreadsheet']['sheet'],
            subject_config['spreadsheet']['range']
        )

        response_map = config['response-map'][subject_config['response-map']]

        for idx, header in enumerate(data['headers']):
            style = response_map.get(str(idx), "Ignore")

            if style == 'DivergentBarChart':
                chart_writer.generate_chart(subject_config['name'], data['answers']['Timestamp'], data['answers'][header], header)


if __name__ == '__main__':
    main()
