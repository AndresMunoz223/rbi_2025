import serial
import pandas as pd
from datetime import datetime

# Configuration
SERIAL_PORT = '/dev/ttyUSB0'  # Change to your port
BAUD_RATE = 115200
CSV_FILENAME = 'R2_data_15.csv'
SAVE_INTERVAL = 10  # Save every 10 records

def main():
    # Initialize DataFrame with columns matching your data
    columns = ['timestamp', 'pos1', 'pos2', 'torque1', 'torque2', 'time_ms']
    df = pd.DataFrame(columns=columns)
    
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Reading from {SERIAL_PORT} at {BAUD_RATE} baud...")
            print("Press Ctrl+C to stop")
            
            while True:
                try:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        # Split the line by | character
                        parts = line.split('|')
                        if len(parts) == 5:
                            # Create data dictionary
                            data = {
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                                'pos1': float(parts[0]),
                                'pos2': float(parts[1]),
                                'torque1': float(parts[2]),
                                'torque2': float(parts[3]),
                                'time_ms': float(parts[4])
                            }
                            
                            # Append to DataFrame
                            df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
                            
                            # Print the received data
                            print(f"Received: {data}")
                            
                            # Periodically save to CSV
                            if len(df) % SAVE_INTERVAL == 0:
                                df.to_csv(CSV_FILENAME, index=False)
                                print(f"Saved {len(df)} records to {CSV_FILENAME}")
                
                except ValueError as e:
                    print(f"Error parsing line: {line} - {e}")
                except UnicodeDecodeError:
                    print("Warning: Could not decode line")
                except Exception as e:
                    print(f"Error: {e}")
    
    except serial.SerialException as e:
        print(f"Serial connection error: {e}")
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    finally:
        # Save remaining data before exiting
        if not df.empty:
            df.to_csv(CSV_FILENAME, index=False)
            print(f"Final save: {len(df)} records written to {CSV_FILENAME}")

if __name__ == "__main__":
    main()