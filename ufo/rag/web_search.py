import requests
from ..config.config import load_config
from ..utils import print_with_color
from langchain.text_splitter import HTMLHeaderTextSplitter
from langchain.docstore.document import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

configs = load_config()

class BingSearchWeb:
    """
    Class to retrieve web documents.
    """
    
    def __init__(self):
        """
        Create a new WebRetriever.
        """
        self.api_key = configs.get("BING_API_KEY", "")

    def search(self, query: str, top_k: int = 1):
        """
        Retrieve the web document from the given URL.
        :param url: The URL to retrieve the web document from.
        :return: The web document from the given URL.
        """
        base_url = "https://api.bing.microsoft.com/v7.0/search"
        params = {"q": query}
        if top_k > 0:
            params["count"] = top_k

        try:
            response = requests.get(base_url, params=params, headers={"Ocp-Apim-Subscription-Key": self.api_key})
            response.raise_for_status()  # Raise exception for non-200 status codes
            result_list = []
            for item in response.json().get("webPages", {}).get("value", []):
                result_list.append({"name": item.get("name"), "url": item.get("url"), "snippet": item.get("snippet")})
            return result_list
        except requests.RequestException as e:
            print_with_color(f"Warning: Error when searching: {e}", "yellow")
            return []

    def get_url_text(self, url: str):
        """
        Retrieve the web document from the given URL.
        :param url: The URL to retrieve the web document from.
        :return: The web text from the given URL.
        """
        print(f"Getting search result for {url}") 
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise exception for non-200 status codes
            html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=[])
            document = html_splitter.split_text(response.text)
            return [Document(page_content=document.page_content, metadata={"url": url})]
        except requests.RequestException as e:
            print_with_color(f"Warning: Error in getting search result for {url}: {e}", "yellow")
            return [Document(page_content="", metadata={"url": url})]

    def create_documents(self, result_list: list):
        """
        Create documents from the given result list.
        :param result_list: The result list to create documents from.
        :return: The documents from the given result list.
        """
        document_list = []
        for result in result_list:
            documents = self.get_url_text(result.get("url", ""))
            for document in documents:
                page_content = document.page_content
                metadata = document.metadata
                metadata["url"] = result.get("url", "")
                metadata["name"] = result.get("name", "")
                metadata["snippet"] = result.get("snippet", "")
                document = Document(page_content=page_content, metadata=metadata)
                document_list.append(document)
        return document_list
    
    def create_indexer(self, documents: list):
        """
        Create an indexer for the given query.
        :param query: The query to create an indexer for.
        :return: The created indexer.
        """
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        db = FAISS.from_documents(documents, embeddings)
        return db
