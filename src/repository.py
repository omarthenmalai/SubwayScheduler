from src.models import *
from neo4j import GraphDatabase
import warnings


neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "root"))


class MapRepository:

    def create_station(self, station):
        '''
        Creates a station node in the graph based on 'station'
        :param station: SubwayStation object
        :return: result of the transaction
        '''
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._create_station, station)
        return transact

    @staticmethod
    def _create_station(tx, station):
        '''
        Runs a query to create a SubwayStation node in the graph with the values in station
        :param tx: session to run the query
        :param station: SubwayStation object
        :return: result of the query
        '''
        result = tx.run(
            '''
                    CREATE (s:SubwayStation{
                        station_name: $station_name, 
                        entrances: $entrances, 
                        lines: $lines,
                        status: $status
                    }) 
                    RETURN s
            ''',
            station_name=station.station_name,
            entrances=station.entrances,
            lines=station.lines,
            status=station.status
        )
        return result.single()


    def create_connection(self, train_line):
        '''
        Create a connection between two stations for a given line
        :param train_line: TrainLine object
        :return: result of the trasaction
        '''
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._create_connection, train_line)

        return transact

    @staticmethod
    def _create_connection(tx, train_line):
        '''
        Runs a query to create an edge between the start and stop nodes in train_line
        :param tx: session that runs the query
        :param train_line: TrainLine object
        :return: result of the query
        '''
        result = tx.run(
            '''
            MATCH (a:SubwayStation),(b:SubwayStation)
            WHERE a.station_name = $start AND b.station_name = $stop
            AND $line IN a.lines AND $line IN b.lines 
            CREATE (a)-[r:CONNECTS { stations: [$start, $stop], line: $line, cost:1 }]->(b)
            RETURN a, b, r
            ''',
            start=train_line.start,
            stop=train_line.stop,
            line=train_line.line
        )
        temp = result.single()
        # print(temp)
        # print(temp['r']['stations'])
        return temp

    def shortest_path(self, start_station, stop_station):
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._shortest_path, start_station, stop_station)
        return transact

    @staticmethod
    def _shortest_path(tx, start_station, stop_station):
        result = tx.run(
            # '''
            # MATCH (n:SubwayStation), (start:SubwayStation { station_name: $start_name }),
            # (stop:SubwayStation { station_name: $stop_name }),
            # path = shortestPath((start)-[*]-(stop))
            # WHERE ALL(x in nodes(path) WHERE x.status = "Normal")
            # RETURN path
            # ''',
            # start_name=start_station.station_name,
            # stop_name=stop_station.station_name
            '''
            MATCH(start:SubwayStation{station_name: $start_name}),
            (end:SubwayStation{station_name: $stop_name})
            CALL gds.alpha.shortestPath.stream({
                nodeQuery: 'MATCH(n:SubwayStation{status:"Normal"}) RETURN id(n) AS id',
                relationshipQuery:'MATCH(n:SubwayStation)-[r:CONNECTS]-(m:SubwayStation) RETURN id(n) AS source, id(m) AS target, r.cost AS cost',
                startNode: start,
                endNode: end,
                relationshipWeightProperty: 'cost'
            })
            YIELD nodeId, cost
            RETURN gds.util.asNode(nodeId).station_name AS station_name, cost
            ''',


            start_name=start_station.station_name,
            # start_entrances=start_station.entrances,
            stop_name=stop_station.station_name
            # stop_entrances=stop_station.entrances
        )
        return [x for x in result]

    def all_stations(self):
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._all_stations)
        return transact

    @staticmethod
    def _all_stations(tx):
        result = tx.run(
            '''
            MATCH (a:SubwayStation) 
            REtURN a
            '''
        )
        return [x for x in result]

    def stations_by_line(self, line):
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._stations_by_line, line)
        return transact

    @staticmethod
    def _stations_by_line(tx, line):
        result = tx.run(
            '''
            MATCH (a:SubwayStation)
            WHERE $line in a.lines  
            REtURN a
            ''',
            line=line
        )
        return [x for x in result]

    def create_reroute(self, train_line, reroute):
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._create_reroute, train_line, reroute)
        return transact

    @staticmethod
    def _create_reroute(tx, train_line, reroute):
        result = tx.run(
            '''
            MATCH (a:SubwayStation),(b:SubwayStation)
            WHERE a.station_name = $start AND b.station_name = $stop
            AND $line IN a.lines AND $line IN b.lines 
            MERGE (a)-[r:REROUTES { line: $line, cost: 1}]-(b)
            ON CREATE SET r.stations = [$start, $stop], r.reroute = [$reroute]
            ON MATCH SET r.stations = r.stations + [$start, $stop], r.reroute = r.reroute + $reroute 
            RETURN a, b, r
            ''',
            start=train_line.start,
            stop=train_line.stop,
            line=train_line.line,
            reroute=reroute
        )
        return result.single()

    def detach_node(self, station):
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._detach_node, station)
        return transact

    @staticmethod
    def _detach_node(tx, station):
        result = tx.run(
            '''
            MATCH (a:SubwayStation{
                station_name: $station_name
            }), (a)-[r:CONNECTS]-()
            SET a.status = "Out of Order"
            DELETE r
            ''',
            station_name=station.station_name,
        )
        return result.single()

    def get_reroutes(self, station):
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._get_reroutes, station)
        return transact

    @staticmethod
    def _get_reroutes(tx, station):
        result = tx.run(
            '''
            MATCH ()-[r:CONNECTS{reroute: $station_name}]->()
            RETURN r
            ''',
            station_name=station.station_name
        )
        return [x for x in result]

    def remove_reroute(self, reroute):
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._remove_reroute, reroute)
        return transact

    @staticmethod
    def _remove_reroute(tx, reroute):
        result = tx.run(
            '''
            MATCH (s:SubwayStation{station_name: $reroute})
            MATCH ()-[r:CONNECTS{reroute: $reroute}]-()
            SET s.status = "Normal"
            DELETE r
            RETURN s
            ''',
            reroute=reroute
        )
        return [x for x in result]

    def update_station_status(self, station, status):
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._update_station_status, station, status)
        return transact

    @staticmethod
    def _update_station_status(tx, station, status):
        result = tx.run(
            '''
            MATCH (a:SubwayStation{
                station_name: $station_name
            })
            SET a.status = $status
            RETURN a
            ''',
            station_name=station.station_name,
            status=status
        )
        return [x for x in result]

    def all_connections(self, station):
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._all_connections, station)
        return transact

    @staticmethod
    def _all_connections(tx, station):
        result = tx.run(
            '''
            MATCH(a:SubwayStation{station_name: $station_name})-[r]-()
            RETURN r
            ''',
            station_name=station.station_name
        )
        return [x for x in result]

    def test(self, start_station, stop_station):
        with neo4j_driver.session() as s:
            result = s.run(
                '''
                MATCH(start:SubwayStation{station_name: $start_name}), 
                (end:SubwayStation{station_name: $stop_name})
                RETURN start, end
                ''',
                start_name=start_station.station_name,
                # start_entrances=start_station.entrances,
                stop_name=stop_station.station_name
                # stop_entrances=stop_station.entrances
            )
            return [x for x in result]
    #                 (end:SubwayStation{station_name: $stop_name, entrances: $stop_entrances})

    @staticmethod
    def clear_db():
        with neo4j_driver.session() as s:
            s.run('''
                MATCH (n) DETACH DELETE n
            ''')
