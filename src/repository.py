from neo4j import GraphDatabase


neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "root"))


class MapRepository:

    def create_station(self, station):
        """
        Creates a station node in the graph based on 'station'
        :param station: SubwayStation object
        :return: result of the transaction
        """
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._create_station, station)
        return transact

    @staticmethod
    def _create_station(tx, station):
        """
        Runs a query to create a SubwayStation node in the graph with the values in station
        :param tx: session to run the query
        :param station: SubwayStation object
        :return: result of the query
        """
        result = tx.run(
            '''
                    MERGE (s:SubwayStation{
                        station_name: $station_name,
                        borough: $borough, 
                        entrances: $entrances, 
                        lines: $lines,
                        status: $status
                    }) 
                    RETURN s
            ''',
            station_name=station.station_name,
            borough=station.borough,
            entrances=station.entrances,
            lines=station.lines,
            status=station.status
        )
        return result.single()

    def get_station_by_station_name(self, station_name):
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._get_station_by_station_name, station_name)

        return transact

    @staticmethod
    def _get_station_by_station_name(tx, station_name):
        result = tx.run(
            '''
            MATCH (s:SubwayStation{station_name:$station_name})
            RETURN s
            ''',
            station_name=station_name
        )
        return [x for x in result]

    def create_connection(self, train_line):
        """
        Create a connection between two stations for a given line
        :param train_line: TrainLine object
        :return: result of the trasaction
        """
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._create_connection, train_line)

        return transact

    @staticmethod
    def _create_connection(tx, train_line):
        """
        Runs a query to create an edge between the start and stop nodes in train_line
        :param tx: session that runs the query
        :param train_line: TrainLine object
        :return: result of the query
        """
        result = tx.run(
            '''
            MATCH (a:SubwayStation),
            (b:SubwayStation)
            WHERE $line IN a.lines AND $line IN b.lines
            AND a.station_name=$start_name AND a.borough=$start_borough
            AND b.station_name=$stop_name AND b.borough=$stop_borough
            AND $start_entrance in a.entrances AND $stop_entrance in b.entrances
            CREATE (a)-[r:CONNECTS { line: $line, cost:1 }]->(b)
            RETURN a, b, r
            ''',
            start_name=train_line.start.station_name,
            start_borough=train_line.start.borough,
            start_entrance=train_line.start.entrances,
            stop_name=train_line.stop.station_name,
            stop_borough=train_line.stop.borough,
            stop_entrance=train_line.stop.entrances,
            line=train_line.line
        )
        temp = result.single()
        return temp

    def get_connections_between_stations(self, station_1, station_2):
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._get_connections_between_stations, station_1, station_2)
        return transact

    @staticmethod
    def _get_connections_between_stations(tx, station_1, station_2):
        result = tx.run(
            '''
            MATCH (a:SubwayStation)-[r]-(b:SubwayStation)
            WHERE a.station_name=$s1_name AND a.borough=$s1_borough AND a.entrances=$s1_entrances
            AND b.station_name=$s2_name AND b.borough=$s2_borough AND b.entrances=$s2_entrances
            RETURN r.line as line
            ''',
            s1_name=station_1.station_name,
            s1_borough=station_1.borough,
            s1_entrances=station_1.entrances,
            s2_name=station_2.station_name,
            s2_borough=station_2.borough,
            s2_entrances=station_2.entrances
        )
        return [x['line'] for x in result]

    def shortest_path(self, start_station, stop_station):
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._shortest_path, start_station, stop_station)
        return transact

    @staticmethod
    def _shortest_path(tx, start_station, stop_station):
        result = tx.run(
            '''
            MATCH (start:SubwayStation{station_name: $start_name}), (end:SubwayStation{station_name:$stop_name})
            CALL gds.alpha.kShortestPaths.stream({
                nodeQuery: 'MATCH(n:SubwayStation) RETURN id(n) AS id',
                relationshipQuery:'MATCH(n:SubwayStation)-[r]-(m:SubwayStation) RETURN id(n) AS source, id(m) AS target,
                                r.cost as cost',
                startNode: start,
                endNode: end,
                k: 1,
                relationshipWeightProperty: 'cost',
                path: true
            })
            YIELD path
            RETURN path
            ''',
            start_name=start_station.station_name,
            stop_name=stop_station.station_name
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
            CREATE (a)-[r:REROUTES{line:$line, cost:1, reroute:$reroute}]->(b)
            RETURN a, b, r
            ''',
            start=train_line.start.station_name,
            stop=train_line.stop.station_name,
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
                station_name: $station_name,
                borough: $borough,
                entrances: $entrances
            }), (a)-[r]-()
            SET a.status = "Out of Order"
            DELETE r
            ''',
            station_name=station.station_name,
            borough=station.borough,
            entrances=station.entrances
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
            MATCH ()-[r:REROUTES]->()
            WHERE $station_name in r.reroute
            RETURN 
                startNode(r) as start, 
                endNode(r) as end, 
                r.line AS line, 
                r.reroute as reroute
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
            MATCH ()-[r:REROUTES]->()
            WHERE $reroute in r.reroute
            SET s.status = "Normal"
            DELETE r
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
            MATCH (a:SubwayStation{station_name: $station_name}), (b:SubwayStation)
            MATCH (a)-[r]-(b)
            RETURN 
                startNode(r) as start, 
                endNode(r) as end, 
                r.line AS line, 
                r.reroute as reroute
            ''',
            station_name=station.station_name
        )
        return [x for x in result]

    @staticmethod
    def clear_db():
        with neo4j_driver.session() as s:
            s.run('''
                MATCH (n) DETACH DELETE n
            ''')
