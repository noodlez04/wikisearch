import re

from pymongo import MongoClient

from wikisearch.consts.mongo import ENTRY_TITLE


class MongoHandler:
    """
        A utility class to communicate with mongo database.
        Each Mongo Handler is per database and collection. If the database or the collection doesn't exist the
        handler will create them locally.
    """

    def __init__(self, database, collection):
        self._mongo_client = MongoClient()
        self._collection = self._mongo_client[database][collection]

    def get_all_documents(self):
        return self._collection.find()

    def get_page(self, title):
        return self._collection.find_one({'title': title})

    def get_page_by_regex(self, title_regex):
        regex = re.compile(title_regex)
        return self._collection.find_one({'title': regex})

    def project_page_by_field(self, field_name):
        return self._collection.find({}, {field_name: True})

    def update_page(self, page):
        """
        Updates a document by it the page title. If the document doesn't exist, insert it
        (the parameter 'upsert' is in charge of that)
        :param page: the updated page
        """
        filter_title = {'title': page[ENTRY_TITLE]}
        updated_value = {"$set": page}
        self._collection.update_one(filter_title, updated_value, upsert=True)

    def is_empty_collection(self):
        return self._collection.count_documents({}) == 0

    def delete_collection_data(self):
        self._collection.delete_many({})

    def insert_data(self, data):
        self._collection.insert_many(data)
