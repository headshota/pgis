from app import db
from sqlalchemy.sql import text
from sqlalchemy.dialects.postgresql import JSON
from geoalchemy2.shape import to_shape
from app.models.powerline import Powerline
from shapely import wkb

class Relation(db.Model):
    __tablename__ = 'power_relations'
    id            = db.Column(db.Integer, primary_key = True)
    properties    = db.Column(JSON)


    # Get the relations with their points and ways that fall in the
    # given bounds
    def with_points_and_lines_in_bounds(bounds):
        # First, get points without aggregation
        # Seconds, get powerlines with aggregation
        # Third, merge the relations from powerlines with points.
        #       This way we will have a dictionary with each relation_id as
        #        key and its properties, points and powerlines as a part of
        #        them.
        #         e.g: {65: {id: 65, points: [], powerlines: [], properties: []}}

        point_rows = Relation.relations_and_points_in_bounds(
            bounds,
            False
        )

        pl_relations = Relation.relations_and_powerlines_in_bounds(
            bounds,
            True
        )

        relations = pl_relations

        for point_row in point_rows:
            relation_id = point_row['rel_id']

            if relation_id not in relations:
                relations[relation_id] = {
                    'id': relation_id,
                    'properties': point_row['rel_prop'],
                    'points': [],
                    'powerlines': []
                }

            relations[relation_id]['points'].append({
                'id': point_row['p_id'],
                'latlng': [point_row['p_x'], point_row['p_y']]
            })

        return relations


    # Get the relations and their points that fall in the given bounds.
    #   aggregated: to choose whether to return the results grouped by
    #               relation or return the direct rows from sql query.
    def relations_and_powerlines_in_bounds(bounds, aggregated=None):
        if aggregated is None:
            aggregated = True

        relation_and_powerline_query = text("""
            SELECT r.id AS rel_id, p.id AS pl_id, ST_AsBinary(p.geom) AS pl_geom,
                   r.properties AS rel_prop
                FROM powerline p
            JOIN power_relation_members m
                ON p.id = m.member_id
            JOIN power_relations r
                ON r.id = m.power_relation_id
            WHERE ST_Intersects(
                ST_MakeEnvelope(:bounds_1, :bounds_2, :bounds_3, :bounds_4),
                p.geom
            )
         """)

        relation_and_powerlines = db.engine.execute(
            relation_and_powerline_query,
            bounds_1 = bounds[1],
            bounds_2 = bounds[0],
            bounds_3 = bounds[3],
            bounds_4 = bounds[2]
        )

        if aggregated:
            relations = {}
            for row in relation_and_powerlines:
                r_id = row['rel_id']

                if r_id not in relations:
                    relations[r_id] = {
                        'id': r_id,
                        'properties': row['rel_prop'],
                        'points': [],
                        'powerlines': []
                    }

                relations[r_id]['powerlines'].append({
                    'id': row['pl_id'],
                    'latlngs': list(wkb.loads(bytes(row['pl_geom'])).coords)
                })

            return relations
        else:
            return relations_and_powerlines

    # Get the relations and their points that fall in the given bounds.
    #   aggregated: to choose whether to return the results grouped by
    #               relation or return the direct rows from sql query.
    def relations_and_points_in_bounds(bounds, aggregated=None):
        if aggregated is None:
            aggregated = True

        relation_and_points_query = text("""
            SELECT r.id AS rel_id, p.id AS p_id, ST_X(p.geom) AS p_x,
                   ST_Y(p.geom) AS p_y, r.properties AS rel_prop
                FROM point p
            JOIN power_relation_members m
                ON p.id = m.member_id
            JOIN power_relations r
                ON r.id = m.power_relation_id
            WHERE ST_Contains(
                ST_MakeEnvelope(:bounds_1, :bounds_2, :bounds_3, :bounds_4),
                p.geom
            )
         """)

        relation_and_points = db.engine.execute(
            relation_and_points_query,
            bounds_1 = bounds[1],
            bounds_2 = bounds[0],
            bounds_3 = bounds[3],
            bounds_4 = bounds[2]
        )

        if aggregated:
            relations = {}
            for row in relation_and_points:
                r_id = row['rel_id']

                if r_id not in relations:
                    relations[r_id] = {
                        'id': r_id,
                        'properties': row['rel_prop'],
                        'points': [],
                        'powerlines': []
                    }

                relations[r_id]['points'].append({
                    'id': row['p_id'],
                    'latlng': [row['p_x'], row['p_y']]
                })

            return relations

        else:
            return relation_and_points

    def relations_and_points_query():
        # Query to get the points and nodes that are part of a relation that
        # has points that are in the bounds
        """
            SELECT DISTINCT p2.id, r.id FROM point p
            JOIN power_relation_members m
                ON p.id = m.member_id
            JOIN power_relation_members m2
                ON m2.power_relation_id = m.power_relation_id
            JOIN point p2
                ON p2.id = m2.member_id
            JOIN power_relations r
                ON r.id = m.power_relation_id
            WHERE ST_Contains(
                ST_MakeEnvelope(:bounds_1, :bounds_2, :bounds_3, :bounds_4),
                p.geom
            )
         """
