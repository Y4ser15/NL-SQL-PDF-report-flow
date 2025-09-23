from __future__ import annotations
import ast
import json
import re
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

# Langflow base + typed IO
from langflow.custom import Component
from langflow.io import (
    DataInput,
    StrInput,
    MultilineInput,
    BoolInput,
    DropdownInput,
    Output,
)
from langflow.schema import Data

# ---------- Domain models ----------
class ReportModel(BaseModel):
    """Report model for template parser format"""
    title: str
    executive_summary: str = ""
    timeframe: str = ""
    dataset_used: str = "Data Analysis"
    key_metrics: List[Dict[str, Any]] = Field(default_factory=list)
    insights: List[Union[str, Dict[str, str]]] = Field(default_factory=list)
    findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)

# ---------- Parser functions ----------
def _parse_template_format(text: str) -> Dict[str, Any]:
    """Parse template-based format into dict"""
    result = {}
    
    # Define patterns for each field
    patterns = {
        'title': r'^Title:\s*(.+?)(?=\n[A-Z]|\Z)',
        'executive_summary': r'^Executive Summary:\s*(.+?)(?=\n[A-Z]|\Z)',
        'timeframe': r'^Timeframe:\s*(.+?)(?=\n[A-Z]|\Z)',
        'dataset_used': r'^Dataset used:\s*(.+?)(?=\n[A-Z]|\Z)',
        'key_metrics': r'^Key Metrics:\s*(.+?)(?=\n[A-Z]|\Z)',
        'insights': r'^Insights:\s*(.+?)(?=\n[A-Z]|\Z)',
        'findings': r'^Findings:\s*(.+?)(?=\n[A-Z]|\Z)',
        'recommendations': r'^Recommendations:\s*(.+?)(?=\n[A-Z]|\Z)',
        'limitations': r'^Limitations:\s*(.+?)(?=\n[A-Z]|\Z)',
        'next_steps': r'^Next Steps:\s*(.+?)(?=\n[A-Z]|\Z)'
    }
    
    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
        if match:
            value = match.group(1).strip()
            
            # Try to parse lists and dicts
            if value.startswith('['):
                try:
                    result[field] = ast.literal_eval(value)
                except:
                    result[field] = []
            else:
                result[field] = value
    
    return result

# ---------- Chart generation functions ----------
def _create_bar_chart(c, data: List[Dict], x: float, y: float, width: float, height: float, 
                     title: str = "", key_field: str = None, value_field: str = None) -> float:
    """Create a bar chart from data"""
    from reportlab.lib import colors
    from reportlab.graphics.shapes import Drawing, Rect, String
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics import renderPDF
    
    if not data or not isinstance(data, list):
        return y
    
    # Auto-detect fields if not specified
    if not key_field and isinstance(data[0], dict):
        keys = list(data[0].keys())
        key_field = keys[0] if keys else None
    
    if not value_field and isinstance(data[0], dict):
        keys = list(data[0].keys())
        value_field = keys[1] if len(keys) > 1 else keys[0] if keys else None
    
    if not key_field or not value_field:
        return y
    
    # Prepare data
    labels = []
    values = []
    
    for item in data[:10]:  # Limit to 10 items for visibility
        if isinstance(item, dict):
            labels.append(str(item.get(key_field, ""))[:10])  # Truncate labels
            try:
                values.append(float(item.get(value_field, 0)))
            except:
                values.append(0)
    
    if not values:
        return y
    
    # Create drawing and chart
    d = Drawing(width, height)
    
    # Add title
    if title:
        d.add(String(width/2, height-15, title, 
                    fontSize=11, fontName='Helvetica-Bold', 
                    textAnchor='middle'))
    
    # Create bar chart
    bc = VerticalBarChart()
    bc.x = 30
    bc.y = 30
    bc.height = height - 60
    bc.width = width - 60
    bc.data = [values]
    bc.categoryAxis.categoryNames = labels
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = max(values) * 1.1
    
    # Styling
    bc.bars[0].fillColor = colors.HexColor('#3498DB')
    bc.categoryAxis.labels.boxAnchor = 'n'
    bc.categoryAxis.labels.angle = 45 if len(labels) > 5 else 0
    bc.categoryAxis.labels.dy = -8
    bc.categoryAxis.labels.fontSize = 8
    bc.valueAxis.labels.fontSize = 8
    
    d.add(bc)
    
    # Render to canvas
    renderPDF.draw(d, c, x, y - height)
    
    return y - height - 20

