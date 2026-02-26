import subprocess

def save_logs(container_name, output_file):
    try:
        print(f"Capturing logs for {container_name}...")
        result = subprocess.run(['docker', 'logs', container_name], capture_output=True, text=True, check=False)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
            f.write("\n\n--- ERRORS ---\n\n")
            f.write(result.stderr)
        print(f"Logs saved to {output_file}")
    except Exception as e:
        print(f"Failed to capture logs for {container_name}: {e}")

if __name__ == "__main__":
    save_logs("hrms-auth", "auth_full_logs.txt")
    save_logs("hrms-db", "db_full_logs.txt")
