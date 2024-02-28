# EzCnc
EzCnc is a CNC (Command and Control) tool that allows you to control a botnet of clients remotely. It provides a FastAPI-based API for managing clients, executing commands, and receiving client responses. It also includes a database for storing client and command data, as well as plotting functionality for visualizing botnet statistics.

## Project Structure

├── EzCnc

│ ├── cnc.py

│ ├── Database.py

│ ├── Exceptions.py

│ ├── init.py

│ |── Structs.py

├── Example

│ └── main.py

├── images

└── README.md

- `EzCnc`: Contains the main code files for the CNC tool.
  - `cnc.py`: Implements the CNC class that handles the API endpoints and database operations.
  - `Database.py`: Provides the DB class for interacting with the SQLite database.
  - `Exceptions.py`: Defines custom exceptions used in the project.
  - `__init__.py`: Initializes the EzCnc package.
  - `Structs.py`: Contains the Structs.py file defining the data structures used in the project.
- `Example`: Includes an example main.py file demonstrating the usage of the EzCnc API.

## Getting Started

To use EzCnc, follow these steps:

1. Install the required dependencies listed in the `requirements.txt` file.
2. Import the `CNC` class from `EzCnc.cnc` in your project.
3. Initialize an instance of the `CNC` class with the desired configuration parameters.
4. run `uvicorn FILE_NAME:API_VARIABLE_NAME --port PORT`
5. Use the API endpoints provided by the CNC class to manage clients, execute commands, and handle client responses.

For detailed usage examples, refer to the `Example/main.py` file.

## Features

- **Client Management**: Add new clients, identify clients, and track client information such as UUID, name, IP, country, and location.
- **Command Execution**: Send commands to clients and receive responses.
- **File Handling**: Upload and store files sent by clients.
- **Data Visualization**: Generate plots to visualize botnet statistics, such as client countries, response occurrences, and file occurrences.

## Contributors

- [iq-thegoat](https://github.com/iq-thegoat)

## License

This project is licensed under the [MIT License](LICENSE).


## Notes

- EzCnc is an ongoing project in active development that aims to provide a CNC (Command and Control) tool for remotely controlling a botnet of clients. While it is currently functional and usable, it is important to note that it is not recommended for any serious use at this stage.
