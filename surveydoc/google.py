import os
import json
import pickle
import os.path
import pandas as pd
from datetime import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


def authenticate(credentials_path):
    scopes = [
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets.readonly'
    ]

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, scopes)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds


class DocWriter():
    def __init__(self, credentials, subject):
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

        self.insert_text("Below, you will find several graphs visualizing the results of your most recent survey. Each question is broken out into a separate graph for easier comparison against previous survey results.")
        self.insert_text("The graph we are using is a diverging bar chart. In this graph, anything to the right of the middle line is a positive response; anything to the left, negative. This is done to more accurately reflect the shifting sentiment of the team instead of hiding the details behind a contrived 'average' score.")
        self.insert_text("Under each section, I have reserved some space for analysis, comments or action items that might arise from our one-on-one review of these results. Please make sure anything you want captured on this document has been recorded to your satisfaction.")

    def generate_doc(self, title):
        document = self.service.documents().create(body={"title": title}).execute()
        self.service.documents().batchUpdate(documentId=document['documentId'], body={'requests': self.requests}).execute()

        # The breaks are stored in the order that they should be inserted, but
        # that will throw off the index count. So let's reverse them and then
        # insert them backwards.
        self.breaks.reverse()
        self.service.documents().batchUpdate(documentId=document['documentId'], body={'requests': self.breaks}).execute()

        return document['documentId']

    def divergent_bar_chart(self, question, image_path):
        self.insert_text(question)
        self.change_style("HEADING_1", "START")

        self.insert_image(image_path)
        self.insert_text("")  # Inserting a blank line to make sure the image isn't completely inline.

        self.insert_text("Comments")
        self.change_style("HEADING_2", "START")
        self.insert_text("")
        # TODO(mmk) We are going to have to generate something for the images in inline_objects

    def text_summary(self, question, answers):
        self.insert_text(question)
        self.change_style("HEADING_1", "START")

        # TODO(mmk) If the answers have a newline in them, then they are being
        # separated out into different bullet points. We need to convert the newlines to the line tabulation character (\u000b)
        self.insert_text("\n".join(answers))
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
        self.requests.append({"createParagraphBullets": {"range": self.last_range(), "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"}})

    def change_style(self, style, alignment):
        self.requests.append({"updateParagraphStyle": {"range": self.last_range(), "paragraphStyle": {"namedStyleType": style, "alignment": alignment}, "fields": "namedStyleType,alignment"}})

    def insert_image(self, image_path):
        self.requests.append({"insertInlineImage": {"uri": image_path, "endOfSegmentLocation": {"segmentId": ""}}})
        self.last_index = self.index
        self.index += 1

    def last_range(self):
        return {"startIndex": self.last_index, "endIndex": self.index}


class DriveManager():
    def __init__(self, credentials):
        self.service = build('drive', 'v3', credentials=credentials)

    def move_doc_to_folder(self, file_id, folder_id):
        uploaded_file = self.service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ','.join(uploaded_file['parents'])

        self.service.files().update(fileId=file_id, addParents=folder_id, removeParents=previous_parents).execute()


class SurveyResultsRepository():
    def __init__(self, credentials):
        self.service = build('sheets', 'v4', credentials=credentials)

    def get_survey_results(self, spreadsheetId, sheet, dataRange):
        result = self.service.spreadsheets().values().get(spreadsheetId=spreadsheetId,
                                                          range=f"{sheet}!{dataRange}").execute()

        values = result.get('values', [])
        questions = values[0]
        responses = pd.DataFrame(data=values[1:], columns=questions)
        responses["Timestamp"] = responses["Timestamp"].apply(
            lambda timestamp: datetime.strptime(timestamp, "%B %Y").strftime("%Y%m"))

        return {'questions': questions, 'answers': responses}
