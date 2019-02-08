import pandas as pd
from datetime import datetime
from googleapiclient.discovery import build


class GoogleSurveyResultsRepository():
    def __init__(self, credentials):
        self.service = build('sheets', 'v4', credentials=credentials)

    def get_survey_results(self, spreadsheetId, sheet, dataRange):
        result = self.service.spreadsheets().values().get(spreadsheetId=spreadsheetId,
                                                          range=f"{sheet}!{dataRange}").execute()

        values = result.get('values', [])
        headers = values[0]
        responses = pd.DataFrame(data=values[1:], columns=headers)
        responses["Timestamp"] = responses["Timestamp"].apply(
            lambda timestamp: datetime.strptime(timestamp, "%B %Y").strftime("%Y%m"))

        return {'headers': headers, 'answers': responses}
