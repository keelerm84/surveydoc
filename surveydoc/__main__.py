import click
import json
from datetime import datetime
from .google import authenticate, SurveyResultsRepository, DocWriter, DriveManager
from .formatters import DivergentBarChart, RecentResponses
from .aws import S3


@click.command()
@click.option('--credentials_path', default='credentials.json', type=click.Path(), help='The path to your Google credentials.json file')
@click.option('--config_path', default='config.json', type=click.File(), help='The path to your configuration file.')
def main(credentials_path, config_path):
    credentials = authenticate(credentials_path)

    config = json.load(config_path)
    config_path.close()

    drive_manager = DriveManager(credentials)
    survey_results_repository = SurveyResultsRepository(credentials)
    divergent_bar_chart = DivergentBarChart()
    recent_responses = RecentResponses()
    s3 = S3(config['s3']['bucket'], config['s3']['directory'])

    for subject_config in config['subjects']:
        doc_writer = DocWriter(credentials, subject_config['name'])

        survey_results = survey_results_repository.get_survey_results(
            subject_config['spreadsheet']['id'],
            subject_config['spreadsheet']['sheet'],
            subject_config['spreadsheet']['range']
        )

        response_map = config['response-map'][subject_config['response-map']]

        for idx, question in enumerate(survey_results['questions']):
            style = response_map.get(str(idx), "Ignore")

            if style != 'Ignore':
                doc_writer.insert_page_break()

            if style == 'DivergentBarChart':
                image_path = divergent_bar_chart.generate(subject_config['name'], survey_results['answers']['Timestamp'], survey_results['answers'][question], question)
                s3_path = s3.write_to_s3(image_path)
                doc_writer.divergent_bar_chart(question, s3_path)
            elif style == "TextSummary":
                answers = recent_responses.filter(survey_results['answers']['Timestamp'], survey_results['answers'][question])
                answers = answers.sample(frac=1)

                doc_writer.text_summary(question, answers)

        document_id = doc_writer.generate_doc("{} {}".format(datetime.now().strftime("%Y-%m"), subject_config['name']))
        drive_manager.move_doc_to_folder(document_id, subject_config['drive-folder'])

if __name__ == '__main__':
    main()
