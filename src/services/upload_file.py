import cloudinary
import cloudinary.uploader
import logging
logging.basicConfig(level=logging.DEBUG)

class UploadFileService:
    def __init__(self, cloud_name, api_key, api_secret):
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file, username) -> str:
        logging.debug(f"Uploading file for user: {username}")
        try:
            public_id = f"RestApp/{username}"
            r = cloudinary.uploader.upload(file.file, public_id=public_id,
                                           overwrite=True)
            logging.debug(f"Upload response: {r}")
            src_url = cloudinary.CloudinaryImage(public_id).build_url(
                width=250, height=250, crop="fill", version=r.get("version")
            )
            return src_url
        except Exception as e:
            logging.error(f"Cloudinary upload error: {e}")
            raise