def _create_pie_chart(c, data: List[Dict], x: float, y: float, width: float, height: float,
                     title: str = "", key_field: str = None, value_field: str = None) -> float:
    """Create a pie chart from data"""
    from reportlab.lib import colors
    from reportlab.graphics.shapes import Drawing, String
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics import renderPDF
    
    if not data or not isinstance(data, list):
        return y
    
    # Auto-detect fields
    if not key_field and isinstance(data[0], dict):
        keys = list(data[0].keys())
        key_field = keys[0] if keys else None
    
    if not value_field and isinstance(data[0], dict):
        keys = list(data[0].keys())
        value_field = keys[1] if len(keys) > 1 else keys[0] if keys else None
    
    if not key_field or not value_field:
        return y
    
    # Prepare data (limit to top 8 for visibility)
    labels = []
    values = []
    
    for item in data[:8]:
        if isinstance(item, dict):
            labels.append(str(item.get(key_field, "")))
            try:
                values.append(float(item.get(value_field, 0)))
            except:
                values.append(0)
    
    if not values or sum(values) == 0:
        return y
    
    # Create drawing
    d = Drawing(width, height)
    
    # Add title
    if title:
        d.add(String(width/2, height-15, title,
                    fontSize=11, fontName='Helvetica-Bold',
                    textAnchor='middle'))
    
    # Create pie chart
    pie = Pie()
    pie.x = width/2 - 60
    pie.y = height/2 - 60
    pie.width = 120
    pie.height = 120
    pie.data = values
    pie.labels = [f"{l}\n({v:,.0f})" for l, v in zip(labels, values)]
    pie.slices.strokeWidth = 0.5
    
    # Color scheme
    color_palette = [
        colors.HexColor('#3498DB'),
        colors.HexColor('#2ECC71'),
        colors.HexColor('#F39C12'),
        colors.HexColor('#E74C3C'),
        colors.HexColor('#9B59B6'),
        colors.HexColor('#1ABC9C'),
        colors.HexColor('#34495E'),
        colors.HexColor('#F1C40F')
    ]
    
    for i, color in enumerate(color_palette[:len(values)]):
        pie.slices[i].fillColor = color
        pie.slices[i].labelRadius = 1.2
        pie.slices[i].fontSize = 7
    
    d.add(pie)
    
    # Render to canvas
    renderPDF.draw(d, c, x, y - height)
    
    return y - height - 20

def _draw_header(c, title: str, page_width: float, page_height: float) -> float:
    """Draw a professional header with gradient effect"""
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    
    # Draw gradient background (simulated with multiple rectangles)
    gradient_colors = [
        colors.HexColor('#2C3E50'),
        colors.HexColor('#34495E'),
        colors.HexColor('#3D5A6C')
    ]
    
    header_height = 3 * cm
    for i, color in enumerate(gradient_colors):
        c.setFillColor(color)
        c.rect(0, page_height - header_height + (i * 0.3 * cm), 
               page_width, header_height - (i * 0.3 * cm), 
               fill=1, stroke=0)
    
    # Add company/report title
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(2 * cm, page_height - 1.8 * cm, title)
    
    # Add date
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, page_height - 2.3 * cm, 
                f"Generated: {datetime.now().strftime('%B %d, %Y')}")
    
    # Add decorative line
    c.setStrokeColor(colors.HexColor('#3498DB'))
    c.setLineWidth(2)
    c.line(0, page_height - header_height, page_width, page_height - header_height)
    
    return page_height - header_height - 0.5 * cm

