import subprocess
import re


def get_host_ip():
    try:
        # Command to run PowerShell command from WSL
        command = 'powershell.exe -Command "ipconfig"'

        # Execute the command
        result = subprocess.run(command, capture_output=True, text=True, shell=True)

        # Extract the IP address using regex
        ip_pattern = re.compile(r'IPv4 Address.*: (\d+\.\d+\.\d+\.\d+)')
        matches = ip_pattern.findall(result.stdout)

        if matches:
            # Assuming the first match is the desired IP address
            return matches[0]
        else:
            print("No IP address found in ipconfig output.")
            return None
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while retrieving the host IP address: {e}")
        return None


def save_ip_to_env(ip_address):
    with open('.env', 'w') as env_file:
        env_file.write(f"HOST_IP={ip_address}\n")


def main():
    host_ip = get_host_ip()
    if host_ip:
        save_ip_to_env(host_ip)
        print(f"Host IP address {host_ip} has been saved to .env file.")
    else:
        print("Failed to retrieve the host machine's IPv4 address")


if __name__ == "__main__":
    main()
