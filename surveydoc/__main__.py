import click
import json
from .google_survey_results import GoogleSurveyResultsRepository
from .google_doc_writer import GoogleDocWriter
from .formatters import DivergentBarChart, RecentResponses
from .google_auth_flow import authenticate
from .google_drive_manager import GoogleDriveManager


@click.command()
@click.option('--credentials_path', default='credentials.json', type=click.Path(), help='The path to your Google credentials.json file')
@click.option('--config_path', default='config.json', type=click.File(), help='The path to your configuration file.')
def main(credentials_path, config_path):
    credentials = authenticate(credentials_path)

    config = json.load(config_path)
    config_path.close()

    google_drive_manager = GoogleDriveManager(credentials)
    survey_results_repository = GoogleSurveyResultsRepository(credentials)
    divergent_bar_chart = DivergentBarChart()
    recent_responses = RecentResponses()

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
                image_path = divergent_bar_chart.generate(subject_config['name'], data['answers']['Timestamp'], data['answers'][header], header)
                document_id = doc_writer.divergent_bar_chart(header, image_path)
            elif style == "TextSummary":
                answers = recent_responses.filter(data['answers']['Timestamp'], data['answers'][header])
                doc_writer.text_summary(header, answers)

        document_id = doc_writer.generate_doc("Testing API")
        google_drive_manager.move_doc_to_folder(document_id, subject_config['drive_folder'])


if __name__ == '__main__':
    main()
