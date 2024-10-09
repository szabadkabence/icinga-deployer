![image](https://github.com/user-attachments/assets/25b5cd45-0672-4ae7-a5c3-6f5c640230ec)

# Icinga Config Deployer

This is a Flask web application designed to generate and deploy configuration files for Icinga, using sensitive data like SSH credentials from a configuration file (`config.ini`). The app allows users to input details such as hostname, IP address, operating system, server type, and more, and generates a configuration file for Icinga hosts.

## Features
- Web interface to input host details.
- Generates Icinga host configuration files.
- Securely transfers configuration files to the Icinga server using SSH.
- Allows the user to restart the Icinga service remotely.
- Dropdowns for OS, Server Type, Main Directory, Subdirectory, and Location are customizable via `config.ini`.

## Project Structure

```
├── app.py                  # Main Flask application file
├── config.ini              # Configuration file storing sensitive data (SSH username, password, and host)
├── templates/
│   └── index.html          # HTML template for the web interface
└── README.md               # This README file
```

## Requirements

- Python 3.x
- Flask
- sshpass (for password-based SSH file transfer)
- Icinga monitoring system

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Install Dependencies

First, ensure you have `Flask` installed. You can install it via `pip`:

```bash
pip install Flask
```

### 3. Create a `config.ini` File

The app requires a `config.ini` file to store sensitive SSH credentials and default options for dropdowns. Create a `config.ini` in the root directory of the project with the following format:

```ini
[ssh]
username = deployer
password = yourpassword
host = icinga-server-hostname-or-ip

[defaults]
operating_system = 
server_type = 
main_directory = 
subdirectory = 
location = 
```

### 4. Run the Application

You can run the application using the following command:

```bash
python app.py
```

By default, the Flask application will be accessible at `http://0.0.0.0:5000`.

### 5. Access the Web Interface

Open your web browser and navigate to:

```
http://<your-server-ip>:5000/
```

You should see the Icinga Config Deployer interface where you can input host details and generate configuration files.

## Usage

1. **Generate Configuration Files**:
   - Fill in the form with the appropriate host details (hostname, IP address, operating system, etc.).
   - Click on "Generate Config" to generate the Icinga configuration file.
   - The configuration file is transferred securely to the Icinga server.

2. **Restart Icinga Service**:
   - After generating the configuration, you can restart the Icinga service by clicking the "Restart Service" button.

## Customizing Dropdown Options

You can modify the dropdown options for **Operating System**, **Server Type**, **Main Directory**, **Subdirectory**, and **Location** via the `config.ini` file. Just list multiple values separated by commas. For example:

```ini
[defaults]
operating_system = Linux, Windows
server_type = Physical, Virtual
main_directory = Physical, Virtual
subdirectory = Network Device, Compute Node, Storage
location = Office1, Server Room1, Server Room2
```
The main_directory and subdirectory options are usable to determine the directory of the host configuration files inside /etc/icinga2/conf.d/hosts directory
## Notes

- **SSH Security**: The app uses `sshpass` to handle password-based SSH connections. It is recommended to switch to SSH key-based authentication for better security.
- Ensure that the `config.ini` file is **not included in version control** by adding it to your `.gitignore` file:
  
  ```
  config.ini
  ```

## Troubleshooting

- **Not Found Error**: If the app shows a "Not Found" error in the browser, ensure that the Flask app is running and that you are accessing the correct URL (`http://<server-ip>:5000/`).
- **Permission Issues**: Make sure that the Flask app and the Icinga server have the necessary permissions to create directories and transfer files.


