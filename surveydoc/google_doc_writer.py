from googleapiclient.discovery import build
import base64


class GoogleDocWriter():
    def __init__(self, credentials):
        self.service = build('docs', 'v1', credentials=credentials)

        self.index = 1
        self.last_index = 1
        self.requests = []

        self.insert_text("Overview and Explanation")
        self.change_style("HEADING_1", "START")

        self.insert_text("Below, you will find several graphs visualizing the results of your most recent survey. Each question is broken out into a separate graph for easier comparison against previous survey results.")
        self.insert_text("The graph we are using is a diverging bar chart. In this graph, anything to the right of the middle line is a positive response; anything to the left, negative. This is done to more accurately reflect the shifting sentiment of the team instead of hiding the details behind a contrived 'average' score.")
        self.insert_text("For each graph, the following legend holds.")
        self.insert_text("Under each section, I have reserved some space for analysis, comments or action items that might arise from our one-on-one review of these results. Please make sure anything you want captured on this document has been recorded to your satisfaction.")

    def generate_doc(self, title):
        document = self.service.documents().create(body={"title": title}).execute()
        self.service.documents().batchUpdate(documentId=document['documentId'], body={'requests': self.requests}).execute()

    def divergent_bar_chart(self, question, image_path):
        self.insert_text(question)
        self.change_style("HEADING_1", "START")

        self.insert_image(image_path)

        self.insert_text("Comments")
        self.change_style("HEADING_2", "START")
        # TODO(mmk) We are going to have to generate something for the images in inline_objects

    def text_summary(self, question, answers):
        self.insert_text(question)
        self.change_style("HEADING_1", "START")

        self.insert_text("\n".join(answers))
        self.change_to_bullets()

    def insert_text(self, text):
        content_length = len(text.encode('utf-16-le')) / 2 + 1  # Adding 1 for the newline
        self.requests.append({"insertText": {"location": {"index": self.index}, "text": f"{text}\n"}})
        self.last_index = self.index
        self.index += content_length

    def change_to_bullets(self):
        self.requests.append({"createParagraphBullets": {"range": self.last_range(), "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"}})

    def change_style(self, style, alignment):
        self.requests.append({"updateParagraphStyle": {"range": self.last_range(), "paragraphStyle": {"namedStyleType": style, "alignment": alignment}, "fields": "namedStyleType,alignment"}})

    def insert_image(self, image_path):
        print(image_path)
        self.requests.append({"insertInlineImage": {"uri": image_path, "location": {"index": self.index}}})
        self.last_index = self.index
        self.index += 1

    def last_range(self):
        return {"startIndex": self.last_index, "endIndex": self.index}
