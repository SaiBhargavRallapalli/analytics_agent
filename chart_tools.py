import pandas as pd
import matplotlib.pyplot as plt
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure a directory for charts exists
CHARTS_DIR = "charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

def generate_chart(
    data: list[dict],
    chart_type: str,
    x_column: str,
    y_column: str,
    title: str = "Chart",
    x_label: str = None,
    y_label: str = None,
    filename: str = None
) -> dict:
    """
    Generates a chart (bar or line) from provided data using matplotlib.
    Saves the chart as a PNG file and returns the file path.

    Args:
        data (list[dict]): A list of dictionaries, typically results from SQL queries.
        chart_type (str): The type of chart to generate ('bar' or 'line').
        x_column (str): The name of the column to use for the X-axis.
        y_column (str): The name of the column to use for the Y-axis.
        title (str): The title of the chart.
        x_label (str): Label for the X-axis. Defaults to x_column.
        y_label (str): Label for the Y-axis. Defaults to y_column.
        filename (str): Optional. The name of the file to save the chart.
                        If None, a unique timestamp-based filename will be generated.
    Returns:
        dict: A dictionary containing 'success' status and 'file_path' of the generated chart,
              or an error message.
    """
    if not data:
        return {"success": False, "message": "No data provided to generate chart."}
    
    try:
        df = pd.DataFrame(data)

        # Ensure x_column and y_column exist in the DataFrame
        if x_column not in df.columns or y_column not in df.columns:
            return {"success": False, "message": f"Required columns '{x_column}' or '{y_column}' not found in data."}

        # Convert timestamp strings to datetime objects for proper plotting if x_column is time-based
        if df[x_column].dtype == 'object' and any(isinstance(val, str) and 'T' in val for val in df[x_column]):
            try:
                df[x_column] = pd.to_datetime(df[x_column])
                df = df.sort_values(by=x_column) # Sort by date for line plots
            except Exception as e:
                logger.warning(f"Could not convert x_column '{x_column}' to datetime: {e}")

        plt.figure(figsize=(10, 6))

        if chart_type == 'bar':
            plt.bar(df[x_column], df[y_column])
        elif chart_type == 'line':
            plt.plot(df[x_column], df[y_column], marker='o')
        else:
            return {"success": False, "message": "Unsupported chart type. Choose 'bar' or 'line'."}

        plt.title(title)
        plt.xlabel(x_label if x_label else x_column.replace('_', ' ').title())
        plt.ylabel(y_label if y_label else y_column.replace('_', ' ').title())
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        if filename is None:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chart_{timestamp_str}.png"
        
        file_path = os.path.join(CHARTS_DIR, filename)
        plt.savefig(file_path)
        plt.close() # Close the plot to free up memory

        logger.info(f"Chart saved to {file_path}")
        return {"success": True, "message": "Chart generated successfully.", "file_path": file_path}

    except Exception as e:
        logger.error(f"Error generating chart: {e}")
        return {"success": False, "message": f"Error generating chart: {e}"}