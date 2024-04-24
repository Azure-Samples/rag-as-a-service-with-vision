import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


_LOCAL_ENV = "local"


class ApiRequestManager(object):
    _session: requests.Session
    _base_url: str

    def __init__(self, env: str):
        # create a requests session with retries
        self._session = requests.Session()
        retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        self._session.mount("http://", HTTPAdapter(max_retries=retries))
        self._session.mount("https://", HTTPAdapter(max_retries=retries))

        self._base_url = self._build_url(env)


    def _build_url(self, env: str) -> str:
        if env == _LOCAL_ENV:
            return "http://localhost:8080"
        raise Exception(f"Environment {env} not supported")


    def upload(
        self,
        files,
        config_id: str
    ):
        params = {
            "rag_config": config_id
        }
        res = self._session.post(
            files=files,
            url=self.upload_url,
            params=params
        )

        return res
        

    def upload_config(
        self,
        config: dict
    ):
        res = self._session.post(
            json=config,
            url=self.upload_config_url
        )

        return res


    def chat(
        self,
        query: str,
        config_id: str
    ):
        body = {
            "query": query,
            "rag_config": config_id
        }

        res = self._session.post(
            json=body,
            url=self._chat_url
        )

        return res


    def search(
        self,
        query: str,
        config_id: str
    ):
        body = {
            "query": query,
            "rag_config": config_id
        }

        res = self._session.post(
            json=body,
            url=self._chat_url
        )

        return res


    @property
    def _chat_url(self) -> str:
        return f"{self._base_url}/rag/chat"
    
    @property
    def search_url(self) -> str:
        return f"{self._base_url}/rag/search"

    @property
    def upload_url(self) -> str:
        return f"{self._base_url}/rag/upload"

    
    @property
    def upload_config_url(self) -> str:
        return f"{self._base_url}/config/"
