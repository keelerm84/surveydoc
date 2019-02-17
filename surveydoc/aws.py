import boto3
import uuid


class S3():
    def __init__(self, bucket, path):
        self.s3 = boto3.resource('s3')
        self.bucket = bucket
        self.path = path

    def write_to_s3(self, image_path):
        key = "{}/{}".format(self.path, uuid.uuid4())

        self.s3.Object(self.bucket, key).put(Body=open(image_path, 'rb'))

        return self.s3.meta.client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': self.bucket,
                'Key': key
            },
            ExpiresIn=3 * 60
        )
