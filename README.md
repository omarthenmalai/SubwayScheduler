# SubwayScheduler

Final Project for ECE464-Databases. Maps out the NYC Subway and provides various functionality like finding the fastest path between two stations, delaying stations, and changing a station's status. Uses a `Neo4j` Graph Database, a `MongoDB` database, and `MySQL` database to store the given data and provide the desired functionality.

## Installation

```git clone https://github.com/omarthenmalai/SubwayScheduler.git```

Run `pip install -r requirements.txt` to install all of the required dependencies.

When setting up `Neo4j` ensure that you download the `Graph Data Science Library` 

# Usage

To populate the databases, run 
```python -m src.database```.
The `users` table and `trips` table will be empty

To start the Flask application, run
```python app```.
The app will be launched on `http://localhost:5000`.

To create an `admin` account, run
```python -m src.create_admin -e <email> -p <password>```
