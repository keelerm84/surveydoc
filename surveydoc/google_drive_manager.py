from googleapiclient.discovery import build


class GoogleDriveManager():
    def __init__(self, credentials):
        self.service = build('drive', 'v3', credentials=credentials)

    def move_doc_to_folder(self, file_id, folder_id):
        uploaded_file = self.service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ','.join(uploaded_file['parents'])

        self.service.files().update(fileId=file_id, addParents=folder_id, removeParents=previous_parents).execute()
