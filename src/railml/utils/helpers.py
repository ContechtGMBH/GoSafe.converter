from py2neo import Node, Relationship
from .spatial import extract_elements_coords
from .variables import DEFAULT_NAMESPACE

#
# extracts topology nodes - all features from the end and from the beginning of the track
#
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

#
# Depending on xml_node parameter:
# extracts all track elements - can be touched in real life
# extracts all ocs elements - control system elements
#
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

#
# extracts all switches
#
def get_track_switches(graph, switch, track_node, projection):
    switch_attributes = switch.attrib

    switch_coords = switch.xpath("rail:geoCoord/@coord", namespaces=DEFAULT_NAMESPACE)
    if len(switch_coords):
        wkt_geometry = extract_elements_coords(switch_coords[0], projection)
        switch_attributes['geometry'] = wkt_geometry

    switch_node = Node("Switch", **switch_attributes)

    graph.create(switch_node)

    relationship = Relationship(track_node, "HAS_SWITCH", switch_node)

    graph.create(relationship)

    connection_attributes = switch.xpath("rail:connection", namespaces=DEFAULT_NAMESPACE)[0].attrib
    connection_node = Node("Connection", **connection_attributes)
    graph.create(connection_node)
    connection_relationship = Relationship(switch_node, "HAS_CONNECTION", connection_node)
    graph.create(connection_relationship)

#
# extracts all crossings
#
def get_track_crossings(graph, crossing, track_node, projection):
    crossing_attributes = crossing.attrib

    crossing_coords = crossing.xpath("rail:geoCoord/@coord", namespaces=DEFAULT_NAMESPACE)
    if len(crossing_coords):
        wkt_geometry = extract_elements_coords(crossing_coords[0], projection)
        crossing_attributes['geometry'] = wkt_geometry

    crossing_node = Node("Crossing", **crossing_attributes)

    graph.create(crossing_node)

    relationship = Relationship(track_node, "HAS_CROSSING", crossing_node)

    graph.create(relationship)

    crossing_connections = crossing.xpath("rail:connection", namespaces=DEFAULT_NAMESPACE)

    for crossing_connection in crossing_connections:
        connection_attributes = crossing_connection.attrib
        connection_node = Node("Connection", **connection_attributes)
        graph.create(connection_node)
        connection_relationship = Relationship(crossing_node, "HAS_CONNECTION", connection_node)
        graph.create(connection_relationship)
