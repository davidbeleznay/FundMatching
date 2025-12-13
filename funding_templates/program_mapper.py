"""
Maps Airtable program names to template IDs
Add new mappings as you create more templates
"""

PROGRAM_TEMPLATE_MAP = {
    # SFI Programs
    "SFI Climate Smart Forestry - Indigenous-Led (ECCC Grant)": "sfi-climate-smart-forestry",
    "SFI Indigenous-Led Climate Smart Forestry - Round 2": "sfi-climate-smart-forestry",
    
    # Add more as you build templates:
    # "BC Salmon Restoration & Innovation Fund": "bcsrif",
    # "FWCP Watershed": "fwcp",
    # "Habitat Conservation Trust Foundation": "hctf",
    # "ECCC Nature Smart Climate Solutions": "eccc-nature-smart",
}

def get_template_id(program_name: str) -> str | None:
    """
    Get template ID for a given program name from Airtable
    
    Args:
        program_name: Program name as stored in Airtable
        
    Returns:
        Template ID (e.g., 'sfi-climate-smart-forestry') or None if no template exists
    """
    return PROGRAM_TEMPLATE_MAP.get(program_name)

def has_template(program_name: str) -> bool:
    """Check if a template exists for this program"""
    return program_name in PROGRAM_TEMPLATE_MAP
