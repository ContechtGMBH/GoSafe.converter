from py2neo import Node, Relationship
from .spatial import extract_elements_coords
from .variables import DEFAULT_NAMESPACE

def topology_node(graph, xml_node, label, relation, track_node, coords, projection):
    if len(coords):
        wkt_geometry = extract_elements_coords(coords[0], projection)
        attributes = xml_node[0].attrib
        attributes['geometry'] = wkt_geometry
        topology_node = Node(label, **attributes)
    else:
        topology_node = Node(label, **xml_node[0].attrib)
    graph.create(topology_node)
    relationship = Relationship(track_node, relation, topology_node)
    graph.create(relationship)

def get_track_elements(graph, xml_node, label, relation, track_node, projection):
    for node in xml_node:
        element_coords = node.xpath("rail:geoCoord/@coord", namespaces=DEFAULT_NAMESPACE)
        if len(element_coords):
            wkt_geometry = extract_elements_coords(element_coords[0], projection)
            attributes = node.attrib
            attributes['geometry'] = wkt_geometry
            track_element_node = Node(label, **attributes)
        else:
            track_element_node = Node(label, **node.attrib)
        graph.create(track_element_node)
        relationship = Relationship(track_node, relation, track_element_node)
        graph.create(relationship)

def get_track_switches():
    pass

def get_track_crossings():
    pass