def _draw_styled_table(c, data: List[Dict], x: float, y: float, page_width: float, 
                      title: str = "", max_rows: int = 15) -> float:
    """Draw a styled table with alternating row colors"""
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import Table, TableStyle
    
    if not data or not isinstance(data, list):
        return y
    
    # Title
    if title:
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor('#2C3E50'))
        c.drawString(x, y, title)
        c.setFillColor(colors.black)
        y -= 20
    
    # Prepare table data
    if data and isinstance(data[0], dict):
        columns = list(data[0].keys())
        
        # Format column headers
        headers = [col.replace('_', ' ').title() for col in columns]
        
        # Create rows
        rows = []
        for item in data[:max_rows]:
            row = []
            for col in columns:
                value = item.get(col, "")
                # Format numbers
                if isinstance(value, (int, float)):
                    if isinstance(value, float):
                        row.append(f"{value:,.2f}")
                    else:
                        row.append(f"{value:,}")
                else:
                    row.append(str(value))
            rows.append(row)
        
        # Combine headers and rows
        table_data = [headers] + rows
        
        # Calculate column widths
        available_width = page_width - (2 * x)
        col_count = len(columns)
        col_widths = [available_width / col_count] * col_count
        
        # Create table
        t = Table(table_data, colWidths=col_widths)
        
        # Apply modern styling
        style = TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            
            # Body styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), 
             [colors.white, colors.HexColor('#ECF0F1')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ])
        
        t.setStyle(style)
        
        # Calculate height and draw
        w, h = t.wrapOn(c, available_width, 20 * cm)
        
        # Check if fits on page
        if y - h < 2 * cm:
            c.showPage()
            y = 27 * cm
        
        t.drawOn(c, x, y - h)
        y = y - h - 10
        
        # Add summary if data was truncated
        if len(data) > max_rows:
            c.setFont("Helvetica-Oblique", 8)
            c.setFillColor(colors.HexColor('#7F8C8D'))
            c.drawString(x, y, f"* Showing {max_rows} of {len(data)} total records")
            c.setFillColor(colors.black)
            y -= 15
    
    return y

def _draw_metric_cards(c, metrics: List[Dict], x: float, y: float, page_width: float) -> float:
    """Draw metrics as styled cards"""
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    
    if not metrics:
        return y
    
    # Title
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor('#2C3E50'))
    c.drawString(x, y, "Key Metrics")
    c.setFillColor(colors.black)
    y -= 25
    
    # Draw metric cards in a grid
    card_width = 7 * cm
    card_height = 2 * cm
    cards_per_row = 2
    spacing = 0.5 * cm
    
    # Store initial y for consistent row positioning
    start_y = y
    
    for i, metric in enumerate(metrics[:10]):
        row = i // cards_per_row
        col = i % cards_per_row
        
        card_x = x + col * (card_width + spacing)
        card_y = start_y - row * (card_height + spacing)
        
        # Check if need new page
        if card_y - card_height < 3 * cm:
            c.showPage()
            start_y = 27 * cm
            card_y = start_y - (row * (card_height + spacing))
        
        # Draw card background
        c.setFillColor(colors.HexColor('#F8F9FA'))
        c.roundRect(card_x, card_y - card_height, card_width, card_height, 
                   5, fill=1, stroke=1)
        c.setStrokeColor(colors.HexColor('#BDC3C7'))
        c.setLineWidth(0.5)
        c.roundRect(card_x, card_y - card_height, card_width, card_height, 
                   5, fill=0, stroke=1)
        
        # Add metric content
        if isinstance(metric, dict):
            # Get first two key-value pairs
            items = list(metric.items())[:2]
            
            if items:
                # Primary metric (larger font)
                key, value = items[0]
                c.setFont("Helvetica", 10)
                c.setFillColor(colors.HexColor('#7F8C8D'))
                c.drawString(card_x + 10, card_y - 20, 
                           key.replace('_', ' ').title())
                
                c.setFont("Helvetica-Bold", 16)
                c.setFillColor(colors.HexColor('#2C3E50'))
                c.drawString(card_x + 10, card_y - 40, str(value))
                
                # Secondary metric (if exists)
                if len(items) > 1:
                    key, value = items[1]
                    c.setFont("Helvetica", 9)
                    c.setFillColor(colors.HexColor('#95A5A6'))
                    c.drawString(card_x + 10, card_y - 55, 
                               f"{key.replace('_', ' ').title()}: {value}")
        
        c.setFillColor(colors.black)
    
    # Calculate final y position based on actual rows used
    total_rows = (min(len(metrics), 10) + cards_per_row - 1) // cards_per_row
    final_y = start_y - (total_rows * (card_height + spacing)) - 20
    
    return final_y

