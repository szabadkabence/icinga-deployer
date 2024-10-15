import os
import subprocess
from flask import Flask, render_template, request, jsonify
import configparser

app = Flask(__name__)

# Get the directory where app.py is located
basedir = os.path.abspath(os.path.dirname(__file__))

# Specify the full path to config.ini
config_path = os.path.join(basedir, 'config.ini')

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read(config_path)

# Fetch sensitive information from config
ssh_username = config['ssh']['username']
ssh_password = config['ssh']['password']
ssh_host = config['ssh']['host']

# Fetch default form values from config.ini (as lists)
default_os_list = config['defaults']['operating_system'].split(',')
default_server_type_list = config['defaults']['server_type'].split(',')
default_main_dir_list = config['defaults']['main_directory'].split(',')
default_sub_dir_list = config['defaults']['subdirectory'].split(',')
default_location_list = config['defaults']['location'].split(',')

# Define the root route
@app.route('/')
def index():
    return render_template(
        'index.html',
        default_os_list=default_os_list,
        default_server_type_list=default_server_type_list,
        default_main_dir_list=default_main_dir_list,
        default_sub_dir_list=default_sub_dir_list,
        default_location_list=default_location_list
    )

# Function to create the local config file
def create_local_config_file(hostname, ip_address, os_type, server_type, location, software_raid, hardware_raid, main_dir, sub_dir):
    config_content = f"""
object Host "{hostname}" {{
  import "generic-host"
  address = "{ip_address}"
  vars.os = "{os_type}"
  vars.server_type = "{server_type}"
  vars.location = "{location}"
  vars.software_raid = {software_raid}
  vars.hardware_raid = {hardware_raid}
}}
"""
    # Directory structure
    local_dir = f"/var/www/config_files/{main_dir}/{sub_dir}"
    os.makedirs(local_dir, exist_ok=True)
    config_path = f"{local_dir}/{hostname}.conf"

    # Write the config file locally
    with open(config_path, 'w') as config_file:
        config_file.write(config_content)

    return config_path

# Function to SCP the file to the Icinga server and create directories
def transfer_file_to_icinga(local_config_path, hostname, ip_address, main_dir, sub_dir):

    remote_dir = f"/etc/icinga2/conf.d/hosts/{main_dir}/{sub_dir}"
    remote_tmp_path = f"/tmp/{hostname}.conf"
    remote_final_path = f"{remote_dir}/{hostname}.conf"

    # Step 1: Create the remote directory structure
    ssh_command = f'sshpass -p "{ssh_password}" ssh -o StrictHostKeyChecking=no {ssh_username}@{ssh_host} "echo \'{ssh_password}\' | sudo -S mkdir -p {remote_dir}"'

    try:
        subprocess.run(ssh_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        return False, f"Error creating remote directory: {e}"

    # Step 2: SCP to /tmp/ on the remote server
    scp_command = f'sshpass -p "{ssh_password}" scp {local_config_path} {ssh_username}@{ssh_host}:{remote_tmp_path}'

    try:
        subprocess.run(scp_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        return False, f"Error transferring config file to /tmp: {e}"

    # Step 3: Move the file to the final destination with sudo
    move_command = f'sshpass -p "{ssh_password}" ssh -o StrictHostKeyChecking=no {ssh_username}@{ssh_host} "echo \'{ssh_password}\' | sudo -S mv {remote_tmp_path} {remote_final_path}"'

    try:
        subprocess.run(move_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        return False, f"Error moving config file to final destination: {e}"

    # Step 4: Add configuration to zones.conf via temporary file
    zones_conf_entry = f"""
object Endpoint "{hostname}" {{
  host = "{ip_address}"
}}

object Zone "{hostname}" {{
  endpoints = [ "{hostname}" ]
  parent = "icinga"
}}
"""
    # Write the zones.conf entry to a temporary file locally
    temp_zones_conf_path = f"/var/www/config_files/{hostname}_zones.conf"
    with open(temp_zones_conf_path, 'w') as zones_conf_file:
        zones_conf_file.write(zones_conf_entry)

    # Upload the temporary zones.conf entry to the Icinga server
    scp_zones_command = f'sshpass -p "{ssh_password}" scp {temp_zones_conf_path} {ssh_username}@{ssh_host}:/tmp/{hostname}_zones.conf'

    try:
        subprocess.run(scp_zones_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        return False, f"Error transferring zones.conf entry to remote server: {e}"

    # Append the temporary zones file to the actual zones.conf on the Icinga server using sudo
    append_zones_command = f'sshpass -p "{ssh_password}" ssh -o StrictHostKeyChecking=no {ssh_username}@{ssh_host} "echo \'{ssh_password}\' | sudo -S bash -c \'cat /tmp/{hostname}_zones.conf >> /etc/icinga2/zones.conf\'"'

    try:
        subprocess.run(append_zones_command, shell=True, check=True)
        return True, f"Config file successfully transferred and zones.conf updated on Icinga server"
    except subprocess.CalledProcessError as e:
        return False, f"Error appending zones.conf entry: {e}"

    # Return after successfully updating zones.conf
    return True, "Config file successfully transferred and zones.conf updated."

# Function to restart the Icinga service
def restart_icinga_service():
    restart_command = f'sshpass -p "{ssh_password}" ssh -o StrictHostKeyChecking=no {ssh_username}@{ssh_host} "echo \'{ssh_password}\' | sudo -S systemctl restart icinga2.service"'
    
    try:
        subprocess.run(restart_command, shell=True, check=True)
        return True, "Icinga2 service successfully restarted."
    except subprocess.CalledProcessError as e:
        return False, f"Error restarting Icinga2 service: {e}"

@app.route('/restart_service', methods=['POST'])
def restart_service():
    try:
        success, message = restart_icinga_service()
        if success:
            return jsonify({'status': 'success', 'message': message})
        else:
            return jsonify({'status': 'error', 'message': message}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"An error occurred: {str(e)}"}), 500


@app.route('/generate', methods=['POST'])
def generate():
    try:
        hostname = request.form.get('hostname')
        ip_address = request.form.get('ip_address')

        # Handle Operating System with custom option
        os_type = request.form.get('os_type')
        if os_type == "custom":
            os_type = request.form.get('custom_os_type')

        # Handle Server Type with custom option
        server_type = request.form.get('server_type')
        if server_type == "custom":
            server_type = request.form.get('custom_server_type')

        main_dir = request.form.get('main_dir')

        # Handle subdirectory selection or custom subdirectory
        sub_dir = request.form.get('sub_dir')
        if sub_dir == "custom":
            sub_dir = request.form.get('custom_sub_dir')

        # Handle location selection or custom location
        location = request.form.get('location')
        if location == "custom":
            location = request.form.get('custom_location')

        # Check Software RAID and Hardware RAID
        software_raid = 'true' if request.form.get('software_raid') else 'false'
        hardware_raid = 'true' if request.form.get('hardware_raid') else 'false'

        # Create the local config file
        local_config_path = create_local_config_file(
            hostname, ip_address, os_type, server_type, location, software_raid, hardware_raid, main_dir, sub_dir
        )

        # Transfer the config file to the Icinga server and update zones.conf
        success, result_message = transfer_file_to_icinga(local_config_path, hostname, ip_address, main_dir, sub_dir)

        if success:
            return jsonify({'status': 'success', 'message': result_message})
        else:
            return jsonify({'status': 'error', 'message': result_message}), 500

    except Exception as e:
        return jsonify({'status': 'error', 'message': f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
