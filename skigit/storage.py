import os
from tempfile import NamedTemporaryFile

from cache_memoize import cache_memoize
from django.conf import settings
from django.core.files.storage import Storage
from django.core.files.base import File
from django.utils.deconstruct import deconstructible

from b2sdk.v1 import InMemoryAccountInfo, B2Api


@deconstructible
class B2Storage(Storage):
    def __init__(self):
        overrides = locals()
        self.application_key_id = settings.BACKBLAZE_KEY_ID
        self.application_key = settings.BACKBLAZE_APPLICATION_KEY

    # @cache_memoize(settings.BACKBLAZE_CACHE_EXPIRES)
    def client(self):
        info = InMemoryAccountInfo()
        b2_api = B2Api(info)
        b2_api.authorize_account("production", self.application_key_id, self.application_key)
        return b2_api

    # @cache_memoize(settings.BACKBLAZE_CACHE_EXPIRES)
    def bucket(self):
        b2_api = self.client()
        return b2_api.get_bucket_by_name(settings.BACKBLAZE_BUCKET)

    def upload(self, path, name):

        resp = self.bucket().upload_local_file(local_file=path, file_name=name)
        return resp

    def delete(self, file_id, name):
        b2_api = self.client()
        try:
            b2_api.delete_file_version(file_id, name)
        except:
            pass

    @cache_memoize(settings.BACKBLAZE_CACHE_EXPIRES)
    def get_meta(self, file_id):
        return self.client().get_file_info(file_id)
