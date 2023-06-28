import os
import os.path
import pickle
import dateutil.parser
from datetime import datetime

import pandas as pd
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


def authenticate(credentials_path):
    scopes = [
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets.readonly'
    ]

    credentials = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, scopes)
            credentials = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    return credentials


class DocWriter:
    def __init__(self, credentials, subject, explanations):
        self.service = build('docs', 'v1', credentials=credentials)

        self.index = 1
        self.last_index = 1
        self.requests = []
        self.breaks = []

        self.insert_text(subject)
        self.change_style("TITLE", "CENTER")

        self.insert_text("Survey Results: {}".format(datetime.now().strftime("%B %Y")))
        self.change_style("SUBTITLE", "CENTER")

        self.insert_text("Overview and Explanation")
        self.change_style("HEADING_1", "START")

        for explanation in explanations:
            self.insert_text(explanation)
            self.insert_text("")

    def generate_doc(self, title):
        document = self.service.documents().create(body={"title": title}).execute()
        self.service.documents().batchUpdate(documentId=document['documentId'],
                                             body={'requests': self.requests}).execute()

        # The breaks are stored in the order that they should be inserted, but
        # that will throw off the index count. So let's reverse them and then
        # insert them backwards.
        self.breaks.reverse()
        self.service.documents().batchUpdate(documentId=document['documentId'],
                                             body={'requests': self.breaks}).execute()

        return document['documentId']

    def divergent_bar_chart(self, question, image_path):
        self.insert_text(question)
        self.change_style("HEADING_1", "START")

        self.insert_image(image_path)
        self.insert_text("")  # Inserting a blank line to make sure the image isn't completely inline.

        self.insert_text("Comments")
        self.change_style("HEADING_2", "START")
        self.insert_text("")

    def text_summary(self, question, answers):
        self.insert_text(question)
        self.change_style("HEADING_1", "START")

        formatted = [answer.replace("\n", u"\u000b") for answer in answers]

        self.insert_text("\n".join(formatted))
        self.change_to_bullets()

        self.insert_text("Comments")
        self.change_style("HEADING_2", "START")
        self.insert_text("")

    def insert_page_break(self):
        self.breaks.append({"insertPageBreak": {"location": {"index": self.index}}})

    def insert_text(self, text):
        content_length = len(text.encode('utf-16-le')) / 2 + 1  # Adding 1 for the newline
        self.requests.append({"insertText": {"endOfSegmentLocation": {"segmentId": ""}, "text": f"{text}\n"}})
        self.last_index = self.index
        self.index += content_length

    def change_to_bullets(self):
        self.requests.append(
            {"createParagraphBullets": {"range": self.last_range(), "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"}})

    def change_style(self, style, alignment):
        self.requests.append({"updateParagraphStyle": {"range": self.last_range(),
                                                       "paragraphStyle": {"namedStyleType": style,
                                                                          "alignment": alignment},
                                                       "fields": "namedStyleType,alignment"}})

    def insert_image(self, image_path):
        self.requests.append({"insertInlineImage": {"uri": image_path, "endOfSegmentLocation": {"segmentId": ""}}})
        self.last_index = self.index
        self.index += 1

    def last_range(self):
        return {"startIndex": self.last_index, "endIndex": self.index}


class DriveManager:
    def __init__(self, credentials):
        self.service = build('drive', 'v3', credentials=credentials)

    def move_doc_to_folder(self, file_id, folder_id):
        uploaded_file = self.service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ','.join(uploaded_file['parents'])

        self.service.files().update(fileId=file_id, addParents=folder_id, removeParents=previous_parents).execute()


class SurveyResultsRepository:
    def __init__(self, credentials):
        self.service = build('sheets', 'v4', credentials=credentials)

    def get_survey_results(self, spreadsheet_id, sheet, data_range):
        result = self.service.spreadsheets().values().get(spreadsheetId=spreadsheet_id,
                                                          range=f"{sheet}!{data_range}").execute()

        values = result.get('values', [])
        questions = values[0]
        responses = pd.DataFrame(data=values[1:], columns=questions)
        responses["Timestamp"] = responses["Timestamp"].apply(
            lambda timestamp: dateutil.parser.parse(timestamp).strftime("%Y%m"))

        return {'questions': questions, 'answers': responses}
