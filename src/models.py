from py2neo import Graph

#
# database credentials
#
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "test"
NEO4J_PORT = "7474"
NEO4J_HOST = "localhost"

NEO4J_URI = "http://" + NEO4J_USERNAME + ":" + NEO4J_PASSWORD + "@" + NEO4J_HOST + ":" + NEO4J_PORT + "/db/data"

db = Graph(NEO4J_URI)
