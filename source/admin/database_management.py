'''
Administrator functions for database

Copyright 2014 Boris Dayma
'''


import pymongo


def set_up_mongodb_server(mongodb_server, login, password, versions):
    '''Sets up a mongodb server for GridCompute.

    Mongo database "gridcompute" is set up to be ready for use by creating "versions" collection and indexes.
    The "gridcompute" database must be present on the server. Any collection in it will be removed.

    Args:
        mongodb_server: Address of the mongo instance including connection port containing
                      "gridcompute" database.
                      Example: 'mongodbserver.com:888' or '10.0.0.1:888' or 'Machine123:888'
        login: Login used to connect on mongo database.
        password: Password used to connect on mongo database.
        versions: List of versions of gridcompute that the mongo database recognizes defined by
                _id: version number (ex: '0.1')
                status: either "allowed", "warning" or "refused"
                message: message to be displayed when status is not "allowed"
                example: [{'_id':'0.1', status:"warning", message:"this is a beta version used for test purposes only"}, {'_id':'1.0', status:"allowed"}]
    '''

    # create new connection
    mongodb = pymongo.MongoClient('{}'.format(mongodb_server)).gridcompute
    mongodb.authenticate(login, password)

    # drop all previous collections
    for collection in mongodb.collection_names(False):
        mongodb.drop_collection(collection)

    # create "versions" collection and populate it
    mongodb['versions'].insert(versions)

if __name__ == "__main__":

    # Define variables of mongodb server
    mongodb_server = 'localhost:27017'
    login, password = 'default_grid', 'gridcompute'
    versions = [{'_id':'0.2', 'status':'warning', 'message':'This is a beta version used for test purposes only'}]

    # Set up MongoDB server
    set_up_mongodb_server(mongodb_server, login, password, versions)
