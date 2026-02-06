import subprocess
import os
import time

def convert_file(input_file, output_file, timeout=60):
    """Convert a file using LibreOffice with a timeout and error handling.

    Args:
        input_file (str): The path to the input file.
        output_file (str): The desired path for the output file.
        timeout (int): The timeout value in seconds.

    Raises:
        RuntimeError: If the conversion fails or times out.
    """
    try:
        # Start the LibreOffice process
        process = subprocess.Popen(
            ['libreoffice', '--headless', '--convert-to', os.path.splitext(output_file)[1][1:], input_file, '--outdir', os.path.dirname(output_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        start_time = time.time()

        # Monitor the process for timeout
        while True:
            if process.poll() is not None:  # process has finished
                break
            if time.time() - start_time > timeout:
                process.terminate()  # ensure to terminate the process
                raise RuntimeError("Conversion timed out.")

        # Check for errors
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"Error during conversion: {stderr.decode()}")

    except Exception as e:
        raise RuntimeError(f"An error occurred: {e}")