def _draw_insights_section(c, insights: List, x: float, y: float, page_width: float) -> float:
    """Draw insights with icons and styling"""
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    
    if not insights:
        return y
    
    # Section title
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor('#2C3E50'))
    c.drawString(x, y, "Key Insights")
    c.setFillColor(colors.black)
    y -= 20
    
    for i, insight in enumerate(insights[:8], 1):
        # Check page break with more buffer
        if y < 5 * cm:  # Increased buffer for better spacing
            c.showPage()
            y = 27 * cm
            # Redraw section title on new page
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(colors.HexColor('#2C3E50'))
            c.drawString(x, y, "Key Insights (continued)")
            c.setFillColor(colors.black)
            y -= 20
        
        # Draw insight number in circle
        c.setFillColor(colors.HexColor('#3498DB'))
        c.circle(x + 10, y - 5, 8, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x + 7, y - 8, str(i))
        
        # Draw insight text
        c.setFillColor(colors.HexColor('#2C3E50'))
        c.setFont("Helvetica", 10)
        
        text = ""
        if isinstance(insight, dict):
            text = insight.get('insight', str(insight))
        else:
            text = str(insight)
        
        # Wrap text
        wrapped = textwrap.wrap(text, width=90)
        text_x = x + 25
        
        for line in wrapped:
            c.drawString(text_x, y - 8, line)
            y -= 14
        
        y -= 8
    
    c.setFillColor(colors.black)
    return y

