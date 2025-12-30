"""
Reporting and Export Module
Generates reports in PDF and Excel formats.
"""

import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from src.config.firebase_config import AppConfig
from src.config.logger_config import setup_logger

logger = setup_logger(__name__)


class ReportGenerator:
    """Base report generator class."""

    def __init__(self, title: str = "Report"):
        """Initialize report generator."""
        self.title = title
        self.generated_at = datetime.now()
        self.output_path = AppConfig.REPORT_OUTPUT_PATH

    def _create_filename(self, extension: str) -> str:
        """Create standardized filename."""
        timestamp = self.generated_at.strftime("%Y%m%d_%H%M%S")
        safe_title = self.title.replace(" ", "_").lower()
        return f"{safe_title}_{timestamp}.{extension}"

    def _ensure_output_path(self):
        """Ensure output path exists."""
        os.makedirs(self.output_path, exist_ok=True)


class PDFReportGenerator(ReportGenerator):
    """PDF report generation."""

    def generate_daily_sales_report(
        self, sales_data: List[Dict[str, Any]]
    ) -> tuple[bool, str]:
        """
        Generate daily sales PDF report.

        Args:
            sales_data: List of sales records

        Returns:
            Tuple of (success, filepath)
        """
        try:
            self._ensure_output_path()
            filename = self._create_filename("pdf")
            filepath = os.path.join(self.output_path, filename)

            # Create PDF document
            doc = SimpleDocTemplate(
                filepath,
                pagesize=letter,
                topMargin=0.5 * inch,
                bottomMargin=0.5 * inch,
                leftMargin=0.5 * inch,
                rightMargin=0.5 * inch
            )

            # Build content
            story = []

            # Add title
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=10,
                alignment=1  # Center
            )
            story.append(Paragraph("DAILY SALES REPORT", title_style))
            story.append(Spacer(1, 0.2 * inch))

            # Add report info
            info_style = styles['Normal']
            story.append(Paragraph(
                f"Date: {self.generated_at.strftime('%Y-%m-%d')}<br/>"
                f"Generated: {self.generated_at.strftime('%H:%M:%S')}",
                info_style
            ))
            story.append(Spacer(1, 0.2 * inch))

            # Create sales table
            if sales_data:
                table_data = [
                    ['Nozzle', 'Fuel Type', 'Quantity', 'Unit Price', 'Total Amount', 'Payment Method']
                ]

                for sale in sales_data:
                    table_data.append([
                        sale.get('nozzle_id', '')[:10],
                        sale.get('fuel_type', ''),
                        f"{sale.get('quantity', 0):.2f}",
                        f"{AppConfig.CURRENCY_SYMBOL} {sale.get('unit_price', 0):.2f}",
                        f"{AppConfig.CURRENCY_SYMBOL} {sale.get('total_amount', 0):.2f}",
                        sale.get('payment_method', '')
                    ])

                # Create and style table
                table = Table(table_data, colWidths=[1*inch, 1.2*inch, 1*inch, 1.2*inch, 1.3*inch, 1.3*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]))
                story.append(table)

            # Build PDF
            doc.build(story)
            logger.info(f"Daily sales report generated: {filepath}")
            return True, filepath

        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            return False, str(e)

    def generate_p_and_l_report(
        self, revenue: float, expenses: float
    ) -> tuple[bool, str]:
        """Generate Profit & Loss PDF report."""
        try:
            self._ensure_output_path()
            filename = self._create_filename("pdf")
            filepath = os.path.join(self.output_path, filename)

            doc = SimpleDocTemplate(filepath, pagesize=letter)
            story = []

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1f4788'),
                alignment=1
            )

            story.append(Paragraph("PROFIT & LOSS STATEMENT", title_style))
            story.append(Spacer(1, 0.3 * inch))

            # P&L Table
            profit = revenue - expenses
            pl_data = [
                ['Item', 'Amount'],
                ['Total Revenue', f"{AppConfig.CURRENCY_SYMBOL} {revenue:.2f}"],
                ['Total Expenses', f"{AppConfig.CURRENCY_SYMBOL} {expenses:.2f}"],
                ['Net Profit/(Loss)', f"{AppConfig.CURRENCY_SYMBOL} {profit:.2f}"]
            ]

            table = Table(pl_data, colWidths=[3*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(table)

            doc.build(story)
            logger.info(f"P&L report generated: {filepath}")
            return True, filepath

        except Exception as e:
            logger.error(f"Error generating P&L report: {str(e)}")
            return False, str(e)


class ExcelReportGenerator(ReportGenerator):
    """Excel report generation."""

    def generate_sales_excel(
        self, sales_data: List[Dict[str, Any]]
    ) -> tuple[bool, str]:
        """Generate sales Excel report."""
        try:
            self._ensure_output_path()
            filename = self._create_filename("xlsx")
            filepath = os.path.join(self.output_path, filename)

            # Convert to DataFrame
            df = pd.DataFrame(sales_data)

            # Write to Excel with formatting
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Sales', index=False)
                worksheet = writer.sheets['Sales']

                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

            logger.info(f"Sales Excel report generated: {filepath}")
            return True, filepath

        except Exception as e:
            logger.error(f"Error generating Excel report: {str(e)}")
            return False, str(e)

    def generate_fuel_stock_excel(
        self, tank_data: List[Dict[str, Any]]
    ) -> tuple[bool, str]:
        """Generate fuel stock Excel report."""
        try:
            self._ensure_output_path()
            filename = self._create_filename("xlsx")
            filepath = os.path.join(self.output_path, filename)

            df = pd.DataFrame(tank_data)

            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Stock', index=False)

            logger.info(f"Stock report generated: {filepath}")
            return True, filepath

        except Exception as e:
            logger.error(f"Error generating stock report: {str(e)}")
            return False, str(e)
