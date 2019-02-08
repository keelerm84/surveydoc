
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import pandas as pd
from datetime import datetime


class GoogleSurveyResultsRepository():
    # If modifying these scopes, delete the file token.json.
    SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'

    def __init__(self):
        store = file.Storage('token.json')
        creds = store.get()

        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('credentials.json', self.SCOPES)
            creds = tools.run_flow(flow, store)

        self.service = build('sheets', 'v4', http=creds.authorize(Http()))

    def get_survey_results(self, spreadsheetId, sheet, dataRange):
        result = self.service.spreadsheets().values().get(spreadsheetId=spreadsheetId,
                                                          range=f"{sheet}!{dataRange}").execute()

        values = result.get('values', [])
        headers = values[0]
        responses = pd.DataFrame(data=values[1:], columns=headers)
        responses["Timestamp"] = responses["Timestamp"].apply(
            lambda timestamp: datetime.strptime(timestamp, "%B %Y").strftime("%Y%m"))

        return {'headers': headers, 'answers': responses}
