from flask import Blueprint, request, jsonify
from src.models import db as graph
from lxml import etree
from py2neo import Node, Relationship, NodeSelector
from utils.variables import DEFAULT_NAMESPACE, OCS_ELEMENTS, TRACK_ELEMENTS
from utils.spatial import extract_tracks_coords, extract_elements_coords
from utils.utilities import get_track_elements, topology_node

railml = Blueprint('railml', __name__, url_prefix='/api/v1/railml')

@railml.route("/import", methods=["POST"])
def import_railml():
    _EPSG = request.form["epsg"]
    document = etree.parse(request.files["file"])
    tracks = document.xpath(".//rail:track", namespaces=DEFAULT_NAMESPACE)

    _CONNECTIONS = []

    for track in tracks:
        track_coords = track.xpath(".//rail:geoMapping/rail:geoCoord/@coord", namespaces=DEFAULT_NAMESPACE)
        if len(track_coords) > 1:
            wkt_geometry = extract_tracks_coords(track_coords, _EPSG)
            attributes = track.attrib
            attributes['geometry'] = wkt_geometry
            track_node = Node("Track", **attributes)
        else:
            track_node = Node("Track", **track.attrib) #basic track node

        graph.create(track_node)

        track_switches = track.xpath("rail:trackTopology/rail:connections//rail:switch", namespaces=DEFAULT_NAMESPACE) # extract switches

        for switch in track_switches:
            # create switch nodes and connect them to the track
            switch_attributes = switch.attrib

            switch_coords = switch.xpath("rail:geoCoord/@coord", namespaces=DEFAULT_NAMESPACE)
            if len(switch_coords):
                wkt_geometry = extract_elements_coords(switch_coords[0], _EPSG)
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

        track_crossings = track.xpath("rail:trackTopology/rail:connections//rail:crossing", namespaces=DEFAULT_NAMESPACE) # extract crossings

        for crossing in track_crossings:
            # create crossing nodes and connect them to the track
            crossing_attributes = crossing.attrib

            crossing_coords = crossing.xpath("rail:geoCoord/@coord", namespaces=DEFAULT_NAMESPACE)
            if len(crossing_coords):
                wkt_geometry = extract_elements_coords(crossing_coords[0], _EPSG)
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

        # track begin connections
        b_connection = track.xpath("rail:trackTopology/rail:trackBegin//rail:connection", namespaces=DEFAULT_NAMESPACE)
        b_buffer_stop = track.xpath("rail:trackTopology/rail:trackBegin//rail:bufferStop", namespaces=DEFAULT_NAMESPACE)
        b_open_end = track.xpath("rail:trackTopology/rail:trackBegin//rail:openEnd", namespaces=DEFAULT_NAMESPACE)
        b_macroscopic_node = track.xpath("rail:trackTopology/rail:trackBegin//rail:macroscopicNode", namespaces=DEFAULT_NAMESPACE)
        b_coords = track.xpath("rail:trackTopology/rail:trackBegin//rail:geoCoord/@coord", namespaces=DEFAULT_NAMESPACE)

        if len(b_connection):
            _CONNECTIONS.append(b_connection[0].attrib)
            topology_node(graph, b_connection, "Connection", "BEGINS", track_node, b_coords, _EPSG)
        elif len(b_buffer_stop):
            topology_node(graph, b_buffer_stop, "Buffer Stop", "BEGINS", track_node, b_coords, _EPSG)
        elif len(b_open_end):
            topology_node(graph, b_open_end, "Open End", "BEGINS", track_node, b_coords, _EPSG)
        elif len(b_macroscopic_node):
            topology_node(graph, b_macroscopic_node, "Macroscopic Node", "BEGINS", track_node, b_coords, _EPSG)

        # track end connections
        e_connection = track.xpath("rail:trackTopology/rail:trackEnd//rail:connection", namespaces=DEFAULT_NAMESPACE)
        e_buffer_stop = track.xpath("rail:trackTopology/rail:trackEnd//rail:bufferStop", namespaces=DEFAULT_NAMESPACE)
        e_open_end = track.xpath("rail:trackTopology/rail:trackEnd//rail:openEnd", namespaces=DEFAULT_NAMESPACE)
        e_macroscopic_node = track.xpath("rail:trackTopology/rail:trackEnd//rail:macroscopicNode", namespaces=DEFAULT_NAMESPACE)
        e_coords = track.xpath("rail:trackTopology/rail:trackEnd//rail:geoCoord/@coord", namespaces=DEFAULT_NAMESPACE)

        if len(e_connection):
            _CONNECTIONS.append(e_connection[0].attrib)
            topology_node(graph, e_connection, "Connection", "ENDS", track_node, e_coords, _EPSG)
        elif len(e_buffer_stop):
            topology_node(graph, e_buffer_stop, "Buffer Stop", "ENDS", track_node, e_coords, _EPSG)
        elif len(e_open_end):
            topology_node(graph, e_open_end, "Open End", "ENDS", track_node, e_coords, _EPSG)
        elif len(e_macroscopic_node):
            topology_node(graph, e_macroscopic_node, "Macroscopic Node", "ENDS", track_node, e_coords, _EPSG)

        # track elements
        for element in TRACK_ELEMENTS:
            _node = track.xpath("rail:trackElements/rail:" + element['tag'], namespaces=DEFAULT_NAMESPACE)
            if len(_node):
                get_track_elements(graph, _node[0], element['label'], "HAS_TRACK_ELEMENT", track_node, _EPSG)
        # ocs elements
        for element in OCS_ELEMENTS:
            _node = track.xpath("rail:ocsElements/rail:" + element['tag'], namespaces=DEFAULT_NAMESPACE)
            if len(_node):
                get_track_elements(graph, _node[0], element['label'], "HAS_OCS_ELEMENT", track_node, _EPSG)

    for connection in _CONNECTIONS:
        k,v = 'id', connection['ref']
        for i, item in enumerate(_CONNECTIONS):
            if v == item[k]:
                _CONNECTIONS.pop(i)

    for connection in _CONNECTIONS:
        selector = NodeSelector(graph)
        c1 = selector.select("Connection", id=connection["id"]).first()
        c2 = selector.select("Connection", id=connection["ref"]).first()
        if c1 and c2:
            relationship = Relationship(c1, "CONNECTS", c2)
            graph.create(relationship)

    return jsonify({"number_of_tracks": len(tracks)})
