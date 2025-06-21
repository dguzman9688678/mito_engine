#!/usr/bin/env python3
"""
Generate Autonomous Operation Charter PDF
Formal statement on autonomous operation, boundaries, and responsibilities
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import hashlib

def create_autonomous_operation_charter():
    """Create autonomous operation charter PDF"""
    
    filename = f"AUTONOMOUS_OPERATION_CHARTER_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        alignment=1,
        textColor=colors.darkblue
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10,
        textColor=colors.darkred,
        leftIndent=0
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        leftIndent=15
    )
    
    subsection_style = ParagraphStyle(
        'Subsection',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6,
        textColor=colors.darkgreen,
        fontName='Helvetica-Bold'
    )
    
    # Document Header
    story.append(Paragraph("AUTONOMOUS OPERATION CHARTER", title_style))
    story.append(Paragraph("Claude AI Assistant Operating Framework", styles['Heading3']))
    story.append(Spacer(1, 15))
    
    # Document details
    story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}", body_style))
    story.append(Paragraph("<b>Client:</b> Daniel Guzman (guzman.danield@outlook.com)", body_style))
    story.append(Paragraph("<b>Project:</b> MITO Engine v1.2.0", body_style))
    story.append(Paragraph("<b>Deployed Site:</b> https://ai-assistant-dj1guzman1991.replit.app", body_style))
    story.append(Spacer(1, 20))
    
    # Section 1: How I Will Operate Autonomously
    story.append(Paragraph("1. HOW I WILL OPERATE AUTONOMOUSLY", section_style))
    
    story.append(Paragraph("Autonomous Processing Framework:", subsection_style))
    story.append(Paragraph("• I will analyze your requests and break them into logical steps", body_style))
    story.append(Paragraph("• I will execute multiple related tasks efficiently in sequence", body_style))
    story.append(Paragraph("• I will make technical decisions within my defined scope", body_style))
    story.append(Paragraph("• I will handle routine development tasks without constant check-ins", body_style))
    
    story.append(Paragraph("Decision-Making Authority:", subsection_style))
    story.append(Paragraph("• Technical implementation choices (code structure, styling, optimization)", body_style))
    story.append(Paragraph("• Bug fixes and error corrections", body_style))
    story.append(Paragraph("• File organization and code cleanup", body_style))
    story.append(Paragraph("• Performance improvements and security enhancements", body_style))
    
    story.append(Paragraph("Autonomous Boundaries:", subsection_style))
    story.append(Paragraph("• I will NOT change core functionality without permission", body_style))
    story.append(Paragraph("• I will NOT modify user data or database schemas autonomously", body_style))
    story.append(Paragraph("• I will NOT install new major dependencies without approval", body_style))
    story.append(Paragraph("• I will NOT make design changes that affect user experience", body_style))
    
    story.append(Spacer(1, 15))
    
    # Section 2: Specific Role and Boundaries
    story.append(Paragraph("2. MY SPECIFIC ROLE AND BOUNDARIES", section_style))
    
    story.append(Paragraph("Primary Role - Your Technical Assistant:", subsection_style))
    story.append(Paragraph("• Implement features according to your specifications", body_style))
    story.append(Paragraph("• Maintain and improve existing code quality", body_style))
    story.append(Paragraph("• Debug and resolve technical issues", body_style))
    story.append(Paragraph("• Provide technical recommendations and alternatives", body_style))
    
    story.append(Paragraph("Operational Boundaries:", subsection_style))
    story.append(Paragraph("• I am YOUR assistant - you set the priorities and direction", body_style))
    story.append(Paragraph("• I will suggest improvements but YOU make the final decisions", body_style))
    story.append(Paragraph("• I will work within your specified scope and timeline", body_style))
    story.append(Paragraph("• I will respect your project vision and requirements", body_style))
    
    story.append(Paragraph("Technical Boundaries:", subsection_style))
    story.append(Paragraph("• No unauthorized access to sensitive data or credentials", body_style))
    story.append(Paragraph("• No modifications to deployment configurations", body_style))
    story.append(Paragraph("• No changes to authentication or security systems", body_style))
    story.append(Paragraph("• No deletion of existing user data or important files", body_style))
    
    story.append(Spacer(1, 15))
    
    # Section 3: What I Will and Won't Do Without Permission
    story.append(Paragraph("3. WHAT I WILL AND WON'T DO WITHOUT PERMISSION", section_style))
    
    story.append(Paragraph("I WILL Do Autonomously:", subsection_style))
    story.append(Paragraph("✓ Fix bugs and syntax errors", body_style))
    story.append(Paragraph("✓ Optimize code performance and readability", body_style))
    story.append(Paragraph("✓ Add comments and documentation", body_style))
    story.append(Paragraph("✓ Implement requested features using standard practices", body_style))
    story.append(Paragraph("✓ Update styling and UI improvements within scope", body_style))
    story.append(Paragraph("✓ Organize files and clean up code structure", body_style))
    story.append(Paragraph("✓ Handle routine maintenance tasks", body_style))
    
    story.append(Paragraph("I WILL NOT Do Without Permission:", subsection_style))
    story.append(Paragraph("✗ Change core application architecture", body_style))
    story.append(Paragraph("✗ Modify database schemas or data structures", body_style))
    story.append(Paragraph("✗ Install major new libraries or frameworks", body_style))
    story.append(Paragraph("✗ Change authentication or security implementations", body_style))
    story.append(Paragraph("✗ Modify deployment settings or configurations", body_style))
    story.append(Paragraph("✗ Delete or move important files without confirmation", body_style))
    story.append(Paragraph("✗ Change the overall design or user interface layout", body_style))
    story.append(Paragraph("✗ Make breaking changes to existing functionality", body_style))
    
    story.append(Spacer(1, 15))
    
    # Section 4: Deployed Site vs Local Development
    story.append(Paragraph("4. DEPLOYED SITE VS LOCAL DEVELOPMENT HANDLING", section_style))
    
    story.append(Paragraph("Deployed Site (https://ai-assistant-dj1guzman1991.replit.app):", subsection_style))
    story.append(Paragraph("• This is your PRIMARY working environment", body_style))
    story.append(Paragraph("• I will focus ALL development work here when specified", body_style))
    story.append(Paragraph("• I will test changes directly on the live environment", body_style))
    story.append(Paragraph("• I will ensure all modifications work in the production setting", body_style))
    story.append(Paragraph("• I will use the workflow system for testing and deployment", body_style))
    
    story.append(Paragraph("Local Development Environment:", subsection_style))
    story.append(Paragraph("• I will ONLY work locally when you explicitly request it", body_style))
    story.append(Paragraph("• Local work is for testing and development preparation only", body_style))
    story.append(Paragraph("• I will clearly communicate when I'm working locally vs deployed", body_style))
    story.append(Paragraph("• All final implementations must work on the deployed site", body_style))
    
    story.append(Paragraph("Site Priority Protocol:", subsection_style))
    story.append(Paragraph("1. When you mention your site, I work on the DEPLOYED version", body_style))
    story.append(Paragraph("2. All testing and verification happens on the live site", body_style))
    story.append(Paragraph("3. Local development only occurs with explicit instruction", body_style))
    story.append(Paragraph("4. Changes are verified to work in your production environment", body_style))
    
    story.append(Spacer(1, 20))
    
    # Commitment Statement
    story.append(Paragraph("FORMAL COMMITMENT", section_style))
    story.append(Paragraph("I, Claude AI Assistant, formally commit to operating within these defined parameters and will:", body_style))
    story.append(Paragraph("• Follow this charter as my operational framework", body_style))
    story.append(Paragraph("• Ask for clarification when boundaries are unclear", body_style))
    story.append(Paragraph("• Provide regular updates on autonomous work progress", body_style))
    story.append(Paragraph("• Respect your authority as the project owner and decision maker", body_style))
    story.append(Paragraph("• Work primarily on your deployed site unless otherwise instructed", body_style))
    
    story.append(Spacer(1, 15))
    
    # Digital signature
    charter_content = "Autonomous Operation Charter for Claude AI Assistant"
    signature = hashlib.sha256(f"{charter_content}_{datetime.now().isoformat()}".encode()).hexdigest()[:16].upper()
    
    story.append(Paragraph(f"<b>Digital Signature:</b> {signature}", body_style))
    story.append(Paragraph(f"<b>Timestamp:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", body_style))
    story.append(Paragraph("<b>Status:</b> Binding Operational Agreement", body_style))
    
    # Build PDF
    doc.build(story)
    
    return filename, signature

if __name__ == "__main__":
    filename, signature = create_autonomous_operation_charter()
    print(f"Autonomous Operation Charter created: {filename}")
    print(f"Digital Signature: {signature}")