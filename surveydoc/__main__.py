import sys
import click
import json
from .google_survey_results import GoogleSurveyResultsRepository
from .google_doc_writer import GoogleDocWriter
from .chart_writer import ChartWriter
from .google_auth_flow import authenticate


@click.command()
@click.option('--credentials_path', default='credentials.json', type=click.Path(), help='The path to your Google credentials.json file')
@click.option('--config_path', default='config.json', type=click.File(), help='The path to your configuration file.')
def main(credentials_path, config_path):
    credentials = authenticate(credentials_path)

    config = json.load(config_path)
    config_path.close()

    survey_results_repository = GoogleSurveyResultsRepository(credentials)
    chart_writer = ChartWriter()

    for subject_config in config['subjects']:
        doc_writer = GoogleDocWriter(credentials)

        data = survey_results_repository.get_survey_results(
            subject_config['spreadsheet']['id'],
            subject_config['spreadsheet']['sheet'],
            subject_config['spreadsheet']['range']
        )

        response_map = config['response-map'][subject_config['response-map']]

        for idx, header in enumerate(data['headers']):
            style = response_map.get(str(idx), "Ignore")

            if style == 'DivergentBarChart':
                image_path = chart_writer.generate_chart(subject_config['name'], data['answers']['Timestamp'], data['answers'][header], header)
                doc_writer.divergent_bar_chart(header, image_path)
            elif style == "TextSummary":
                # TODO(mmk) We should probably have a separate class that
                # handles finding the right splice of answers and returns a
                # simple new line separated list of responses (having removed
                # all empty responses and randomized the answers)
                answers = data['answers'][header]
                answers.apply(str)
                doc_writer.text_summary(header, answers.values)

        doc_writer.generate_doc("Testing API")


if __name__ == '__main__':
    main()
