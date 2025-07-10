import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
from PIL import Image as PILImage

logger = logging.getLogger(__name__)

class PDFGenerator:
    """Generate PDF documents from HTML templates"""
    
    def __init__(self):
        self.styles = self._initialize_styles()
        self.page_size = A4
        self.margins = {
            'left': 72,
            'right': 72,
            'top': 72,
            'bottom': 72
        }
    
    def _initialize_styles(self) -> Dict[str, ParagraphStyle]:
        """Initialize custom paragraph styles"""
        styles = getSampleStyleSheet()
        
        # Custom styles
        custom_styles = {
            'CustomTitle': ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#0066CC'),
                alignment=TA_CENTER,
                spaceAfter=30,
                fontName='Helvetica-Bold'
            ),
            'CustomHeading': ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#333333'),
                spaceAfter=12,
                fontName='Helvetica-Bold'
            ),
            'CustomSubheading': ParagraphStyle(
                'CustomSubheading',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=colors.HexColor('#444444'),
                spaceAfter=10,
                fontName='Helvetica-Bold'
            ),
            'CustomNormal': ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=11,
                alignment=TA_JUSTIFY,
                spaceAfter=12,
                leading=16
            ),
            'CustomBullet': ParagraphStyle(
                'CustomBullet',
                parent=styles['Normal'],
                fontSize=11,
                leftIndent=20,
                spaceAfter=8
            ),
            'RightAlign': ParagraphStyle(
                'RightAlign',
                parent=styles['Normal'],
                fontSize=11,
                alignment=TA_RIGHT
            ),
            'CenterAlign': ParagraphStyle(
                'CenterAlign',
                parent=styles['Normal'],
                fontSize=11,
                alignment=TA_CENTER
            ),
            'Footer': ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                alignment=TA_CENTER,
                textColor=colors.grey
            ),
            'Signature': ParagraphStyle(
                'Signature',
                parent=styles['Normal'],
                fontSize=11,
                alignment=TA_LEFT,
                spaceAfter=5
            )
        }
        
        # Add custom styles to default styles
        for name, style in custom_styles.items():
            styles.add(style)
        
        return styles
    
    def generate_pdf(self, content: str, output_path: str, 
                    document_type: str = 'letter',
                    metadata: Dict[str, Any] = None) -> bool:
        """Generate PDF from HTML content"""
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=self.page_size,
                rightMargin=self.margins['right'],
                leftMargin=self.margins['left'],
                topMargin=self.margins['top'],
                bottomMargin=self.margins['bottom']
            )
            
            # Build story (content elements)
            story = []
            
            # Add header/logo if provided
            if metadata and 'logo_path' in metadata:
                story.extend(self._add_header(metadata['logo_path']))
            
            # Convert HTML content to reportlab elements
            story.extend(self._html_to_story(content))
            
            # Add footer if required
            if metadata and metadata.get('add_footer', False):
                # This would require custom page template
                pass
            
            # Build PDF
            doc.build(story, onFirstPage=self._add_page_number, 
                     onLaterPages=self._add_page_number)
            
            logger.info(f"PDF generated successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return False
    
    def generate_pdf_from_template(self, template_type: str, data: Dict[str, Any], 
                                  output_path: str) -> bool:
        """Generate PDF from predefined template"""
        try:
            # Get appropriate template generator
            generators = {
                'offer_letter': self._generate_offer_letter,
                'appointment_letter': self._generate_appointment_letter,
                'experience_letter': self._generate_experience_letter,
                'fnf_statement': self._generate_fnf_statement,
                'asset_handover': self._generate_asset_handover_form
            }
            
            generator = generators.get(template_type)
            if not generator:
                logger.error(f"Unknown template type: {template_type}")
                return False
            
            # Generate PDF using specific template
            return generator(data, output_path)
            
        except Exception as e:
            logger.error(f"Error generating PDF from template: {str(e)}")
            return False
    
    def _html_to_story(self, html_content: str) -> List:
        """Convert HTML content to reportlab story elements"""
        story = []
        
        # Simple HTML parsing (in production, use BeautifulSoup or similar)
        lines = html_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Headers
            if line.startswith('<h1>') and line.endswith('</h1>'):
                text = line[4:-5]
                story.append(Paragraph(text, self.styles['CustomTitle']))
                story.append(Spacer(1, 20))
            
            elif line.startswith('<h2>') and line.endswith('</h2>'):
                text = line[4:-5]
                story.append(Paragraph(text, self.styles['CustomHeading']))
                story.append(Spacer(1, 12))
            
            elif line.startswith('<h3>') and line.endswith('</h3>'):
                text = line[4:-5]
                story.append(Paragraph(text, self.styles['CustomSubheading']))
                story.append(Spacer(1, 10))
            
            # Paragraphs
            elif line.startswith('<p>') and line.endswith('</p>'):
                text = line[3:-4]
                
                # Check for special classes
                if 'class=' in line:
                    if 'right' in line.lower():
                        style = self.styles['RightAlign']
                    elif 'center' in line.lower():
                        style = self.styles['CenterAlign']
                    else:
                        style = self.styles['CustomNormal']
                else:
                    style = self.styles['CustomNormal']
                
                story.append(Paragraph(text, style))
                story.append(Spacer(1, 12))
            
            # Lists
            elif line.startswith('<li>') and line.endswith('</li>'):
                text = f"• {line[4:-5]}"
                story.append(Paragraph(text, self.styles['CustomBullet']))
            
            # Tables (simplified)
            elif line.startswith('<table'):
                # Would need more complex parsing for tables
                pass
        
        return story
    
    def _add_header(self, logo_path: str) -> List:
        """Add header with logo"""
        story = []
        
        if os.path.exists(logo_path):
            try:
                img = Image(logo_path, width=2*inch, height=0.75*inch)
                story.append(img)
                story.append(Spacer(1, 20))
            except Exception as e:
                logger.error(f"Error adding logo: {str(e)}")
        
        return story
    
    def _add_page_number(self, canvas_obj, doc):
        """Add page numbers to PDF"""
        canvas_obj.saveState()
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.setFillColor(colors.grey)
        
        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"
        
        canvas_obj.drawCentredString(
            self.page_size[0] / 2,
            0.5 * inch,
            text
        )
        
        canvas_obj.restoreState()
    
    def _generate_offer_letter(self, data: Dict[str, Any], output_path: str) -> bool:
        """Generate offer letter PDF"""
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=self.page_size,
                rightMargin=self.margins['right'],
                leftMargin=self.margins['left'],
                topMargin=self.margins['top'],
                bottomMargin=self.margins['bottom']
            )
            
            story = []
            
            # Add logo
            logo_path = os.path.join('static', 'images', 'company_logo.png')
            if os.path.exists(logo_path):
                story.extend(self._add_header(logo_path))
            
            # Title
            story.append(Paragraph("OFFER LETTER", self.styles['CustomTitle']))
            story.append(Spacer(1, 20))
            
            # Date and Reference
            story.append(Paragraph(f"Date: {data.get('issue_date', '')}", self.styles['RightAlign']))
            story.append(Paragraph(f"Ref: RI/HR/{data.get('employee_id', '')}/2024", self.styles['RightAlign']))
            story.append(Spacer(1, 20))
            
            # Recipient
            story.append(Paragraph(f"<b>{data.get('employee_name', '')}</b>", self.styles['CustomNormal']))
            story.append(Paragraph(data.get('employee_address', ''), self.styles['CustomNormal']))
            story.append(Spacer(1, 20))
            
            # Subject
            story.append(Paragraph(f"<b>Sub: Offer Letter - {data.get('designation', '')}</b>", self.styles['CustomNormal']))
            story.append(Spacer(1, 20))
            
            # Salutation
            story.append(Paragraph(f"Dear {data.get('first_name', '')},", self.styles['CustomNormal']))
            story.append(Spacer(1, 12))
            
            # Body content based on employee type
            if data.get('employee_type') == 'full_time':
                self._add_fulltime_offer_content(story, data)
            elif data.get('employee_type') == 'intern':
                self._add_intern_offer_content(story, data)
            else:
                self._add_contractor_offer_content(story, data)
            
            # Closing
            story.append(Spacer(1, 20))
            story.append(Paragraph(
                "We are confident that you will be able to make a significant contribution to the success of our Company.",
                self.styles['CustomNormal']
            ))
            story.append(Spacer(1, 12))
            story.append(Paragraph(
                "Please sign and share the scanned copy of this letter and return it to the HR Department to indicate your acceptance of this offer.",
                self.styles['CustomNormal']
            ))
            story.append(Spacer(1, 30))
            
            # Signature section
            self._add_signature_section(story, data)
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            logger.error(f"Error generating offer letter: {str(e)}")
            return False
    
    def _add_fulltime_offer_content(self, story: List, data: Dict[str, Any]):
        """Add full-time employee offer content"""
        # Opening
        content = f"""With reference to your application and subsequent discussion/interview, 
        we are pleased to offer you the position of <b>{data.get('designation', '')}</b>. 
        You are expected to join on <b>{data.get('date_of_joining', '')}</b> on or before."""
        story.append(Paragraph(content, self.styles['CustomNormal']))
        story.append(Spacer(1, 12))
        
        # CTC
        content = f"""Your CTC (Cost-to-Company) will be <b>{data.get('ctc', '')} 
        ({data.get('ctc_words', '')})</b> per annum."""
        story.append(Paragraph(content, self.styles['CustomNormal']))
        story.append(Spacer(1, 12))
        
        # CTC Breakdown Table
        if 'ctc_breakdown' in data:
            story.append(Paragraph("<b>Compensation Structure:</b>", self.styles['CustomNormal']))
            story.append(Spacer(1, 12))
            story.append(self._create_ctc_table(data['ctc_breakdown']))
            story.append(Spacer(1, 20))
        
        # Probation
        content = f"""You will be on probation for a period of {data.get('probation_period', 3)} months 
        from the date of your joining. Your performance will be assessed for confirmation."""
        story.append(Paragraph(content, self.styles['CustomNormal']))
    
    def _add_intern_offer_content(self, story: List, data: Dict[str, Any]):
        """Add intern offer content"""
        # Opening
        content = f"""With reference to your application and subsequent discussion/interview, 
        we are pleased to offer you the position of <b>{data.get('designation', '')} Intern</b>. 
        You are expected to join on <b>{data.get('date_of_joining', '')}</b>."""
        story.append(Paragraph(content, self.styles['CustomNormal']))
        story.append(Spacer(1, 12))
        
        # Stipend
        content = f"""It will be <b>{data.get('internship_duration', '6 months')} of Internship</b> 
        starting from your date of joining, and the stipend will be <b>{data.get('stipend', '')}</b> per month."""
        story.append(Paragraph(content, self.styles['CustomNormal']))
        story.append(Spacer(1, 12))
        
        # Performance
        content = """We will assess your performance for the initial 15 days, and if we determine 
        your performance is unsatisfactory, we may terminate your employment with us."""
        story.append(Paragraph(content, self.styles['CustomNormal']))
    
    def _add_contractor_offer_content(self, story: List, data: Dict[str, Any]):
        """Add contractor offer content"""
        # Opening
        content = f"""This Contract Agreement is by and between {data.get('employee_name', '')} 
        and RAPID INNOVATION and defines the scope of work and fees for services to be performed."""
        story.append(Paragraph(content, self.styles['CustomNormal']))
        story.append(Spacer(1, 12))
        
        # Compensation
        content = f"""Regarding your compensation, you will be paid on Hourly basis 
        <b>{data.get('hourly_rate', '')}</b>, which reflects our acknowledgment of your 
        valuable contributions to the team."""
        story.append(Paragraph(content, self.styles['CustomNormal']))
    
    def _create_ctc_table(self, ctc_breakdown: Dict[str, Any]) -> Table:
        """Create CTC breakdown table"""
        # Table data
        data = [
            ['Component', 'Monthly (₹)', 'Annual (₹)'],
            ['Basic Salary', ctc_breakdown.get('monthly_basic', ''), ctc_breakdown.get('basic_salary', '')],
            ['HRA', ctc_breakdown.get('monthly_hra', ''), ctc_breakdown.get('hra', '')],
            ['Special Allowance', ctc_breakdown.get('monthly_special', ''), ctc_breakdown.get('special_allowance', '')],
            ['Medical Allowance', '1,250', '15,000'],
            ['Books & Periodicals', '1,000', '12,000'],
            ['', '', ''],
            ['Gross CTC', ctc_breakdown.get('monthly_gross', ''), ctc_breakdown.get('gross_ctc', '')],
            ['PF Employer Contribution', ctc_breakdown.get('monthly_pf', ''), ctc_breakdown.get('pf_employer', '')],
            ['', '', ''],
            ['Total CTC', '', ctc_breakdown.get('total_ctc', '')]
        ]
        
        # Create table
        table = Table(data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        
        # Apply style
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.8, 0.8, 0.8)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            
            # Total row
            ('BACKGROUND', (0, -1), (-1, -1), colors.Color(0.9, 0.9, 0.9)),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        return table
    
    def _add_signature_section(self, story: List, data: Dict[str, Any]):
        """Add signature section to letter"""
        story.append(Paragraph("Sincerely,", self.styles['CustomNormal']))
        story.append(Spacer(1, 40))
        
        # Create signature table
        sig_data = [
            [data.get('hr_manager_name', ''), '', 'Accepted By'],
            [data.get('hr_manager_designation', ''), '', data.get('employee_name', '')],
            ['', '', ''],
            ['Date: _____________', '', 'Date: _____________']
        ]
        
        sig_table = Table(sig_data, colWidths=[2.5*inch, 1*inch, 2.5*inch])
        sig_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(sig_table)
    
    def _generate_appointment_letter(self, data: Dict[str, Any], output_path: str) -> bool:
        """Generate appointment letter PDF"""
        # Similar structure to offer letter with appointment-specific content
        pass
    
    def _generate_experience_letter(self, data: Dict[str, Any], output_path: str) -> bool:
        """Generate experience letter PDF"""
        # Experience letter specific implementation
        pass
    
    def _generate_fnf_statement(self, data: Dict[str, Any], output_path: str) -> bool:
        """Generate FnF statement PDF"""
        # FnF statement specific implementation
        pass
    
    def _generate_asset_handover_form(self, data: Dict[str, Any], output_path: str) -> bool:
        """Generate asset handover form PDF"""
        # Asset handover form specific implementation
        pass
    
    def merge_pdfs(self, pdf_paths: List[str], output_path: str) -> bool:
        """Merge multiple PDFs into one"""
        try:
            from PyPDF2 import PdfMerger
            
            merger = PdfMerger()
            
            for pdf_path in pdf_paths:
                if os.path.exists(pdf_path):
                    merger.append(pdf_path)
            
            merger.write(output_path)
            merger.close()
            
            logger.info(f"PDFs merged successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error merging PDFs: {str(e)}")
            return False