# ---------- Main PDF generation ----------
def _write_visual_pdf(report: ReportModel, query_data: Optional[List[Dict]], 
                     out_path: Path, chart_type: str = "Auto") -> None:
    """Write enhanced PDF with visualizations and styling"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        from reportlab.lib import colors
    except ImportError:
        raise RuntimeError(
            "Missing dependency: reportlab. Install with: pip install reportlab"
        )
    
    c = canvas.Canvas(str(out_path), pagesize=A4)
    page_width, page_height = A4
    x = 2 * cm
    
    # Draw header
    y = _draw_header(c, report.title, page_width, page_height)
    
    # Executive Summary with styling
    if report.executive_summary:
        # Draw summary box
        c.setFillColor(colors.HexColor('#EBF5FB'))
        c.roundRect(x - 10, y - 60, page_width - 2*x + 20, 50, 5, fill=1, stroke=1)
        c.setStrokeColor(colors.HexColor('#3498DB'))
        c.setLineWidth(1)
        c.roundRect(x - 10, y - 60, page_width - 2*x + 20, 50, 5, fill=0, stroke=1)
        
        # Summary text
        c.setFillColor(colors.HexColor('#2C3E50'))
        c.setFont("Helvetica", 11)
        wrapped = textwrap.wrap(report.executive_summary, width=80)
        text_y = y - 20
        for line in wrapped[:3]:  # Max 3 lines
            c.drawString(x, text_y, line)
            text_y -= 14
        
        y -= 70
        c.setFillColor(colors.black)
    
    # Visualizations from query data - only if chart_type is not "None"
    if chart_type != "None" and query_data and isinstance(query_data, list) and query_data:
        # Determine data structure
        if isinstance(query_data[0], dict):
            keys = list(query_data[0].keys())
            
            # Find numeric field
            numeric_field = None
            for key in keys:
                if isinstance(query_data[0].get(key), (int, float)):
                    numeric_field = key
                    break
            
            # Draw charts based on chart_type setting
            if numeric_field:
                if chart_type in ["Auto", "Bar", "Both"]:
                    if len(query_data) <= 15:
                        y = _create_bar_chart(c, query_data, x, y, 
                                            page_width - 2*x, 200,
                                            title="Data Distribution",
                                            value_field=numeric_field)
                
                if chart_type in ["Auto", "Pie", "Both"]:
                    if len(query_data) >= 3:
                        y = _create_pie_chart(c, query_data[:8], x, y,
                                            page_width - 2*x, 200,
                                            title="Top Items Distribution",
                                            value_field=numeric_field)
    
    # Metric cards
    if report.key_metrics:
        if y < 10 * cm:
            c.showPage()
            y = 27 * cm
        else:
            y -= 15  # Add spacing between sections
        y = _draw_metric_cards(c, report.key_metrics, x, y, page_width)
    
    # Data table from query results
    if query_data and isinstance(query_data, list):
        if y < 10 * cm:
            c.showPage()
            y = 27 * cm
        else:
            y -= 15  # Add spacing between sections
        y = _draw_styled_table(c, query_data, x, y, page_width, 
                              title="Detailed Results", max_rows=15)
    
    # Insights section
    if report.insights:
        if y < 10 * cm:
            c.showPage()
            y = 27 * cm
        else:
            y -= 15  # Add spacing between sections
        y = _draw_insights_section(c, report.insights, x, y, page_width)
    
    # Findings with bullets
    if report.findings:
        if y < 8 * cm:
            c.showPage()
            y = 27 * cm
        else:
            y -= 15  # Add spacing between sections
        
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor('#2C3E50'))
        c.drawString(x, y, "Detailed Findings")
        c.setFillColor(colors.black)
        y -= 20
        
        for finding in report.findings[:10]:
            # Check if we need a new page before starting a finding
            if y < 4 * cm:  # Increased buffer
                c.showPage()
                y = 27 * cm
                # Redraw section title on new page
                c.setFont("Helvetica-Bold", 14)
                c.setFillColor(colors.HexColor('#2C3E50'))
                c.drawString(x, y, "Detailed Findings (continued)")
                c.setFillColor(colors.black)
                y -= 20
            
            c.setFont("Helvetica", 10)
            # Draw bullet
            c.setFillColor(colors.HexColor('#3498DB'))
            c.circle(x + 5, y - 4, 2, fill=1, stroke=0)
            c.setFillColor(colors.black)
            # Draw text
            wrapped = textwrap.wrap(finding, width=85)
            for j, line in enumerate(wrapped):
                if j == 0:
                    c.drawString(x + 15, y - 5, line)
                else:
                    c.drawString(x + 15, y - 5, line)
                y -= 14
            y -= 5
    
    # Recommendations with icons
    if report.recommendations:
        if y < 8 * cm:
            c.showPage()
            y = 27 * cm
        else:
            y -= 15  # Add spacing between sections
        
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor('#27AE60'))
        c.drawString(x, y, "Recommendations")
        c.setFillColor(colors.black)
        y -= 20
        
        for i, rec in enumerate(report.recommendations[:8], 1):
            # Check if we need a new page before starting a recommendation
            if y < 4 * cm:  # Increased buffer
                c.showPage()
                y = 27 * cm
                # Redraw section title on new page
                c.setFont("Helvetica-Bold", 14)
                c.setFillColor(colors.HexColor('#27AE60'))
                c.drawString(x, y, "Recommendations (continued)")
                c.setFillColor(colors.black)
                y -= 20
            
            # Draw check icon
            c.setStrokeColor(colors.HexColor('#27AE60'))
            c.setLineWidth(2)
            c.line(x + 3, y - 3, x + 6, y - 6)
            c.line(x + 6, y - 6, x + 12, y + 2)
            c.setStrokeColor(colors.black)  # Reset stroke color
            c.setLineWidth(1)  # Reset line width
            
            c.setFont("Helvetica", 10)
            c.setFillColor(colors.HexColor('#2C3E50'))
            wrapped = textwrap.wrap(rec, width=85)
            for j, line in enumerate(wrapped):
                if j == 0:
                    c.drawString(x + 20, y - 5, line)
                else:
                    c.drawString(x + 20, y - 5, line)
                y -= 14
            y -= 5
        
        c.setFillColor(colors.black)  # Reset fill color
    
    # Limitations and Next Steps in columns
    if report.limitations or report.next_steps:
        if y < 10 * cm:
            c.showPage()
            y = 27 * cm
        else:
            y -= 15  # Add spacing between sections
        
        # Two column layout
        col_width = (page_width - 2*x) / 2 - 20
        
        # Track the lowest y position for both columns
        lowest_y = y
        
        # Limitations column
        if report.limitations:
            c.setFont("Helvetica-Bold", 12)
            c.setFillColor(colors.HexColor('#E67E22'))
            c.drawString(x, y, "Limitations")
            c.setFillColor(colors.black)
            temp_y = y - 18
            
            c.setFont("Helvetica", 9)
            for lim in report.limitations[:5]:
                # Wrap text properly
                wrapped = textwrap.wrap(lim, width=40)
                if wrapped:
                    # First line with bullet
                    c.drawString(x + 5, temp_y, f"• {wrapped[0]}")
                    temp_y -= 12
                    # Continuation lines without bullet
                    for line in wrapped[1:]:
                        c.drawString(x + 12, temp_y, line)
                        temp_y -= 12
                    temp_y -= 3  # Small gap between items
            
            lowest_y = min(lowest_y, temp_y)
        
        # Next Steps column
        if report.next_steps:
            c.setFont("Helvetica-Bold", 12)
            c.setFillColor(colors.HexColor('#8E44AD'))
            c.drawString(x + col_width + 40, y, "Next Steps")
            c.setFillColor(colors.black)
            temp_y = y - 18
            
            c.setFont("Helvetica", 9)
            for step in report.next_steps[:5]:
                # Wrap text properly
                wrapped = textwrap.wrap(step, width=40)
                if wrapped:
                    # First line with arrow
                    c.drawString(x + col_width + 45, temp_y, f"→ {wrapped[0]}")
                    temp_y -= 12
                    # Continuation lines without arrow
                    for line in wrapped[1:]:
                        c.drawString(x + col_width + 52, temp_y, line)
                        temp_y -= 12
                    temp_y -= 3  # Small gap between items
            
            lowest_y = min(lowest_y, temp_y)
        
        y = lowest_y - 10
    
    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.HexColor('#95A5A6'))
    c.drawString(x, 1.5 * cm, f"Data Source: {report.dataset_used}")
    c.drawString(page_width - 6*cm, 1.5 * cm, f"Page 1")
    
    # Add footer line
    c.setStrokeColor(colors.HexColor('#BDC3C7'))
    c.setLineWidth(0.5)
    c.line(x, 2*cm, page_width - x, 2*cm)
    
    c.save()

# ---------- Langflow Component ----------
class VisualReportToPDF(Component):
    display_name = "Visual Report → PDF"
    description = "Create professional PDF reports with charts and visualizations"
    icon = "file-text"
    name = "VisualReportToPDF"
    
    inputs = [
        MultilineInput(
            name="report_data",
            display_name="Report Data (Template Format)",
            info="Report from template parser",
            required=True,
        ),
        DataInput(
            name="query_results",
            display_name="Query Results (Data)",
            info="Query results as Data/JSON from SQL component",
            required=False,
        ),
        StrInput(
            name="file_name",
            display_name="Output File Name",
            value="report.pdf",
            info="PDF file name",
        ),
        StrInput(
            name="output_folder",
            display_name="Output Folder",
            value=".",
            info="Where to save the PDF",
        ),
        DropdownInput(
            name="chart_type",
            display_name="Primary Chart Type",
            options=["Auto", "Bar", "Pie", "Both", "None"],
            value="Auto",
            info="Type of visualization to include",
        ),
    ]
    
    outputs = [
        Output(
            name="pdf_file",
            display_name="PDF File",
            method="build_pdf",
        ),
        Output(
            name="report_info",
            display_name="Report Info",
            method="build_info",
        ),
    ]
    
    def _parse_report(self) -> ReportModel:
        """Parse report from template format"""
        try:
            raw = self.report_data
            
            # Handle different input types
            if hasattr(raw, 'text'):
                raw = raw.text
            elif hasattr(raw, 'data'):
                if isinstance(raw.data, str):
                    raw = raw.data
                else:
                    return ReportModel(**raw.data)
            
            if isinstance(raw, str):
                data = _parse_template_format(raw)
            else:
                data = raw
            
            return ReportModel(**data)
            
        except Exception as e:
            raise ValueError(f"Failed to parse report: {e}")
    
    def _get_query_data(self) -> Optional[List[Dict]]:
        """Extract query results data"""
        if not self.query_results:
            return None
        
        try:
            # Handle Data object
            if hasattr(self.query_results, 'data'):
                data = self.query_results.data
                
                # Check if it's the expected format
                if isinstance(data, dict) and 'results' in data:
                    return data['results']
                elif isinstance(data, list):
                    return data
                elif isinstance(data, str):
                    parsed = json.loads(data)
                    if isinstance(parsed, dict) and 'results' in parsed:
                        return parsed['results']
                    elif isinstance(parsed, list):
                        return parsed
            
            # Handle direct list
            elif isinstance(self.query_results, list):
                return self.query_results
            
            # Handle JSON string
            elif isinstance(self.query_results, str):
                parsed = json.loads(self.query_results)
                if isinstance(parsed, dict) and 'results' in parsed:
                    return parsed['results']
                elif isinstance(parsed, list):
                    return parsed
        
        except Exception as e:
            self.log(f"Could not parse query results: {e}")
        
        return None
    
    def build_pdf(self) -> Data:
        """Build the visual PDF report"""
        if not self.report_data:
            raise ValueError("Missing 'report_data' input.")
        
        try:
            report = self._parse_report()
            query_data = self._get_query_data()
        except Exception as e:
            self.log(f"[VisualReportToPDF] Parse error: {e}")
            self.status = f"Parse error: {e}"
            return Data(data={"error": str(e)}, text="Failed to parse report.")
        
        # Setup output path
        folder = Path(self.output_folder or ".")
        folder.mkdir(parents=True, exist_ok=True)
        
        file_name = (self.file_name or "report.pdf").strip() or "report.pdf"
        if not file_name.lower().endswith(".pdf"):
            file_name += ".pdf"
        
        out_path = folder / file_name
        
        try:
            _write_visual_pdf(report, query_data, out_path, chart_type=self.chart_type)
        except Exception as e:
            self.log(f"[VisualReportToPDF] PDF rendering failed: {e}")
            self.status = f"Rendering error: {e}"
            return Data(data={"error": str(e)}, text="Rendering failed.")
        
        self.status = f"Visual PDF created: {out_path}"
        
        # Prepare output info
        info = {
            "pdf_path": str(out_path),
            "file_name": file_name,
            "folder": str(folder),
            "metrics_count": len(report.key_metrics),
            "has_charts": query_data is not None and len(query_data) > 0,
            "total_insights": len(report.insights),
            "total_findings": len(report.findings)
        }
        
        if query_data:
            info["data_rows"] = len(query_data)
        
        return Data(
            data=info,
            text=f"Visual PDF report generated → {out_path}",
        )
    
    def build_info(self) -> Data:
        """Return information about the report"""
        try:
            report = self._parse_report()
            query_data = self._get_query_data()
            
            info = {
                "title": report.title,
                "has_summary": bool(report.executive_summary),
                "metrics_count": len(report.key_metrics),
                "findings_count": len(report.findings),
                "insights_count": len(report.insights),
                "recommendations_count": len(report.recommendations),
                "has_query_data": query_data is not None,
                "data_rows": len(query_data) if query_data else 0
            }
            
            return Data(
                data=info,
                text=f"Report: {report.title} ({len(report.findings)} findings, {len(query_data) if query_data else 0} data rows)"
            )
        except Exception as e:
            return Data(data={"error": str(e)}, text=f"Failed to analyze report: {e}")