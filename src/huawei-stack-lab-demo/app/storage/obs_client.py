import os
import time

from obs import ObsClient, PutObjectHeader

RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}
MAX_RETRIES = 3


def _call_obs_with_retry(call):
    delay = 0.5
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = call()
            if resp.status < 300:
                return resp
            if resp.status not in RETRYABLE_STATUS:
                raise RuntimeError(f"OBS failed: status={resp.status}, reason={resp.reason}")
            last_err = RuntimeError(f"OBS failed: status={resp.status}")
        except (TimeoutError, ConnectionError) as e:
            last_err = e
        if attempt == MAX_RETRIES - 1:
            raise last_err
        time.sleep(delay)
        delay *= 2


def build_obs_client() -> ObsClient:
    return ObsClient(
        access_key_id=os.environ["OBS_AK"],
        secret_access_key=os.environ["OBS_SK"],
        server=os.environ["OBS_ENDPOINT"],
    )


class ObjectStorage:
    def __init__(self, client: ObsClient, bucket: str):
        self._client = client
        self._bucket = bucket

    def upload_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        def _put():
            return self._client.putContent(
                self._bucket,
                key,
                data,
                headers=PutObjectHeader(contentType=content_type),
            )

        _call_obs_with_retry(_put)
        return key

    def download_bytes(self, key: str) -> bytes:
        def _get():
            return self._client.getObject(self._bucket, key, loadStreamInMemory=True)

        resp = _call_obs_with_retry(_get)
        return resp.body.buffer

    def probe_bucket(self) -> None:
        """Lightweight readiness check: list at most one object in the bucket."""
        def _list():
            return self._client.listObjects(self._bucket, max_keys=1)

        _call_obs_with_retry(_list)

    def list_keys(self, prefix: str = ""):
        def _list():
            return self._client.listObjects(self._bucket, prefix=prefix)

        resp = _call_obs_with_retry(_list)
        for obj in resp.body.contents or []:
            yield obj.key

    def create_presigned_download_url(self, key: str, expires: int = 3600):
        return self._client.createSignedUrl(
            method="GET",
            bucketName=self._bucket,
            objectKey=key,
            expires=expires,
        )

    def create_presigned_upload_url(
        self,
        key: str,
        content_type: str = "application/octet-stream",
        expires: int = 3600,
    ):
        return self._client.createSignedUrl(
            method="PUT",
            bucketName=self._bucket,
            objectKey=key,
            expires=expires,
            headers={"Content-Type": content_type},
        )
