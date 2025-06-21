"""
MITO Engine - Visualization Manager
Complete data visualization and reporting system
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from pathlib import Path
import base64
from io import BytesIO
import uuid

class Chart:
    """Chart data structure"""
    
    def __init__(self, chart_id: str, title: str, chart_type: str, data: Dict[str, Any],
                 config: Dict[str, Any] = None):
        self.chart_id = chart_id
        self.title = title
        self.chart_type = chart_type
        self.data = data
        self.config = config or {}
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

class Dashboard:
    """Dashboard data structure"""
    
    def __init__(self, dashboard_id: str, name: str, description: str = ""):
        self.dashboard_id = dashboard_id
        self.name = name
        self.description = description
        self.charts = []
        self.layout = {}
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

class VisualizationManager:
    """Complete data visualization and reporting system"""
    
    def __init__(self, db_path: str = "visualizations.db"):
        self.db_path = db_path
        self.charts = {}
        self.dashboards = {}
        
        # Set matplotlib style
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = (10, 6)
        
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize visualization database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Charts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS charts (
                chart_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                chart_type TEXT NOT NULL,
                data TEXT NOT NULL,
                config TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Dashboards table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dashboards (
                dashboard_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                layout TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Dashboard charts relationship
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dashboard_charts (
                dashboard_id TEXT,
                chart_id TEXT,
                position INTEGER,
                FOREIGN KEY (dashboard_id) REFERENCES dashboards (dashboard_id),
                FOREIGN KEY (chart_id) REFERENCES charts (chart_id)
            )
        ''')
        
        # Reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                report_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                data_source TEXT,
                config TEXT,
                generated_at TEXT NOT NULL,
                file_path TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_chart(self, title: str, chart_type: str, data: Dict[str, Any],
                    config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create new chart"""
        try:
            chart_id = str(uuid.uuid4())
            chart = Chart(chart_id, title, chart_type, data, config)
            
            # Validate chart type
            supported_types = ['line', 'bar', 'pie', 'scatter', 'histogram', 'heatmap', 'box']
            if chart_type not in supported_types:
                return {"success": False, "error": f"Unsupported chart type: {chart_type}"}
            
            # Store in memory and database
            self.charts[chart_id] = chart
            self._store_chart(chart)
            
            return {
                "success": True,
                "chart_id": chart_id,
                "title": title,
                "type": chart_type,
                "message": "Chart created successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_chart_image(self, chart_id: str, format: str = "png", 
                           width: int = 10, height: int = 6) -> Dict[str, Any]:
        """Generate chart image"""
        try:
            if chart_id not in self.charts:
                chart = self._load_chart(chart_id)
                if not chart:
                    return {"success": False, "error": "Chart not found"}
                self.charts[chart_id] = chart
            
            chart = self.charts[chart_id]
            
            # Create figure
            fig, ax = plt.subplots(figsize=(width, height))
            
            # Generate chart based on type
            if chart.chart_type == "line":
                self._generate_line_chart(ax, chart)
            elif chart.chart_type == "bar":
                self._generate_bar_chart(ax, chart)
            elif chart.chart_type == "pie":
                self._generate_pie_chart(ax, chart)
            elif chart.chart_type == "scatter":
                self._generate_scatter_chart(ax, chart)
            elif chart.chart_type == "histogram":
                self._generate_histogram_chart(ax, chart)
            elif chart.chart_type == "heatmap":
                self._generate_heatmap_chart(ax, chart)
            elif chart.chart_type == "box":
                self._generate_box_chart(ax, chart)
            else:
                plt.close(fig)
                return {"success": False, "error": f"Unsupported chart type: {chart.chart_type}"}
            
            # Apply styling
            ax.set_title(chart.title, fontsize=16, fontweight='bold')
            
            # Apply custom config
            if chart.config:
                if 'xlabel' in chart.config:
                    ax.set_xlabel(chart.config['xlabel'])
                if 'ylabel' in chart.config:
                    ax.set_ylabel(chart.config['ylabel'])
                if 'grid' in chart.config and chart.config['grid']:
                    ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save to memory buffer
            buffer = BytesIO()
            plt.savefig(buffer, format=format, dpi=300, bbox_inches='tight')
            buffer.seek(0)
            
            # Convert to base64 for web display
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            plt.close(fig)
            
            return {
                "success": True,
                "chart_id": chart_id,
                "format": format,
                "image_data": image_base64,
                "width": width,
                "height": height
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_line_chart(self, ax, chart: Chart):
        """Generate line chart"""
        data = chart.data
        
        if 'x' in data and 'y' in data:
            x_data = data['x']
            y_data = data['y']
            
            # Handle multiple series
            if isinstance(y_data[0], list):
                for i, series in enumerate(y_data):
                    label = data.get('labels', [f'Series {i+1}'])[i] if 'labels' in data else f'Series {i+1}'
                    ax.plot(x_data, series, marker='o', label=label)
                ax.legend()
            else:
                ax.plot(x_data, y_data, marker='o', linewidth=2, markersize=4)
        
        elif 'series' in data:
            for series_name, series_data in data['series'].items():
                ax.plot(series_data['x'], series_data['y'], marker='o', label=series_name)
            ax.legend()
    
    def _generate_bar_chart(self, ax, chart: Chart):
        """Generate bar chart"""
        data = chart.data
        
        if 'categories' in data and 'values' in data:
            categories = data['categories']
            values = data['values']
            
            bars = ax.bar(categories, values, alpha=0.8)
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'{value}', ha='center', va='bottom')
            
            # Rotate x-axis labels if needed
            if len(max(categories, key=len)) > 10:
                plt.xticks(rotation=45, ha='right')
    
    def _generate_pie_chart(self, ax, chart: Chart):
        """Generate pie chart"""
        data = chart.data
        
        if 'labels' in data and 'values' in data:
            labels = data['labels']
            values = data['values']
            
            # Create pie chart with percentage labels
            wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
                                            startangle=90, textprops={'fontsize': 10})
            
            # Equal aspect ratio ensures pie is drawn as circle
            ax.axis('equal')
    
    def _generate_scatter_chart(self, ax, chart: Chart):
        """Generate scatter chart"""
        data = chart.data
        
        if 'x' in data and 'y' in data:
            x_data = data['x']
            y_data = data['y']
            
            # Optional: color and size data
            colors = data.get('colors', None)
            sizes = data.get('sizes', 50)
            
            scatter = ax.scatter(x_data, y_data, c=colors, s=sizes, alpha=0.7)
            
            # Add colorbar if colors are provided
            if colors:
                plt.colorbar(scatter, ax=ax)
    
    def _generate_histogram_chart(self, ax, chart: Chart):
        """Generate histogram chart"""
        data = chart.data
        
        if 'values' in data:
            values = data['values']
            bins = data.get('bins', 30)
            
            ax.hist(values, bins=bins, alpha=0.7, edgecolor='black')
    
    def _generate_heatmap_chart(self, ax, chart: Chart):
        """Generate heatmap chart"""
        data = chart.data
        
        if 'matrix' in data:
            matrix = np.array(data['matrix'])
            
            # Create heatmap
            im = ax.imshow(matrix, cmap='viridis', aspect='auto')
            
            # Add colorbar
            plt.colorbar(im, ax=ax)
            
            # Add labels if provided
            if 'x_labels' in data:
                ax.set_xticks(range(len(data['x_labels'])))
                ax.set_xticklabels(data['x_labels'])
            
            if 'y_labels' in data:
                ax.set_yticks(range(len(data['y_labels'])))
                ax.set_yticklabels(data['y_labels'])
    
    def _generate_box_chart(self, ax, chart: Chart):
        """Generate box plot chart"""
        data = chart.data
        
        if 'datasets' in data:
            datasets = data['datasets']
            labels = data.get('labels', [f'Dataset {i+1}' for i in range(len(datasets))])
            
            box_plot = ax.boxplot(datasets, labels=labels, patch_artist=True)
            
            # Color the boxes
            colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow', 'lightpink']
            for patch, color in zip(box_plot['boxes'], colors):
                patch.set_facecolor(color)
    
    def create_dashboard(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create new dashboard"""
        try:
            dashboard_id = str(uuid.uuid4())
            dashboard = Dashboard(dashboard_id, name, description)
            
            self.dashboards[dashboard_id] = dashboard
            self._store_dashboard(dashboard)
            
            return {
                "success": True,
                "dashboard_id": dashboard_id,
                "name": name,
                "message": "Dashboard created successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_chart_to_dashboard(self, dashboard_id: str, chart_id: str, position: int = None) -> Dict[str, Any]:
        """Add chart to dashboard"""
        try:
            if dashboard_id not in self.dashboards:
                dashboard = self._load_dashboard(dashboard_id)
                if not dashboard:
                    return {"success": False, "error": "Dashboard not found"}
                self.dashboards[dashboard_id] = dashboard
            
            if chart_id not in self.charts:
                chart = self._load_chart(chart_id)
                if not chart:
                    return {"success": False, "error": "Chart not found"}
                self.charts[chart_id] = chart
            
            dashboard = self.dashboards[dashboard_id]
            
            if position is None:
                position = len(dashboard.charts)
            
            if chart_id not in dashboard.charts:
                dashboard.charts.append(chart_id)
                dashboard.updated_at = datetime.now().isoformat()
                
                # Update database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO dashboard_charts (dashboard_id, chart_id, position)
                    VALUES (?, ?, ?)
                ''', (dashboard_id, chart_id, position))
                
                cursor.execute('''
                    UPDATE dashboards SET updated_at = ? WHERE dashboard_id = ?
                ''', (dashboard.updated_at, dashboard_id))
                
                conn.commit()
                conn.close()
            
            return {
                "success": True,
                "message": "Chart added to dashboard successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_dashboard_html(self, dashboard_id: str) -> Dict[str, Any]:
        """Generate HTML dashboard"""
        try:
            if dashboard_id not in self.dashboards:
                dashboard = self._load_dashboard(dashboard_id)
                if not dashboard:
                    return {"success": False, "error": "Dashboard not found"}
                self.dashboards[dashboard_id] = dashboard
            
            dashboard = self.dashboards[dashboard_id]
            
            # Generate HTML structure
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{dashboard.name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .dashboard-header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .dashboard-title {{
            font-size: 2.5em;
            color: #333;
            margin: 0;
        }}
        .dashboard-description {{
            color: #666;
            margin-top: 10px;
        }}
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
        }}
        .chart-container {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chart-title {{
            font-size: 1.3em;
            color: #333;
            margin-bottom: 15px;
            text-align: center;
        }}
        .chart-image {{
            width: 100%;
            height: auto;
            border-radius: 4px;
        }}
        .no-charts {{
            text-align: center;
            color: #666;
            font-style: italic;
            margin-top: 50px;
        }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <h1 class="dashboard-title">{dashboard.name}</h1>
        <p class="dashboard-description">{dashboard.description}</p>
    </div>
    
    <div class="chart-grid">
"""
            
            if not dashboard.charts:
                html_content += """
        <div class="no-charts">
            <p>No charts added to this dashboard yet.</p>
        </div>
"""
            else:
                # Generate charts
                for chart_id in dashboard.charts:
                    chart_result = self.generate_chart_image(chart_id)
                    if chart_result["success"]:
                        chart = self.charts[chart_id]
                        html_content += f"""
        <div class="chart-container">
            <h3 class="chart-title">{chart.title}</h3>
            <img src="data:image/png;base64,{chart_result['image_data']}" alt="{chart.title}" class="chart-image">
        </div>
"""
            
            html_content += """
    </div>
</body>
</html>
"""
            
            # Save HTML file
            filename = f"dashboard_{dashboard_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                "success": True,
                "dashboard_id": dashboard_id,
                "filename": filename,
                "html_content": html_content
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_analytics_report(self, data_source: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate analytics report"""
        try:
            report_id = str(uuid.uuid4())
            
            # Sample analytics data (would normally come from actual data source)
            sample_data = self._generate_sample_analytics_data()
            
            # Create charts for the report
            charts = []
            
            # Traffic overview chart
            traffic_chart = self.create_chart(
                "Website Traffic Overview",
                "line",
                {
                    "x": sample_data["dates"],
                    "y": sample_data["visitors"],
                    "labels": ["Daily Visitors"]
                },
                {"xlabel": "Date", "ylabel": "Visitors", "grid": True}
            )
            
            if traffic_chart["success"]:
                charts.append(traffic_chart["chart_id"])
            
            # Page views by category
            category_chart = self.create_chart(
                "Page Views by Category",
                "bar",
                {
                    "categories": sample_data["categories"],
                    "values": sample_data["page_views"]
                },
                {"xlabel": "Category", "ylabel": "Page Views"}
            )
            
            if category_chart["success"]:
                charts.append(category_chart["chart_id"])
            
            # Browser distribution
            browser_chart = self.create_chart(
                "Browser Distribution",
                "pie",
                {
                    "labels": sample_data["browsers"],
                    "values": sample_data["browser_counts"]
                }
            )
            
            if browser_chart["success"]:
                charts.append(browser_chart["chart_id"])
            
            # Create dashboard for the report
            dashboard_result = self.create_dashboard(
                f"Analytics Report - {datetime.now().strftime('%Y-%m-%d')}",
                f"Comprehensive analytics report generated from {data_source}"
            )
            
            if dashboard_result["success"]:
                dashboard_id = dashboard_result["dashboard_id"]
                
                # Add charts to dashboard
                for chart_id in charts:
                    self.add_chart_to_dashboard(dashboard_id, chart_id)
                
                # Generate HTML report
                html_result = self.generate_dashboard_html(dashboard_id)
                
                # Store report metadata
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO reports (report_id, name, description, data_source, config, generated_at, file_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (report_id, f"Analytics Report {datetime.now().strftime('%Y-%m-%d')}", 
                      "Automated analytics report", data_source, json.dumps(config or {}),
                      datetime.now().isoformat(), html_result.get("filename")))
                
                conn.commit()
                conn.close()
                
                return {
                    "success": True,
                    "report_id": report_id,
                    "dashboard_id": dashboard_id,
                    "charts": charts,
                    "html_file": html_result.get("filename"),
                    "message": "Analytics report generated successfully"
                }
            
            return {"success": False, "error": "Failed to create dashboard for report"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_sample_analytics_data(self) -> Dict[str, Any]:
        """Generate sample analytics data"""
        # Generate dates for last 30 days
        end_date = datetime.now()
        dates = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(29, -1, -1)]
        
        # Generate sample data
        np.random.seed(42)  # For reproducible results
        
        return {
            "dates": dates,
            "visitors": np.random.randint(100, 1000, 30).tolist(),
            "categories": ["Home", "Products", "About", "Contact", "Blog"],
            "page_views": np.random.randint(50, 500, 5).tolist(),
            "browsers": ["Chrome", "Firefox", "Safari", "Edge", "Other"],
            "browser_counts": np.random.randint(10, 100, 5).tolist()
        }
    
    def list_charts(self) -> List[Dict[str, Any]]:
        """List all charts"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT chart_id, title, chart_type, created_at, updated_at
                FROM charts ORDER BY created_at DESC
            ''')
            
            charts = []
            for row in cursor.fetchall():
                charts.append({
                    "chart_id": row[0],
                    "title": row[1],
                    "type": row[2],
                    "created_at": row[3],
                    "updated_at": row[4]
                })
            
            conn.close()
            return charts
            
        except Exception:
            return []
    
    def list_dashboards(self) -> List[Dict[str, Any]]:
        """List all dashboards"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT dashboard_id, name, description, created_at, updated_at
                FROM dashboards ORDER BY created_at DESC
            ''')
            
            dashboards = []
            for row in cursor.fetchall():
                # Count charts in dashboard
                cursor.execute('''
                    SELECT COUNT(*) FROM dashboard_charts WHERE dashboard_id = ?
                ''', (row[0],))
                chart_count = cursor.fetchone()[0]
                
                dashboards.append({
                    "dashboard_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "chart_count": chart_count,
                    "created_at": row[3],
                    "updated_at": row[4]
                })
            
            conn.close()
            return dashboards
            
        except Exception:
            return []
    
    def _store_chart(self, chart: Chart):
        """Store chart in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO charts 
                (chart_id, title, chart_type, data, config, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (chart.chart_id, chart.title, chart.chart_type, 
                  json.dumps(chart.data), json.dumps(chart.config),
                  chart.created_at, chart.updated_at))
            
            conn.commit()
            conn.close()
            
        except Exception:
            pass
    
    def _store_dashboard(self, dashboard: Dashboard):
        """Store dashboard in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO dashboards 
                (dashboard_id, name, description, layout, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (dashboard.dashboard_id, dashboard.name, dashboard.description,
                  json.dumps(dashboard.layout), dashboard.created_at, dashboard.updated_at))
            
            conn.commit()
            conn.close()
            
        except Exception:
            pass
    
    def _load_chart(self, chart_id: str) -> Optional[Chart]:
        """Load chart from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT title, chart_type, data, config, created_at, updated_at
                FROM charts WHERE chart_id = ?
            ''', (chart_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                chart = Chart(chart_id, row[0], row[1], json.loads(row[2]), 
                            json.loads(row[3]) if row[3] else {})
                chart.created_at = row[4]
                chart.updated_at = row[5]
                return chart
            
            return None
            
        except Exception:
            return None
    
    def _load_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Load dashboard from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name, description, layout, created_at, updated_at
                FROM dashboards WHERE dashboard_id = ?
            ''', (dashboard_id,))
            
            row = cursor.fetchone()
            
            if row:
                dashboard = Dashboard(dashboard_id, row[0], row[1])
                dashboard.layout = json.loads(row[2]) if row[2] else {}
                dashboard.created_at = row[3]
                dashboard.updated_at = row[4]
                
                # Load associated charts
                cursor.execute('''
                    SELECT chart_id FROM dashboard_charts 
                    WHERE dashboard_id = ? ORDER BY position
                ''', (dashboard_id,))
                
                dashboard.charts = [row[0] for row in cursor.fetchall()]
                
                conn.close()
                return dashboard
            
            conn.close()
            return None
            
        except Exception:
            return None

# Global visualization manager instance
viz_manager = VisualizationManager()

def main():
    """Demo of visualization manager functionality"""
    
    # Create sample charts
    line_chart = viz_manager.create_chart(
        "Sales Trend",
        "line",
        {
            "x": ["Jan", "Feb", "Mar", "Apr", "May"],
            "y": [100, 150, 120, 200, 180]
        },
        {"xlabel": "Month", "ylabel": "Sales ($)", "grid": True}
    )
    print("Line chart created:", line_chart)
    
    bar_chart = viz_manager.create_chart(
        "Product Categories",
        "bar",
        {
            "categories": ["Electronics", "Clothing", "Books", "Sports"],
            "values": [250, 180, 90, 150]
        }
    )
    print("Bar chart created:", bar_chart)
    
    # Create dashboard
    dashboard = viz_manager.create_dashboard("Sales Dashboard", "Monthly sales overview")
    print("Dashboard created:", dashboard)
    
    if dashboard["success"] and line_chart["success"] and bar_chart["success"]:
        # Add charts to dashboard
        viz_manager.add_chart_to_dashboard(dashboard["dashboard_id"], line_chart["chart_id"])
        viz_manager.add_chart_to_dashboard(dashboard["dashboard_id"], bar_chart["chart_id"])
        
        # Generate dashboard HTML
        html_result = viz_manager.generate_dashboard_html(dashboard["dashboard_id"])
        print("Dashboard HTML generated:", html_result["success"])
    
    # Generate analytics report
    report = viz_manager.generate_analytics_report("website_analytics")
    print("Analytics report generated:", report["success"])

if __name__ == "__main__":
    main()